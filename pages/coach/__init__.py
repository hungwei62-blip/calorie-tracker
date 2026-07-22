"""教練端頁面。"""
from __future__ import annotations
from datetime import date, timedelta
from io import BytesIO
import html
import io as _io
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as _plt
from matplotlib.backends.backend_pdf import PdfPages as _PdfPages
import streamlit as st
from services import application, metrics, sheets
from services.health import run_health_checks
from services.security import (
    safe_data_read_failure_message,
    safe_failure_message,
)
from domain.history import aggregate_daily as _history_aggregate_daily
from domain.history import parse_record_date as _parse_record_date
from services.exports import build_history_csv
from pages.student import (
    StudentHistoryData,
    load_student_history_data,
    render_student_history_charts,
)
from pages.common import (
    _clear_analysis_cache,
    current_auth_context,
    get_default_avatar_source,
)
from ui.coach_student_card import coach_student_card


COACH_NUTRIENT_SPECS = (
    ("卡路里", "calories", "calorie", "kcal", "#ff6068"),
    ("水", "water", "water", "ml", "#90cbfb"),
    ("蛋白質", "protein", "protein", "g", "#bbf250"),
)

_EXPANDED_GOAL_STUDENT_KEY = "coach_goal_expanded_student"
_GOAL_FLASH_KEY = "coach_goal_update_flash"
_HISTORY_EXPORT_CACHE_KEY = "coach_history_prepared_export"


def _non_negative_number(value: object) -> float:
    """Return a finite non-negative number for progress rendering."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) and number > 0 else 0.0


def calculate_coach_nutrient_progress(
    actual: object, goal: object
) -> tuple[float, float, float]:
    """Normalize a nutrient pair and clamp its visual progress to 0-100%."""
    actual_value = _non_negative_number(actual)
    goal_value = _non_negative_number(goal)
    percentage = min(actual_value / goal_value * 100, 100) if goal_value else 0.0
    return actual_value, goal_value, percentage


def _format_nutrient_value(value: float) -> str:
    return str(int(round(value)))


def build_coach_nutrient_progress_html(
    label: str,
    actual: object,
    goal: object,
    unit: str,
    color: str,
) -> str:
    """Build one compact, accessible horizontal nutrient progress indicator."""
    actual_value, goal_value, percentage = calculate_coach_nutrient_progress(
        actual, goal
    )
    actual_text = _format_nutrient_value(actual_value)
    goal_text = _format_nutrient_value(goal_value) if goal_value else "—"
    safe_label = html.escape(label)
    safe_unit = html.escape(unit)
    safe_color = html.escape(color, quote=True)
    value_text = f"{actual_text} / {goal_text} {safe_unit}"

    return (
        '<div class="coach-nutrient">'
        f'<span class="coach-nutrient-label">{safe_label}</span>'
        '<div class="coach-nutrient-track" role="progressbar" '
        f'aria-label="{safe_label}" aria-valuemin="0" aria-valuemax="100" '
        f'aria-valuenow="{percentage:.0f}">'
        f'<span style="width:{percentage:.2f}%;background:{safe_color}"></span>'
        "</div>"
        f'<span class="coach-nutrient-value">{value_text}</span>'
        "</div>"
    )


def build_coach_student_card_html(
    name: object,
    has_training: bool,
    totals: dict[str, object],
    goals: dict[str, object],
) -> str:
    """Build a student status card with three single-row nutrient indicators."""
    display_name = str(name or "Unknown")
    safe_name = html.escape(display_name)
    safe_initial = html.escape(display_name[0] if display_name else "?")
    training_class = "" if has_training else " not-done"
    training_html = (
        '<i class="fas fa-check"></i> Trained'
        if has_training
        else '<i class="fas fa-times"></i> Not trained'
    )
    nutrients_html = "".join(
        build_coach_nutrient_progress_html(
            label,
            totals.get(actual_key, 0),
            goals.get(goal_key, 0),
            unit,
            color,
        )
        for label, actual_key, goal_key, unit, color in COACH_NUTRIENT_SPECS
    )

    return (
        '<div class="member-card">'
        '<div class="member-top-row">'
        f'<div class="member-avatar">{safe_initial}</div>'
        f'<div class="member-name">{safe_name}</div>'
        f'<div class="training-badge{training_class}">{training_html}</div>'
        "</div>"
        f'<div class="coach-nutrient-grid">{nutrients_html}</div>'
        "</div>"
    )


def build_coach_welcome_html(display_name: object, avatar_source: str) -> str:
    """Build the coach greeting with the same avatar treatment as students."""
    safe_name = html.escape(str(display_name or "Coach"))
    safe_avatar = html.escape(avatar_source, quote=True)
    return (
        '<div class="coach-home-welcome" style="display:flex;align-items:center;'
        'gap:16px;margin-top:0;margin-bottom:25px;width:100%;">'
        f'<img src="{safe_avatar}" alt="avatar" style="width:56px;height:56px;'
        'border-radius:50%;object-fit:cover;box-shadow:0 4px 12px rgba(0,0,0,0.05);">'
        f'<span style="font-size:24px;font-weight:400;color:#1F2937;'
        'font-family:system-ui,-apple-system,sans-serif;white-space:nowrap;">'
        f'Hello ! {safe_name}</span></div>'
    )


def _render_password_reset_requests() -> None:
    notice = st.session_state.pop("temporary_password_notice", None)
    if isinstance(notice, dict):
        st.success(
            f"{notice.get('student_name', '學員')} 的臨時密碼已產生，"
            "請立即記錄並透過既有聯絡方式告知。此密碼不會再次顯示。"
        )
        st.code(str(notice.get("temporary_password") or ""), language=None)

    try:
        requests = application.get_password_reset_requests(
            current_auth_context()
        )
    except Exception as exc:
        st.warning(safe_failure_message("password_reset.list", exc))
        return

    with st.expander(f"密碼重設申請（{len(requests)}）", expanded=bool(requests)):
        if not requests:
            st.caption("目前沒有待處理申請。")
            return
        for request in requests:
            student = request.get("student") or {}
            student_name = str(
                student.get("name") or student.get("username") or "學員"
            )
            st.write(
                f"{student_name}｜申請時間：{request.get('requested_at', '')}"
            )
            approve_column, reject_column = st.columns(2)
            request_id = str(request.get("request_id") or "")
            if approve_column.button(
                "核准並產生臨時密碼",
                key=f"approve_password_reset_{request_id}",
                width="stretch",
            ):
                try:
                    temporary_password = application.approve_password_reset(
                        current_auth_context(), request_id
                    )
                except Exception as exc:
                    st.error(safe_failure_message("password_reset.approve", exc))
                else:
                    st.session_state.temporary_password_notice = {
                        "student_name": student_name,
                        "temporary_password": temporary_password,
                    }
                    st.rerun()
            if reject_column.button(
                "駁回",
                key=f"reject_password_reset_{request_id}",
                width="stretch",
            ):
                try:
                    application.reject_password_reset(
                        current_auth_context(), request_id
                    )
                except Exception as exc:
                    st.error(safe_failure_message("password_reset.reject", exc))
                else:
                    st.rerun()
            st.divider()


def _render_student_goal_editor(
    user_id: str, goals: dict[str, object]
) -> None:
    """Render the three supported goal fields directly below a status card."""
    flash = st.session_state.get(_GOAL_FLASH_KEY)
    if isinstance(flash, dict) and flash.get("user_id") == user_id:
        st.success(str(flash.get("message") or "目標已更新"))
        st.session_state.pop(_GOAL_FLASH_KEY, None)

    with st.container(key=f"coach_goal_editor_{user_id}", border=True):
        with st.form(f"coach_goal_form_{user_id}"):
            calorie_column, protein_column, water_column = st.columns(3)
            with calorie_column:
                calorie = st.number_input(
                    "卡路里目標 (kcal)",
                    min_value=1.0,
                    value=max(1.0, float(goals.get("calorie") or 0)),
                    step=50.0,
                )
            with protein_column:
                protein = st.number_input(
                    "蛋白質目標 (g)",
                    min_value=1.0,
                    value=max(1.0, float(goals.get("protein") or 0)),
                    step=5.0,
                )
            with water_column:
                water = st.number_input(
                    "飲水目標 (ml)",
                    min_value=1.0,
                    value=max(1.0, float(goals.get("water") or 0)),
                    step=100.0,
                )
            submitted = st.form_submit_button("更新學員目標", width="stretch")

    if not submitted:
        return
    try:
        if min(calorie, protein, water) <= 0:
            raise ValueError("三項目標都必須大於 0")
        updated = application.update_student_goals(
            current_auth_context(),
            user_id,
            {"calorie": calorie, "protein": protein, "water": water},
        )
        if not updated:
            raise LookupError("student not found")
        _clear_analysis_cache()
    except ValueError as exc:
        st.warning(str(exc))
    except Exception as exc:
        st.error(safe_failure_message("coach_goals.update", exc))
    else:
        st.session_state[_GOAL_FLASH_KEY] = {
            "user_id": user_id,
            "message": "目標已更新",
        }
        st.rerun()


def page_coach_overview() -> None:
    coach_name = str(st.session_state.username or "Coach")
    avatar_source = get_default_avatar_source()
    with st.container(key="coach_overview_header"):
        st.markdown(
            build_coach_welcome_html(coach_name, avatar_source),
            unsafe_allow_html=True,
        )
        st.header("本日學員狀態")

    _render_password_reset_requests()

    if st.session_state.get("role") == "admin":
        with st.container(key="admin_health_status"):
            with st.expander("系統健康狀態"):
                for check in run_health_checks():
                    prefix = {"ok": "正常", "warning": "注意", "error": "異常"}[check.status]
                    st.markdown(
                        '<div class="admin-health-row">'
                        f"{html.escape(str(check.name))}｜{prefix}｜{html.escape(str(check.detail))}"
                        "</div>",
                        unsafe_allow_html=True,
                    )

    try:
        students = application.get_students(current_auth_context())
        all_records = sheets.get_records()
        all_trainings = sheets.get_training_records()
    except Exception as exc:
        st.error(safe_failure_message("coach_overview.read", exc))
        return

    if not students:
        st.info("No students yet.")
        return

    today = date.today()
    today_prefix = today.isoformat()
    records_by_student = {}
    training_by_student = {}
    for record in all_records:
        if str(record.get("timestamp", ""))[:10] == today_prefix:
            records_by_student.setdefault(record.get("user_id", ""), []).append(record)
    for training in all_trainings:
        if str(training.get("timestamp", ""))[:10] == today_prefix:
            training_by_student[training.get("user_id", "")] = training
    for student in students:
        uid = student.get("user_id", "")
        name = student.get("name") or student.get("username") or "Unknown"
        goals = sheets.get_user_goals(uid)
        today_records = records_by_student.get(uid, [])
        totals = metrics.sum_totals(today_records).as_dict()
        training_today = training_by_student.get(uid)
        has_training = bool(training_today) and bool(training_today.get("training_types"))

        expanded = st.session_state.get(_EXPANDED_GOAL_STUDENT_KEY) == uid
        if coach_student_card(
            student_id=uid,
            name=str(name),
            has_training=has_training,
            totals=totals,
            goals=goals,
            expanded=expanded,
            key=f"coach_student_card_{uid}",
        ):
            st.session_state[_EXPANDED_GOAL_STUDENT_KEY] = None if expanded else uid
            st.rerun()
        if expanded:
            _render_student_goal_editor(uid, goals)
def page_coach_student_detail() -> None:

    uid = st.session_state.get("view_student_id")

    if not uid:

        st.error("未指定學員")

        return

    student = application.get_student(current_auth_context(), uid)

    if not student:

        st.error("沒有權限查看此學員")
        st.session_state.page = "學員狀態"
        st.session_state.pop("view_student_id", None)
        return

    st.header(f"📋 學員：{student.get('username', '未知')}")

    if st.button("← 返回總覽"):

        st.session_state.page = "學員狀態"

        st.session_state.pop("view_student_id", None)

        st.rerun()

    st.divider()


    # ============================================================
    # Excel 匯入功能
    # ============================================================
    st.subheader("匯入 Excel")

    uploaded_file = st.file_uploader(
        "選擇 Excel 檔案（每個工作表代表一個月份）",
        type=["xlsx"],
        key="excel_import_file"
    )

    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.getvalue()

            # 第一次分析（不回寫）
            with st.spinner("分析 Excel 檔案中..."):
                analysis_result = application.import_student_records(
                    current_auth_context(), uid,
                    excel_file_bytes=file_bytes, overwrite_duplicates=False,
                )

            # 顯示分析結果
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("可新增", f"{analysis_result['imported']} 筆")
            with col2:
                st.metric("將覆寫", f"{analysis_result['overwritten']} 筆")
            with col3:
                st.metric("將跳過", f"{analysis_result['skipped']} 筆")

            # 如果有錯誤，顯示警告
            if analysis_result["errors"]:
                with st.expander("⚠️ 匯入時的錯誤（點擊查看）"):
                    for err in analysis_result["errors"]:
                        st.warning(err)

            # 如果有重複，顯示並讓使用者選擇
            if analysis_result["duplicates"]:
                with st.expander(f"⚠️ 發現 {len(analysis_result['duplicates'])} 筆重複資料（點擊查看）"):
                    for dup in analysis_result["duplicates"][:20]:
                        st.write(f"📅 {dup['date']}｜現有熱量：{dup['existing'].get('calories', 0)} kcal")

            # 選擇匯入模式
            if analysis_result["imported"] > 0 or analysis_result["skipped"] > 0:
                overwrite_mode = st.radio(
                    "遇到重複日期怎麼辦？",
                    ["跳過（保留現有資料）", "覆寫（用新資料取代）"],
                    index=0,
                    horizontal=True,
                )
                do_overwrite = (overwrite_mode == "覆寫（用新資料取代）")

                if st.button("確認匯入", type="primary", width="stretch"):
                    with st.spinner("匯入資料中..."):
                        # 第二次呼叫，實際寫入
                        final_result = application.import_student_records(
                            current_auth_context(), uid,
                            precomputed_data=analysis_result['parsed_data'],
                            operation_token=analysis_result['parsed_data']['operation_token'],
                            overwrite_duplicates=do_overwrite
                        )
                        _clear_analysis_cache()

                        msg = f"匯入完成！新增 {final_result['imported']} 筆"
                        if final_result["overwritten"] > 0:
                            msg += f"，覆寫 {final_result['overwritten']} 筆"
                        if final_result["skipped"] > 0:
                            msg += f"，跳過 {final_result['skipped']} 筆"
                        st.success(msg)

                        st.session_state.excel_import_file = None
                        st.info("請手動刷新頁面以查看最新資料")
            else:
                st.info("沒有找到可匯入的資料")

        except Exception as exc:
            st.error(safe_failure_message("coach_import.preview", exc))

    st.divider()


    goals = sheets.get_user_goals(uid)

    today = date.today()

    today_records = sheets.get_records_by_date(uid, today)

    totals = metrics.sum_totals(today_records).as_dict()

    st.subheader("今日摘要")

    col1, col2 = st.columns(2)

    with col1:

        cal = totals.get("calories", 0)

        st.metric("熱量", f"{cal:.0f}", f"{goals.get('calorie', 0) - cal:.0f}")

    with col2:

        weight = sheets.get_latest_weight(uid)

        st.metric("體重", f"{weight:.1f}kg" if weight else "-", delta=None)

    st.divider()

    st.subheader("營養目標")

    col1, col2 = st.columns(2)

    with col1:

        new_calorie = st.number_input("每日熱量目標 (kcal)", value=float(goals.get("calorie", 2000)), step=50.0)

        new_protein = st.number_input("每日蛋白質目標 (g)", value=float(goals.get("protein", 60)), step=5.0)

    with col2:

        new_carb = st.number_input("每日碳水目標 (g)", value=float(goals.get("carb", 250)), step=10.0)

        new_fat = st.number_input("每日脂肪目標 (g)", value=float(goals.get("fat", 65)), step=5.0)

        new_water = st.number_input("每日水量目標 (ml)", value=float(goals.get("water", 2000)), step=100.0)

    if st.button("儲存目標修改"):

        try:

            application.update_student_goals(current_auth_context(), uid, {

                "calorie": new_calorie,

                "protein": new_protein,

                "carb": new_carb,

                "fat": new_fat,

                "water": new_water,

            })

            _clear_analysis_cache()

            st.success("目標已更新！")

            st.rerun()

        except Exception as exc:

            st.error(safe_failure_message("coach_goals.update", exc))

    st.divider()

    st.subheader("體重趨勢")

    weight_records = sheets.get_weight_records(uid)

    if weight_records:

        weight_data = {"日期": [], "體重 (kg)": []}

        for r in weight_records[-14:]:

            weight_data["日期"].append(r.get("timestamp", "")[:10])

            weight_data["體重 (kg)"].append(r.get("weight_kg", 0))

        st.line_chart(weight_data, x="日期", y="體重 (kg)")

    else:

        st.info("尚無體重記錄")

# =============================================================================
# 教練端：學員歷史頁面（圖表 / 教練備註 / 匯出 PDF + CSV）

# =============================================================================
# 教練端：學員歷史頁面（圖表 / 教練備註 / 匯出 PDF + CSV）
# =============================================================================

def _build_history_csv(student, daily, weights, trainings, notes, start_date, end_date):
    return build_history_csv(
        student, daily, weights, trainings, notes, start_date, end_date
    )

def _build_history_pdf(student, daily, weights, trainings, notes, start_date, end_date):
    # 中文字型設定
    # 中文字型設定
    import matplotlib.font_manager as fm
    # 嘗試使用系統中文字型
    # 內嵌中文字型（放在 assets/fonts/ 目錄）
    # 嘗試載入內嵌中文字型
    font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansTC-Regular.otf")

    if os.path.exists(font_path):
        # 使用 addfont 註冊字型
        try:
            fm.fontManager.addfont(font_path)
            _plt.rcParams["font.family"] = "sans-serif"
            _plt.rcParams["font.sans-serif"] = ["Noto Sans TC", "DejaVu Sans"]
        except Exception:
            prop = fm.FontProperties(fname=font_path)
            _plt.rcParams["font.family"] = prop.get_family()
            _plt.rcParams["font.sans-serif"] = [font_path]
    else:
        # Fallback 到系統字型
        font_paths = [
            "C:/Windows/Fonts/msjh.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    fm.fontManager.addfont(fp)
                    _plt.rcParams["font.family"] = "sans-serif"
                    _plt.rcParams["font.sans-serif"] = ["Noto Sans CJK TC", "DejaVu Sans"]
                except Exception:
                    prop = fm.FontProperties(fname=fp)
                    _plt.rcParams["font.family"] = prop.get_family()
                    _plt.rcParams["font.sans-serif"] = [fp]
                break
        else:
            _plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
            _plt.rcParams["font.family"] = "sans-serif"

    _plt.rcParams["axes.unicode_minus"] = False
    name = student.get("name", student.get("username", "未知"))
    buf = _io.BytesIO()
    with _PdfPages(buf) as pdf:
        # Page 1: 摘要
        fig = _plt.figure(figsize=(8.27, 11.69))
        fig.suptitle(str(name) + " 歷史紀錄", fontsize=18, fontweight="bold")
        ax = fig.add_subplot(111)
        ax.axis("off")
        days_count = (end_date - start_date).days + 1
        total_cal = sum(v["calorie"] for v in daily.values())
        total_pro = sum(v["protein"] for v in daily.values())
        total_water = sum(v["water"] for v in daily.values())
        avg_cal = total_cal / max(days_count, 1)
        avg_pro = total_pro / max(days_count, 1)
        sorted_weights = sorted(
            [r for r in weights if start_date <= _parse_record_date(r.get("timestamp", "")) <= end_date],
            key=lambda r: r.get("timestamp", ""),
        )
        first_w = sorted_weights[0].get("weight_kg") if sorted_weights else None
        last_w  = sorted_weights[-1].get("weight_kg") if sorted_weights else None
        weight_delta = (last_w - first_w) if (first_w is not None and last_w is not None) else None
        first_s = ("%.1f kg" % first_w) if first_w is not None else "-"
        last_s  = ("%.1f kg" % last_w)  if last_w  is not None else "-"
        delta_s = ""
        if weight_delta is not None:
            delta_s = "（%+.1f kg）" % weight_delta
        lines = [
            "區間：" + start_date.isoformat() + " ~ " + end_date.isoformat() + "（" + str(days_count) + " 天）",
            "",
            "平均熱量：%.0f kcal / 天" % avg_cal,
            "平均蛋白質：%.0f g / 天" % avg_pro,
            "總飲水量：%.0f ml" % total_water,
            "體重：" + first_s + " -> " + last_s + delta_s,
            "備註數：" + str(len(notes)) + " 筆",
        ]
        ax.text(0.05, 0.95, "\n".join(lines), va="top", ha="left", fontsize=12)
        pdf.savefig(fig, bbox_inches="tight")
        _plt.close(fig)

        # Page 2: 飲食組成圓餅
        total_pro2 = sum(v["protein"] for v in daily.values())
        total_carb = sum(v["carb"] for v in daily.values())
        total_fat = sum(v["fat"] for v in daily.values())
        if total_pro2 + total_carb + total_fat > 0:
            fig, ax = _plt.subplots(figsize=(8.27, 11.69))
            fig.suptitle("飲食組成（區間總和）", fontsize=16, fontweight="bold")
            ax.pie(
                [total_carb, total_pro2, total_fat],
                labels=[
                    "醣類\n%.0fg" % total_carb,
                    "蛋白質\n%.0fg" % total_pro2,
                    "脂質\n%.0fg" % total_fat,
                ],
                autopct="%1.1f%%",
                startangle=90,
                colors=["#FFD166", "#06D6A0", "#EF476F"],
            )
            ax.axis("equal")
            pdf.savefig(fig, bbox_inches="tight")
            _plt.close(fig)

        # Page 3: 熱量 / 蛋白質 / 水量
        if daily:
            xs = [d.strftime("%m/%d") for d in sorted(daily.keys())]
            cals = [daily[d]["calorie"] for d in sorted(daily.keys())]
            pros = [daily[d]["protein"] for d in sorted(daily.keys())]
            wats = [daily[d]["water"] for d in sorted(daily.keys())]
            fig, axes = _plt.subplots(3, 1, figsize=(8.27, 11.69))
            fig.suptitle("每日攝取趨勢", fontsize=16, fontweight="bold")
            axes[0].plot(xs, cals, marker="o", color="#118AB2")
            axes[0].set_title("熱量 (kcal)")
            axes[0].grid(True, alpha=0.3)
            axes[1].plot(xs, pros, marker="o", color="#06D6A0")
            axes[1].set_title("蛋白質 (g)")
            axes[1].grid(True, alpha=0.3)
            axes[2].bar(xs, wats, color="#073B4C")
            axes[2].set_title("水量 (ml)")
            axes[2].grid(True, alpha=0.3, axis="y")
            for a in axes:
                a.tick_params(axis="x", rotation=45)
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig, bbox_inches="tight")
            _plt.close(fig)

        # Page 4: 體重
        if sorted_weights:
            fig, ax = _plt.subplots(figsize=(8.27, 11.69))
            fig.suptitle("體重變化", fontsize=16, fontweight="bold")
            xs = [r.get("timestamp", "")[:10] for r in sorted_weights]
            ys = [r.get("weight_kg", 0) for r in sorted_weights]
            ax.plot(xs, ys, marker="o", color="#EF476F")
            ax.set_ylabel("kg")
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig, bbox_inches="tight")
            _plt.close(fig)

        # Page 5: 訓練 + 備註
        fig, ax = _plt.subplots(figsize=(8.27, 11.69))
        ax.axis("off")
        fig.suptitle("訓練記錄與教練備註", fontsize=16, fontweight="bold")
        text_lines = ["【訓練記錄】"]
        if trainings:
            for r in sorted(trainings, key=lambda x: x.get("timestamp", ""))[-20:]:
                detail = sheets.format_training_record(r)
                text_lines.append("  " + r.get("timestamp", "")[:10] + "  " + (detail or "-"))
        else:
            text_lines.append("  （無）")
        text_lines += ["", "【教練備註】"]
        if notes:
            for n in notes[-20:]:
                text_lines.append("  " + n.get("timestamp", "")[:19] + "  " + str(n.get("coach_id", "")) + "：" + str(n.get("note", "")))
        else:
            text_lines.append("  （無）")
        ax.text(0.05, 0.95, "\n".join(text_lines), va="top", ha="left", fontsize=10)
        pdf.savefig(fig, bbox_inches="tight")
        _plt.close(fig)
    return buf.getvalue()

def _render_coach_history_data_tools(
    student: dict[str, object],
    user_id: str,
    display_name: str,
    history_data: StudentHistoryData,
) -> None:
    """Keep import and export utilities separate from the shared charts."""
    tools = st.expander(
        "資料工具",
        icon=":material/build:",
        key="coach_history_data_tools",
        on_change="rerun",
    )
    if not tools.open:
        return

    with tools:
        st.subheader("匯入 Excel")
        uploaded_file = st.file_uploader(
            "選擇 Excel 檔案（每個工作表代表一個月份）",
            type=["xlsx"],
            key="coach_history_excel_import",
        )
        if uploaded_file is not None:
            try:
                with st.spinner("分析 Excel 檔案中..."):
                    analysis_result = application.import_student_records(
                        current_auth_context(),
                        user_id,
                        excel_file_bytes=uploaded_file.getvalue(),
                        overwrite_duplicates=False,
                    )
                metric_columns = st.columns(3)
                metric_columns[0].metric("可新增", f"{analysis_result['imported']} 筆")
                metric_columns[1].metric("將覆寫", f"{analysis_result['overwritten']} 筆")
                metric_columns[2].metric("將跳過", f"{analysis_result['skipped']} 筆")
                if analysis_result["errors"]:
                    with st.expander("匯入錯誤", icon=":material/warning:"):
                        for error in analysis_result["errors"]:
                            st.warning(error)
                if analysis_result["imported"] > 0 or analysis_result["skipped"] > 0:
                    overwrite_mode = st.segmented_control(
                        "遇到重複日期",
                        ("跳過", "覆寫"),
                        default="跳過",
                        required=True,
                        key="coach_history_import_duplicate_mode",
                    )
                    if st.button(
                        "確認匯入",
                        type="primary",
                        width="stretch",
                        key="coach_history_confirm_import",
                    ):
                        with st.spinner("匯入資料中..."):
                            final_result = application.import_student_records(
                                current_auth_context(),
                                user_id,
                                precomputed_data=analysis_result["parsed_data"],
                                operation_token=analysis_result["parsed_data"]["operation_token"],
                                overwrite_duplicates=overwrite_mode == "覆寫",
                            )
                        _clear_analysis_cache()
                        st.session_state.pop(_HISTORY_EXPORT_CACHE_KEY, None)
                        st.success(
                            "匯入完成！新增 "
                            f"{final_result['imported']} 筆，覆寫 "
                            f"{final_result['overwritten']} 筆，跳過 "
                            f"{final_result['skipped']} 筆"
                        )
            except Exception as exc:
                st.error(safe_failure_message("coach_history.import", exc))

        st.subheader("匯出資料")
        range_mode = st.segmented_control(
            "匯出範圍",
            ("7 天", "30 天", "自訂日期"),
            default="7 天",
            required=True,
            key="coach_history_export_range",
            width="stretch",
        )
        today = date.today()
        if range_mode == "30 天":
            start_date, end_date = today - timedelta(days=29), today
        elif range_mode == "自訂日期":
            start_column, end_column = st.columns(2)
            start_date = start_column.date_input(
                "開始日期",
                today - timedelta(days=6),
                max_value=today,
                key="coach_history_export_start",
            )
            end_date = end_column.date_input(
                "結束日期",
                today,
                max_value=today,
                key="coach_history_export_end",
            )
            if start_date > end_date:
                start_date, end_date = end_date, start_date
                st.warning("開始日期晚於結束日期，已自動交換。")
        else:
            start_date, end_date = today - timedelta(days=6), today

        export_signature = (
            user_id,
            start_date.isoformat(),
            end_date.isoformat(),
        )
        prepared_export = st.session_state.get(_HISTORY_EXPORT_CACHE_KEY)
        if not isinstance(prepared_export, dict) or prepared_export.get(
            "signature"
        ) != export_signature:
            st.session_state.pop(_HISTORY_EXPORT_CACHE_KEY, None)
            prepared_export = None

        if st.button(
            "準備下載檔案",
            icon=":material/download:",
            key="coach_history_prepare_export",
            width="stretch",
        ):
            try:
                note_rows = sheets.get_notes(user_id)
                daily = _history_aggregate_daily(
                    history_data.records, start_date, end_date
                )
                weights = [
                    row
                    for row in history_data.weights
                    if start_date
                    <= _parse_record_date(row.get("timestamp", ""))
                    <= end_date
                ]
                trainings = [
                    row
                    for row in history_data.trainings
                    if start_date
                    <= _parse_record_date(row.get("timestamp", ""))
                    <= end_date
                ]
                notes = [
                    row
                    for row in note_rows
                    if start_date
                    <= _parse_record_date(row.get("timestamp", ""))
                    <= end_date
                ]
                prepared_export = {
                    "signature": export_signature,
                    "csv": _build_history_csv(
                        student,
                        daily,
                        weights,
                        trainings,
                        notes,
                        start_date,
                        end_date,
                    ),
                    "pdf": _build_history_pdf(
                        student,
                        daily,
                        weights,
                        trainings,
                        notes,
                        start_date,
                        end_date,
                    ),
                }
                st.session_state[_HISTORY_EXPORT_CACHE_KEY] = prepared_export
            except Exception as exc:
                st.error(
                    safe_data_read_failure_message(
                        "coach_history.export", exc
                    )
                )
                prepared_export = None

        if prepared_export is None:
            st.caption("選擇匯出範圍後，再準備下載檔案。")
        else:
            download_columns = st.columns(2)
            filename = (
                f"{display_name}_歷史_"
                f"{start_date.isoformat()}_{end_date.isoformat()}"
            )
            download_columns[0].download_button(
                "下載 CSV",
                data=prepared_export["csv"],
                file_name=f"{filename}.csv",
                mime="text/csv",
                width="stretch",
                key="coach_history_download_csv",
            )
            download_columns[1].download_button(
                "下載 PDF",
                data=prepared_export["pdf"],
                file_name=f"{filename}.pdf",
                mime="application/pdf",
                width="stretch",
                key="coach_history_download_pdf",
            )


def page_coach_student_history() -> None:
    """Render the same read-only charts used by the selected student."""
    with st.container(key="coach_student_history_page"):
        st.header("學員歷史")
        user_id = str(st.session_state.get("view_student_id") or "")
        if not user_id:
            try:
                students = application.get_students(current_auth_context())
            except Exception as exc:
                st.error(safe_failure_message("coach_history.list_students", exc))
                return
            if not students:
                st.info("目前沒有學員。")
                return
            labels = {
                str(student.get("user_id") or ""): str(
                    student.get("name") or student.get("username") or "未知"
                )
                for student in students
            }
            selected_user = st.selectbox(
                "選擇學員",
                options=list(labels),
                format_func=lambda value: labels.get(value, value),
                key="coach_history_student_picker",
            )
            if st.button(
                "查看歷史",
                type="primary",
                key="coach_history_student_picker_button",
            ):
                st.session_state.view_student_id = selected_user
                st.session_state.pop(_HISTORY_EXPORT_CACHE_KEY, None)
                st.rerun()
            return

        student = application.get_student(current_auth_context(), user_id)
        if not student:
            st.error("沒有權限查看此學員，請返回總覽重新選擇。")
            if st.button("返回學員狀態", icon=":material/arrow_back:"):
                st.session_state.page = "學員狀態"
                st.session_state.pop("view_student_id", None)
                st.session_state.pop(_HISTORY_EXPORT_CACHE_KEY, None)
                st.rerun()
            return

        display_name = str(
            student.get("name") or student.get("username") or "未知"
        )
        with st.container(horizontal=True, vertical_alignment="center"):
            if st.button(
                "返回總覽",
                icon=":material/arrow_back:",
                key="coach_history_back",
            ):
                st.session_state.page = "學員狀態"
                st.session_state.pop("view_student_id", None)
                st.session_state.pop(_HISTORY_EXPORT_CACHE_KEY, None)
                st.rerun()
            st.subheader(f"{display_name} 的歷史紀錄")

        try:
            history_data = load_student_history_data(user_id)
        except Exception as exc:
            st.error(
                safe_data_read_failure_message("coach_history.read", exc)
            )
            return

        with st.container(key="student_history_page"):
            render_student_history_charts(
                user_id,
                allow_record_actions=False,
                history_data=history_data,
            )

        _render_coach_history_data_tools(
            student, user_id, display_name, history_data
        )


# =============================================================================

# END_HISTORY_BLOCK

# =============================================================================
