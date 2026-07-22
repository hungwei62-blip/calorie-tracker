"""Calendar-based history manager for student-owned records."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

import streamlit as st

from domain.history import parse_record_date
from pages.common import TRAINING_TYPES, current_auth_context
from services import application, auth, metrics, sheets
from ui.history_calendar import history_record_calendar


KIND_LABELS = {
    "food": "食物",
    "water": "飲水",
    "training": "訓練",
    "weight": "體重",
}

_MANAGE_DIALOG_STATE = "history_manage_dialog_state"
_DELETE_DIALOG_STATE = "history_delete_dialog_state"


def _selected_day_timestamp(selected_day: date) -> str:
    now = datetime.now(auth.TAIPEI_TZ)
    return datetime.combine(selected_day, now.timetz()).isoformat()


def _set_history_flash(message: str) -> None:
    st.session_state.history_record_flash = message


def _finish_change(clear_cache: Callable[[], None], message: str) -> None:
    clear_cache()
    st.session_state.pop(_MANAGE_DIALOG_STATE, None)
    st.session_state.pop(_DELETE_DIALOG_STATE, None)
    _set_history_flash(message)
    st.rerun()


def _set_manage_view(
    view: str, kind: str = "", record_id: str = ""
) -> None:
    st.session_state[_MANAGE_DIALOG_STATE] = {
        "view": view,
        "kind": kind,
        "record_id": record_id,
    }


def _set_delete_target(kind: str = "", record_id: str = "") -> None:
    st.session_state[_DELETE_DIALOG_STATE] = {
        "kind": kind,
        "record_id": record_id,
    }


def _record_time(record: dict[str, Any]) -> str:
    text = str(record.get("timestamp") or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return parsed.strftime("%H:%M") if "T" in text else ""


def _record_description(kind: str, record: dict[str, Any]) -> str:
    if kind == "food":
        return (
            f"{record.get('food_summary') or '食物'} · "
            f"{float(record.get('calories') or 0):.0f} kcal · "
            f"{float(record.get('protein') or 0):.0f} g"
        )
    if kind == "water":
        return f"{float(record.get('water_ml') or 0):.0f} ml"
    if kind == "weight":
        return f"{float(record.get('weight_kg') or 0):.1f} kg"
    return sheets.format_training_record(record) or "訓練"


def _record_items_for_day(
    selected_day: date,
    records: list[dict[str, Any]],
    weights: list[dict[str, Any]],
    trainings: list[dict[str, Any]],
) -> list[tuple[str, str, dict[str, Any]]]:
    items: list[tuple[str, str, dict[str, Any]]] = []
    for record in records:
        if parse_record_date(record.get("timestamp")) != selected_day:
            continue
        kind = "water" if record.get("meal_type") == "飲水" else "food"
        items.append((str(record.get("timestamp") or ""), kind, record))
    for kind, rows in (("weight", weights), ("training", trainings)):
        for row in rows:
            if parse_record_date(row.get("timestamp")) == selected_day:
                items.append((str(row.get("timestamp") or ""), kind, row))
    items.sort(key=lambda item: item[0], reverse=True)
    return items


def _recorded_dates(
    records: list[dict[str, Any]],
    weights: list[dict[str, Any]],
    trainings: list[dict[str, Any]],
    *,
    today: date,
) -> set[date]:
    dates = {
        parse_record_date(row.get("timestamp"))
        for row in (*records, *weights, *trainings)
    }
    return {day for day in dates if date.min < day <= today}


def _find_record_item(
    items: list[tuple[str, str, dict[str, Any]]],
    kind: str,
    record_id: str,
) -> dict[str, Any] | None:
    for _timestamp, item_kind, record in items:
        if item_kind == kind and str(record.get("record_id") or "") == record_id:
            return record
    return None


def _render_dialog_record_list(
    items: list[tuple[str, str, dict[str, Any]]],
    *,
    action_label: str,
    action_prefix: str,
    on_select: Callable[[str, str], None],
) -> None:
    if not items:
        st.info("這一天尚無紀錄。")
        return
    with st.container(gap="small"):
        for index, (_timestamp, kind, record) in enumerate(items):
            record_id = str(record.get("record_id") or "")
            row_key = f"{kind}_{record_id or index}"
            with st.container(
                key=f"dialog_record_row_{action_prefix}_{row_key}",
                border=True,
                horizontal=True,
                vertical_alignment="center",
                gap="small",
            ):
                with st.container(width="stretch", gap=None):
                    time_text = _record_time(record)
                    st.markdown(
                        f"**{KIND_LABELS[kind]}**"
                        f"{f' · {time_text}' if time_text else ''}  \n"
                        f"{_record_description(kind, record)}"
                    )
                st.button(
                    action_label,
                    key=f"{action_prefix}_{row_key}",
                    width="content",
                    disabled=not record_id,
                    on_click=on_select,
                    args=(kind, record_id),
                )


def _render_edit_form(
    kind: str,
    record: dict[str, Any],
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    record_id = str(record.get("record_id") or "")
    if not record_id:
        st.error("此筆資料尚未建立 record_id，請先完成資料遷移。")
        return

    with st.form(f"history_edit_{kind}_{record_id}"):
        if kind == "food":
            summary = st.text_input(
                "食物內容", value=str(record.get("food_summary") or "")
            )
            calories = st.number_input(
                "熱量 (kcal)", min_value=0, step=10,
                value=int(round(float(record.get("calories") or 0))),
            )
            protein = st.number_input(
                "蛋白質 (g)", min_value=0, step=1,
                value=int(round(float(record.get("protein") or 0))),
            )
        elif kind == "water":
            water_ml = st.number_input(
                "飲水量 (ml)", min_value=1, step=100,
                value=max(1, int(round(float(record.get("water_ml") or 0)))),
            )
        elif kind == "weight":
            weight_kg = st.number_input(
                "體重 (kg)", min_value=30.0, max_value=300.0, step=0.1,
                value=float(record.get("weight_kg") or 60),
            )
        else:
            selected_types = st.multiselect(
                "訓練類型 (可複選)", TRAINING_TYPES,
                default=list(record.get("training_types") or []),
            )
            strength_detail = st.text_input(
                "重量訓練內容", value=str(record.get("strength_detail") or "")
            )
            cardio_detail = st.text_input(
                "有氧訓練內容", value=str(record.get("cardio_detail") or "")
            )
            other_detail = st.text_input(
                "其他訓練內容", value=str(record.get("other_detail") or "")
            )
        submitted = st.form_submit_button("儲存修改", width="stretch")

    if not submitted:
        return
    try:
        if kind == "food":
            if calories == 0 and protein == 0:
                raise ValueError("熱量與蛋白質至少一項必須大於 0")
            changed = application.update_own_record(
                current_auth_context(), user_id, record_id,
                {"food_summary": summary, "calories": calories, "protein": protein},
            )
        elif kind == "water":
            changed = application.update_own_record(
                current_auth_context(), user_id, record_id, {"water_ml": water_ml}
            )
        elif kind == "weight":
            changed = application.update_own_weight(
                current_auth_context(), user_id, record_id, weight_kg
            )
        else:
            changed = application.update_own_training(
                current_auth_context(), user_id, record_id,
                training_types=selected_types,
                strength_detail=strength_detail,
                cardio_detail=cardio_detail,
                other_detail=other_detail,
            )
        if not changed:
            raise LookupError("record not found")
    except ValueError as exc:
        st.warning(str(exc))
    except Exception:
        st.error("紀錄更新失敗，請稍後再試。")
    else:
        _finish_change(clear_cache, "紀錄已更新")


def _render_add_form(
    kind: str,
    selected_day: date,
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    with st.form(f"history_add_{kind}_{selected_day.isoformat()}"):
        if kind == "food":
            calories = st.number_input("熱量 (kcal)", min_value=0, value=None, step=10)
            protein = st.number_input("蛋白質 (g)", min_value=0, value=None, step=1)
        elif kind == "water":
            water_ml = st.number_input("飲水量 (ml)", min_value=1, value=None, step=100)
        elif kind == "weight":
            weight_kg = st.number_input(
                "體重 (kg)", min_value=30.0, max_value=300.0,
                value=None, step=0.1,
            )
        else:
            selected_types = st.multiselect("訓練類型 (可複選)", TRAINING_TYPES)
            strength_detail = st.text_input("重量訓練內容")
            cardio_detail = st.text_input("有氧訓練內容")
            other_detail = st.text_input("其他訓練內容")
        submitted = st.form_submit_button("新增紀錄", width="stretch")

    if not submitted:
        return
    try:
        context = current_auth_context()
        if kind == "food":
            calorie_value, protein_value = calories or 0, protein or 0
            if calorie_value == 0 and protein_value == 0:
                raise ValueError("熱量與蛋白質至少一項必須大於 0")
            application.append_student_record(
                context, user_id=user_id,
                timestamp=_selected_day_timestamp(selected_day),
                meal_type="食物", food_summary="手動紀錄",
                calories=calorie_value, protein=protein_value, carb=0, fat=0,
                water_ml=0, image_url="", portion=1,
            )
        elif kind == "water":
            if not water_ml:
                raise ValueError("請輸入飲水量")
            application.append_student_record(
                context, user_id=user_id,
                timestamp=_selected_day_timestamp(selected_day),
                meal_type="飲水", food_summary="飲水", calories=0, protein=0,
                carb=0, fat=0, water_ml=water_ml, image_url="", portion=1,
            )
        elif kind == "weight":
            if weight_kg is None:
                raise ValueError("請輸入體重")
            application.append_student_weight(
                context, user_id, _selected_day_timestamp(selected_day), weight_kg
            )
        else:
            if sheets.get_training_by_date(user_id, selected_day):
                raise ValueError("這一天已有訓練紀錄，請修改原紀錄")
            application.update_student_training(
                context, user_id=user_id, timestamp=selected_day.isoformat(),
                training_types=selected_types,
                strength_detail=strength_detail,
                cardio_detail=cardio_detail,
                other_detail=other_detail,
            )
    except ValueError as exc:
        st.warning(str(exc))
    except Exception:
        st.error("紀錄新增失敗，請稍後再試。")
    else:
        _finish_change(clear_cache, "紀錄完成")


def _render_manage_day_dialog(
    selected_day: date,
    items: list[tuple[str, str, dict[str, Any]]],
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    state = st.session_state.get(
        _MANAGE_DIALOG_STATE,
        {"view": "list", "kind": "", "record_id": ""},
    )
    view = str(state.get("view") or "list")
    kind = str(state.get("kind") or "")
    record_id = str(state.get("record_id") or "")

    st.caption(selected_day.strftime("%Y/%m/%d"))
    with st.container(key="history_dialog_totals"):
        st.markdown(
            build_daily_totals_html(_daily_totals_for_items(items)),
            unsafe_allow_html=True,
        )
    if view != "list":
        st.button(
            "返回",
            icon=":material/arrow_back:",
            key="history_manage_back",
            on_click=_set_manage_view,
            args=("list",),
        )

    if view == "add" and kind in KIND_LABELS:
        st.markdown(f"**新增{KIND_LABELS[kind]}紀錄**")
        _render_add_form(kind, selected_day, user_id, clear_cache)
        return
    if view == "edit" and kind in KIND_LABELS:
        record = _find_record_item(items, kind, record_id)
        if record is None:
            st.error("找不到要修改的紀錄，請重新整理後再試。")
            return
        st.markdown(f"**修改{KIND_LABELS[kind]}紀錄**")
        _render_edit_form(kind, record, user_id, clear_cache)
        return

    if not items:
        st.caption("新增紀錄")
        with st.container(
            key="history_dialog_add_actions", horizontal=True, gap="small"
        ):
            for item_kind in ("food", "water", "training", "weight"):
                st.button(
                    KIND_LABELS[item_kind],
                    key=f"history_dialog_add_{item_kind}",
                    width="stretch",
                    on_click=_set_manage_view,
                    args=("add", item_kind, ""),
                )
        return

    st.markdown("**修改當日攝取總量**")
    _render_daily_totals_edit_form(
        selected_day, items, user_id, clear_cache
    )

    other_items = [item for item in items if item[1] in {"training", "weight"}]
    if other_items:
        st.caption("訓練與體重紀錄")
        _render_dialog_record_list(
            other_items,
            action_label="修改",
            action_prefix="history_dialog_edit",
            on_select=lambda item_kind, item_id: _set_manage_view(
                "edit", item_kind, item_id
            ),
        )


@st.dialog("修改紀錄")
def _manage_day_dialog(
    selected_day: date,
    items: list[tuple[str, str, dict[str, Any]]],
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    with st.container(key="history_manage_dialog"):
        _render_manage_day_dialog(selected_day, items, user_id, clear_cache)


def _delete_record(
    kind: str,
    record_id: str,
    user_id: str,
) -> bool:
    context = current_auth_context()
    if kind in {"food", "water"}:
        return application.delete_own_record(context, user_id, record_id)
    if kind == "weight":
        return application.delete_own_weight(context, user_id, record_id)
    return application.delete_own_training(context, user_id, record_id)


def _render_delete_day_dialog(
    selected_day: date,
    items: list[tuple[str, str, dict[str, Any]]],
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    state = st.session_state.get(
        _DELETE_DIALOG_STATE, {"kind": "", "record_id": ""}
    )
    kind = str(state.get("kind") or "")
    record_id = str(state.get("record_id") or "")
    st.caption(selected_day.strftime("%Y/%m/%d"))

    if not kind or not record_id:
        st.write("請選擇要刪除的紀錄：")
        _render_dialog_record_list(
            items,
            action_label="選擇",
            action_prefix="history_dialog_delete_select",
            on_select=_set_delete_target,
        )
        return

    record = _find_record_item(items, kind, record_id)
    if record is None:
        st.error("找不到要刪除的紀錄，請重新整理後再試。")
        return
    st.warning("刪除後無法復原，確定要刪除這筆紀錄嗎？")
    st.markdown(f"**{KIND_LABELS[kind]}**  \n{_record_description(kind, record)}")
    with st.container(horizontal=True, gap="small"):
        st.button(
            "返回",
            key="history_delete_back",
            width="stretch",
            on_click=_set_delete_target,
        )
        confirmed = st.button(
            "確認刪除",
            key="history_delete_confirm",
            type="primary",
            width="stretch",
        )
    if not confirmed:
        return
    try:
        if not _delete_record(kind, record_id, user_id):
            raise LookupError("record not found")
    except Exception:
        st.error("紀錄刪除失敗，請稍後再試。")
    else:
        _finish_change(clear_cache, "紀錄已刪除")


@st.dialog("刪除紀錄")
def _delete_day_dialog(
    selected_day: date,
    items: list[tuple[str, str, dict[str, Any]]],
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    with st.container(key="history_delete_dialog"):
        _render_delete_day_dialog(selected_day, items, user_id, clear_cache)


def _format_total(value: object) -> str:
    try:
        number = max(0, int(round(float(value or 0))))
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}"


def _daily_totals_for_items(
    items: list[tuple[str, str, dict[str, Any]]],
) -> dict[str, float]:
    nutrition_records = [
        record for _, kind, record in items if kind in {"food", "water"}
    ]
    return metrics.sum_totals(nutrition_records).as_dict()


def _replace_daily_nutrition_totals(
    selected_day: date,
    items: list[tuple[str, str, dict[str, Any]]],
    user_id: str,
    *,
    calories: int,
    protein: int,
    water_ml: int,
) -> None:
    """Replace a day's totals with the fewest changes to its existing rows."""
    context = current_auth_context()
    food_rows = [record for _, kind, record in items if kind == "food"]
    water_rows = [record for _, kind, record in items if kind == "water"]

    def redistributed_values(
        rows: list[dict[str, Any]], field: str, target: int
    ) -> list[float]:
        values = [max(0.0, float(row.get(field) or 0)) for row in rows]
        difference = float(target) - sum(values)
        if not values:
            return values
        if difference >= 0:
            values[0] += difference
            return values
        remaining = -difference
        for index, value in enumerate(values):
            reduction = min(value, remaining)
            values[index] -= reduction
            remaining -= reduction
            if remaining <= 0.000001:
                break
        return values

    calorie_values = redistributed_values(food_rows, "calories", calories)
    protein_values = redistributed_values(food_rows, "protein", protein)
    for index, record in enumerate(food_rows):
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            raise RuntimeError("此筆飲食資料尚未完成 record_id 遷移")
        updates: dict[str, float] = {}
        if abs(calorie_values[index] - float(record.get("calories") or 0)) > 0.001:
            updates["calories"] = calorie_values[index]
        if abs(protein_values[index] - float(record.get("protein") or 0)) > 0.001:
            updates["protein"] = protein_values[index]
        if not updates:
            continue
        if not application.update_own_record(
            context, user_id, record_id, updates
        ):
            raise LookupError("food record not found")

    if not food_rows and (calories > 0 or protein > 0):
        application.append_student_record(
            context,
            user_id=user_id,
            timestamp=_selected_day_timestamp(selected_day),
            meal_type="食物",
            food_summary="手動紀錄",
            calories=calories,
            protein=protein,
            carb=0,
            fat=0,
            water_ml=0,
            image_url="",
            portion=1,
        )

    water_values = redistributed_values(water_rows, "water_ml", water_ml)
    for index, record in enumerate(water_rows):
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            raise RuntimeError("此筆飲水資料尚未完成 record_id 遷移")
        if abs(water_values[index] - float(record.get("water_ml") or 0)) <= 0.001:
            continue
        if not application.update_own_record(
            context,
            user_id,
            record_id,
            {"water_ml": water_values[index]},
        ):
            raise LookupError("water record not found")

    if not water_rows and water_ml > 0:
        application.append_student_record(
            context,
            user_id=user_id,
            timestamp=_selected_day_timestamp(selected_day),
            meal_type="飲水",
            food_summary="飲水",
            calories=0,
            protein=0,
            carb=0,
            fat=0,
            water_ml=water_ml,
            image_url="",
            portion=1,
        )


def _render_daily_totals_edit_form(
    selected_day: date,
    items: list[tuple[str, str, dict[str, Any]]],
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    totals = _daily_totals_for_items(items)
    with st.form(f"history_daily_totals_{selected_day.isoformat()}"):
        calories = st.number_input(
            "當日熱量總量 (kcal)",
            min_value=0,
            step=10,
            value=int(round(float(totals.get("calories") or 0))),
        )
        protein = st.number_input(
            "當日蛋白質總量 (g)",
            min_value=0,
            step=1,
            value=int(round(float(totals.get("protein") or 0))),
        )
        water_ml = st.number_input(
            "當日飲水總量 (ml)",
            min_value=0,
            step=100,
            value=int(round(float(totals.get("water") or 0))),
        )
        submitted = st.form_submit_button("儲存修改", width="stretch")

    if not submitted:
        return
    try:
        _replace_daily_nutrition_totals(
            selected_day,
            items,
            user_id,
            calories=calories,
            protein=protein,
            water_ml=water_ml,
        )
    except (ValueError, RuntimeError) as exc:
        st.warning(str(exc))
    except Exception:
        st.error("紀錄更新失敗，請稍後再試。")
    else:
        _finish_change(clear_cache, "紀錄已更新")


def build_daily_totals_html(totals: dict[str, Any]) -> str:
    """Render the shared, three-line calorie, protein, and water summary."""
    return (
        '<div class="history-daily-summary-values">'
        f'<div>熱量 <strong>{_format_total(totals.get("calories"))}</strong> kcal</div>'
        f'<div>蛋白質 <strong>{_format_total(totals.get("protein"))}</strong> g</div>'
        f'<div>飲水 <strong>{_format_total(totals.get("water"))}</strong> ml</div>'
        "</div>"
    )


def render_daily_record_manager(
    user_id: str, clear_cache: Callable[[], None]
) -> None:
    """Render the record calendar and selected-day summary actions."""
    with st.container(key="student_daily_record_manager", border=False):
        flash = st.session_state.pop("history_record_flash", None)
        if flash:
            st.success(str(flash))

        today = auth.today_date()
        records = sheets.get_records(user_id)
        weights = sheets.get_weight_records(user_id)
        trainings = sheets.get_training_records(user_id)
        selection = history_record_calendar(
            today=today,
            record_dates=_recorded_dates(
                records, weights, trainings, today=today
            ),
            key="history_record_calendar",
        )
        selected_day = selection.selected_date
        if selected_day is None:
            return

        items = _record_items_for_day(selected_day, records, weights, trainings)
        totals = _daily_totals_for_items(items)
        schema_ready = all(sheets.get_record_id_schema_status().values())
        if not schema_ready:
            st.warning("歷史紀錄目前為唯讀；請先完成 record_id 資料遷移。")

        with st.container(
            key="history_daily_summary",
            border=True,
            horizontal=True,
            vertical_alignment="center",
            gap="small",
        ):
            with st.container(key="history_daily_summary_values", width="stretch"):
                st.markdown(
                    build_daily_totals_html(totals),
                    unsafe_allow_html=True,
                )
            with st.container(
                key="history_daily_summary_actions",
                width="content",
                horizontal=True,
                gap="small",
            ):
                if st.button(
                    "修改",
                    key="history_day_manage",
                    width="content",
                    disabled=not schema_ready,
                ):
                    _set_manage_view("list")
                    _manage_day_dialog(selected_day, items, user_id, clear_cache)
                if st.button(
                    "刪除",
                    key="history_day_delete",
                    width="content",
                    disabled=not schema_ready or not items,
                ):
                    _set_delete_target()
                    _delete_day_dialog(selected_day, items, user_id, clear_cache)
