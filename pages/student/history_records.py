"""Daily history manager for student-owned food, water, training, and weight rows."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

import streamlit as st

from pages.common import TRAINING_TYPES, current_auth_context
from services import application, auth, metrics, sheets


KIND_LABELS = {
    "food": "食物",
    "water": "飲水",
    "training": "訓練",
    "weight": "體重",
}


def _selected_day_timestamp(selected_day: date) -> str:
    now = datetime.now(auth.TAIPEI_TZ)
    return datetime.combine(selected_day, now.timetz()).isoformat()


def _set_history_flash(message: str) -> None:
    st.session_state.history_record_flash = message


def _finish_change(clear_cache: Callable[[], None], message: str) -> None:
    clear_cache()
    _set_history_flash(message)
    st.rerun()


@st.dialog("修改紀錄")
def _edit_record_dialog(
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
            summary = st.text_input("食物內容", value=str(record.get("food_summary") or ""))
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
            raise LookupError("找不到要修改的紀錄，請重新整理後再試")
    except ValueError as exc:
        st.warning(str(exc))
    except Exception:
        st.error("紀錄更新失敗，請稍後再試。")
    else:
        _finish_change(clear_cache, "紀錄已更新")


@st.dialog("刪除紀錄")
def _delete_record_dialog(
    kind: str,
    record: dict[str, Any],
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    st.warning("刪除後無法復原，確定要刪除這筆紀錄嗎？")
    record_id = str(record.get("record_id") or "")
    if st.button("確認刪除", type="primary", width="stretch"):
        try:
            context = current_auth_context()
            if kind in {"food", "water"}:
                deleted = application.delete_own_record(context, user_id, record_id)
            elif kind == "weight":
                deleted = application.delete_own_weight(context, user_id, record_id)
            else:
                deleted = application.delete_own_training(context, user_id, record_id)
            if not deleted:
                raise LookupError("record not found")
        except Exception:
            st.error("紀錄刪除失敗，請稍後再試。")
        else:
            _finish_change(clear_cache, "紀錄已刪除")


@st.dialog("新增歷史紀錄")
def _add_record_dialog(
    kind: str,
    selected_day: date,
    user_id: str,
    clear_cache: Callable[[], None],
) -> None:
    st.caption(selected_day.strftime("%Y/%m/%d"))
    with st.form(f"history_add_{kind}_{selected_day.isoformat()}"):
        if kind == "food":
            summary = st.text_input("食物內容")
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
                context, user_id=user_id, timestamp=_selected_day_timestamp(selected_day),
                meal_type="食物", food_summary=summary.strip() or "手動紀錄",
                calories=calorie_value, protein=protein_value, carb=0, fat=0,
                water_ml=0, image_url="", portion=1,
            )
        elif kind == "water":
            if not water_ml:
                raise ValueError("請輸入飲水量")
            application.append_student_record(
                context, user_id=user_id, timestamp=_selected_day_timestamp(selected_day),
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


def render_daily_record_manager(
    user_id: str, clear_cache: Callable[[], None]
) -> None:
    """Render a date-centered, record-ID-safe history management section."""
    with st.container(key="student_daily_record_manager", border=True):
        st.subheader("每日紀錄")
        flash = st.session_state.pop("history_record_flash", None)
        if flash:
            st.success(str(flash))

        today = auth.today_date()
        selected_day = st.date_input(
            "選擇日期", value=today, max_value=today,
            key="history_record_date",
        )
        records = sheets.get_records_by_date(user_id, selected_day)
        weights = [
            row for row in sheets.get_weight_records(user_id)
            if str(row.get("timestamp") or "")[:10] == selected_day.isoformat()
        ]
        trainings = [
            row for row in sheets.get_training_records(user_id)
            if str(row.get("timestamp") or "")[:10] == selected_day.isoformat()
        ]
        totals = metrics.sum_totals(records).as_dict()
        summary_columns = st.columns(3)
        summary_columns[0].metric("熱量", f"{totals.get('calories', 0):.0f} kcal")
        summary_columns[1].metric("蛋白質", f"{totals.get('protein', 0):.0f} g")
        summary_columns[2].metric("飲水", f"{totals.get('water', 0):.0f} ml")

        schema_ready = all(sheets.get_record_id_schema_status().values())
        if not schema_ready:
            st.warning("歷史紀錄目前為唯讀；請先完成 record_id 資料遷移。")

        st.caption("新增紀錄")
        with st.container(
            key="history_add_actions",
            horizontal=True,
            gap="small",
        ):
            for kind in ("food", "water", "training", "weight"):
                training_exists = kind == "training" and bool(trainings)
                if st.button(
                    KIND_LABELS[kind],
                    key=f"history_add_{kind}",
                    width="stretch",
                    disabled=not schema_ready or training_exists,
                ):
                    _add_record_dialog(kind, selected_day, user_id, clear_cache)

        items: list[tuple[str, str, dict[str, Any]]] = []
        for record in records:
            kind = "water" if record.get("meal_type") == "飲水" else "food"
            items.append((str(record.get("timestamp") or ""), kind, record))
        items.extend((str(row.get("timestamp") or ""), "weight", row) for row in weights)
        items.extend((str(row.get("timestamp") or ""), "training", row) for row in trainings)
        items.sort(key=lambda item: item[0], reverse=True)

        st.caption("當日明細")
        if not items:
            st.info("這一天尚無紀錄。")
            return
        with st.container(
            key="history_record_list",
            height=300,
            border=False,
            gap="small",
        ):
            for index, (_timestamp, kind, record) in enumerate(items):
                record_id = str(record.get("record_id") or "")
                row_key = f"{kind}_{record_id or index}"
                with st.container(
                    key=f"history_record_row_{row_key}",
                    border=True,
                    horizontal=True,
                    vertical_alignment="center",
                    gap="small",
                ):
                    with st.container(
                        key=f"history_record_content_{row_key}",
                        width="stretch",
                        gap=None,
                    ):
                        time_text = _record_time(record)
                        st.markdown(
                            f"**{KIND_LABELS[kind]}**"
                            f"{f' · {time_text}' if time_text else ''}  \n"
                            f"{_record_description(kind, record)}"
                        )
                    disabled = not schema_ready or not record_id
                    with st.container(
                        key=f"history_record_actions_{row_key}",
                        width="content",
                        horizontal=True,
                        gap="small",
                    ):
                        if st.button(
                            "修改",
                            key=f"history_edit_{row_key}",
                            width="content",
                            disabled=disabled,
                        ):
                            _edit_record_dialog(kind, record, user_id, clear_cache)
                        if st.button(
                            "刪除",
                            key=f"history_delete_{row_key}",
                            width="content",
                            disabled=disabled,
                        ):
                            _delete_record_dialog(kind, record, user_id, clear_cache)
