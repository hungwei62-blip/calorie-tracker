"""學員端、登入與註冊頁面。"""
from __future__ import annotations
from datetime import date, datetime, timedelta
import hashlib
import html
from io import BytesIO
import math
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from services import application, auth, gemini, metrics, sheets
from services.security import (
    LOGIN_RATE_LIMITER,
    PASSWORD_RESET_RATE_LIMITER,
    log_event,
    safe_failure_message,
)
from domain.daily_completion import DailyCompletion, calculate_daily_completion
from domain.history import (
    NutritionHistoryPoint,
    TrainingCalendarDay,
    WaterHistoryPoint,
    WeightHistoryPoint,
    build_nutrition_history_series,
    build_training_calendar,
    build_water_history_series,
    build_weight_history_series,
    history_date_range,
    nutrition_history_averages,
    shift_training_period,
    summarize_weight_measurements,
    training_period_bounds,
    water_history_average,
)
from domain.nutrition import EXERCISE_LEVELS, calculate_bmr, calculate_goals, calculate_tdee
from pages.common import (
    DEFAULT_GOALS, TRAINING_TYPES, _clear_analysis_cache, _fetch_goals_cached,
    _fetch_records_cached, _today_range, do_logout,
    current_auth_context, get_default_avatar_source,
)
from ui.camera import camera_capture
from pages.student.history_records import render_daily_record_manager

DAILY_RECORD_TABS = ("食物", "飲水", "訓練", "體重")
DAILY_RECORD_TAB_TARGET_KEY = "daily_record_tab_target"
LEGACY_DAILY_RECORD_TABS = {
    "🍴 飲食": "食物",
    "⚖️ 體重": "體重",
    "🏋️ 訓練": "訓練",
}
HISTORY_PRIMARY = "#A8D5C2"
HISTORY_PRIMARY_DARK = "#5A9C84"
HISTORY_ACCENT = "#F4B183"
HISTORY_ACCENT_DARK = "#C87943"
HISTORY_SECONDARY_TEXT = "#7D8C8A"
WATER_HISTORY_PRIMARY = "#BFD8FF"
WATER_HISTORY_SECONDARY = "#7E8FA3"


def _to_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _progress_percentage(actual: object, goal: object) -> float:
    actual_value = max(_to_float(actual), 0.0)
    goal_value = _to_float(goal)
    if goal_value <= 0:
        return 0.0
    return min(actual_value / goal_value * 100, 100.0)


def _goal_status(
    actual: object,
    goal: object,
    *,
    over_only: bool = False,
) -> tuple[str, str] | None:
    """Return the compact card status, or nothing when no valid goal exists."""
    actual_value = max(_to_float(actual), 0.0)
    goal_value = _to_float(goal)
    if goal_value <= 0:
        return None
    if over_only:
        return ("超過", "#b85c5c") if actual_value > goal_value else None
    if actual_value >= goal_value:
        return "達成", "#3f7d5a"
    return "不足", "#b85c5c"


def _goal_tooltip_html(label: str, goal: object, unit: str) -> str:
    """Build the non-interactive goal tooltip rendered over a progress card."""
    goal_value = _to_float(goal)
    if not math.isfinite(goal_value) or goal_value <= 0:
        message = "尚未設定目標"
    else:
        message = (
            f"{html.escape(label)}目標 {goal_value:,.0f} "
            f"{html.escape(unit)}"
        )
    return (
        '<div class="goal-card-tooltip" role="tooltip">'
        f"{message}"
        "</div>"
    )


def build_daily_progress_figure(
    label: str,
    actual: object,
    goal: object,
    unit: str,
    display_date: date | None = None,
) -> go.Figure:
    """建立適合桌面三欄與手機雙欄的緊湊 Plotly 圓環圖。"""
    actual_value = max(_to_float(actual), 0.0)
    percentage = _progress_percentage(actual_value, goal)
    date_label = (display_date or date.today()).strftime("%d %B")
    card_background = {
        "水量": "#e0edf6",
        "蛋白質": "#f8ebe7",
    }.get(label, "#c7edf6")

    figure = go.Figure(
        data=[
            go.Pie(
                values=[percentage, 100 - percentage],
                hole=0.68,
                marker={"colors": ["#ffffff", "rgba(255, 255, 255, 0.30)"]},
                domain={"x": [0.48, 1.0], "y": [0.08, 0.92]},
                sort=False,
                direction="clockwise",
                showlegend=False,
                hoverinfo="none",
                textinfo="none",
            )
        ]
    )
    annotations = [
            {
                "x": 0.03,
                "y": 0.84,
                "xref": "paper",
                "yref": "paper",
                "text": label,
                "font": {
                    "family": "system-ui, -apple-system, sans-serif",
                    "size": 15,
                    "weight": 500,
                    "color": "#1a1a1a",
                },
                "showarrow": False,
                "xanchor": "left",
            },
            {
                "x": 0.03,
                "y": 0.50,
                "xref": "paper",
                "yref": "paper",
                "text": f"<b>{percentage:.0f}%</b>",
                "font": {"size": 26, "color": "#1a2530"},
                "showarrow": False,
                "xanchor": "left",
                "yanchor": "middle",
            },
            {
                "x": 0.03,
                "y": 0.14,
                "xref": "paper",
                "yref": "paper",
                "text": date_label,
                "font": {"size": 11, "color": "#5a6e7f"},
                "showarrow": False,
                "xanchor": "left",
            },
            {
                "x": 0.74,
                "y": 0.50,
                "xref": "paper",
                "yref": "paper",
                "text": f"<b>{actual_value:.0f}</b>",
                "font": {"size": 18, "color": "#1a2530"},
                "showarrow": False,
                "xanchor": "center",
                "yanchor": "middle",
            },
            {
                "x": 0.74,
                "y": 0.34,
                "xref": "paper",
                "yref": "paper",
                "text": unit,
                "font": {"size": 8, "color": "#5a6e7f"},
                "showarrow": False,
                "xanchor": "center",
            },
        ]
    status = _goal_status(actual_value, goal)
    if status:
        status_text, status_color = status
        annotations.append(
            {
                "x": 0.96,
                "y": 0.04,
                "xref": "paper",
                "yref": "paper",
                "text": f"<b>{status_text}</b>",
                "font": {"size": 11, "color": status_color},
                "showarrow": False,
                "xanchor": "right",
                "yanchor": "bottom",
            }
        )

    figure.update_layout(
        paper_bgcolor=card_background,
        plot_bgcolor=card_background,
        height=180,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        showlegend=False,
        annotations=annotations,
    )
    return figure


def build_calorie_figure(actual: object, goal: object) -> go.Figure:
    """建立學員首頁使用的白色 Calories 圓環卡。"""
    actual_value = max(_to_float(actual), 0.0)
    percentage = _progress_percentage(actual_value, goal)

    figure = go.Figure(
        data=[
            go.Pie(
                values=[percentage, 100 - percentage],
                hole=0.76,
                domain={"x": [0, 1], "y": [0, 1]},
                marker={"colors": ["#ffbfa3", "#f0f0f0"]},
                sort=False,
                direction="clockwise",
                showlegend=False,
                hoverinfo="none",
                textinfo="none",
            )
        ]
    )
    annotations = [
        {
            "x": 0.02,
            "y": 1.22,
            "xref": "paper",
            "yref": "paper",
            "text": "卡路里",
            "font": {
                "family": "system-ui, -apple-system, sans-serif",
                "size": 15,
                "weight": 500,
                "color": "#1a1a1a",
            },
            "showarrow": False,
            "align": "left",
            "xanchor": "left",
            "yanchor": "top",
        },
        {
            "x": 0.5,
            "y": 0.5,
            "xref": "paper",
            "yref": "paper",
            "text": f"<b style='font-size:28px; color:#1a1a1a;'>{actual_value:.0f}</b>",
            "showarrow": False,
            "align": "center",
        },
        {
            "x": 0.5,
            "y": 0.22,
            "xref": "paper",
            "yref": "paper",
            "text": (
                "<span style='font-size:12px; color:#666666; "
                "font-weight:500;'>Kcal</span>"
            ),
            "showarrow": False,
            "align": "center",
        },
    ]
    status = _goal_status(actual_value, goal, over_only=True)
    if status:
        status_text, status_color = status
        annotations.append(
            {
                "x": 0.96,
                "y": 0.04,
                "xref": "paper",
                "yref": "paper",
                "text": f"<b>{status_text}</b>",
                "font": {"size": 11, "color": status_color},
                "showarrow": False,
                "xanchor": "right",
                "yanchor": "bottom",
            }
        )

    figure.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
        height=180,
        font={
            "family": (
                "system-ui, -apple-system, BlinkMacSystemFont, "
                "'Segoe UI', Roboto, sans-serif"
            )
        },
        showlegend=False,
        annotations=annotations,
    )
    return figure


def _weight_summary(
    weight_records: list[dict[str, object]],
    *,
    end_date: date | None = None,
) -> tuple[float | None, str]:
    """從 Weight 紀錄取得最新體重與相較前一筆的趨勢文字。"""
    summary = summarize_weight_measurements(weight_records, end_date=end_date)
    if summary is None:
        return None, ""

    latest_weight = summary.latest_weight
    if summary.difference is None or summary.percentage is None:
        return latest_weight, ""

    difference = summary.difference
    difference_percentage = summary.percentage
    if difference < 0:
        trend = f"⇩ {abs(difference):.1f} Kg ({difference_percentage:.1f}%)"
    elif difference > 0:
        trend = f"⇧ {abs(difference):.1f} Kg (+{difference_percentage:.1f}%)"
    else:
        trend = "⬌ 體重維持持平"
    return latest_weight, trend


_COMPLETION_ICONS = {
    "體重": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="5" width="16" height="15" rx="4"/><path d="M9 9.5c1.7-1.4 4.3-1.4 6 0"/><path d="m12 9.5 1.2 2"/></svg>',
    "水量": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3S6.5 9.2 6.5 14a5.5 5.5 0 0 0 11 0C17.5 9.2 12 3 12 3Z"/></svg>',
    "蛋白質": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v7M4.5 3v5.5A2.5 2.5 0 0 0 7 11v10M9.5 3v5.5A2.5 2.5 0 0 1 7 11"/><path d="M16 3v18M16 3c2.2 1.5 3.5 4 3.5 6.5H16"/></svg>',
    "卡路里": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13.2 3.5c.4 3-1.5 4.3-3 6.2-1.4 1.7-2.2 3.3-1.5 5.5.4-1.3 1.3-2.2 2.5-3.2-.2 2.3 1 3.7 2.4 4.8 1.5-1.2 2.2-2.8 1.8-4.8 1.5 1.4 2.4 3 2.1 4.9-.4 2.5-2.5 4.1-5.3 4.1-3.4 0-5.7-2.2-5.7-5.5 0-4.6 4.2-6.1 6.7-12Z"/></svg>',
}


def _completion_badge_svg(completed: bool) -> str:
    path = '<path d="m4 8 2.5 2.5L12 5"/>' if completed else '<path d="m5 5 6 6M11 5l-6 6"/>'
    return f'<svg viewBox="0 0 16 16" aria-hidden="true">{path}</svg>'


def _format_daily_total(value: object) -> str:
    """Format a daily total as a safe, non-negative whole number."""
    number = _to_float(value)
    if not math.isfinite(number) or number < 0:
        number = 0.0
    return f"{number:,.0f}"


def build_daily_completion_html(
    completion: DailyCompletion,
    totals: dict[str, object],
) -> str:
    """Render the interactive completion card and its upward value popover."""
    statuses = (
        ("體重", completion.weight_logged),
        ("水量", completion.water_logged),
        ("蛋白質", completion.protein_logged),
        ("卡路里", completion.calories_logged),
    )
    items = []
    for label, completed in statuses:
        status_text = "已完成" if completed else "未完成"
        state_class = "is-complete" if completed else "is-incomplete"
        items.append(
            f'<div class="daily-completion-item {state_class}" role="listitem" '
            f'aria-label="{label}：{status_text}" title="{label}：{status_text}">'
            f'<span class="daily-completion-icon">{_COMPLETION_ICONS[label]}</span>'
            f'<span class="daily-completion-badge">{_completion_badge_svg(completed)}</span>'
            '</div>'
        )
    bonus_class = " has-bonus" if completion.bonus else ""
    daily_values = (
        ("熱量", _format_daily_total(totals.get("calories")), "kcal"),
        ("蛋白質", _format_daily_total(totals.get("protein")), "g"),
        ("飲水", _format_daily_total(totals.get("water")), "ml"),
    )
    value_rows = "".join(
        '<div class="daily-completion-value-row">'
        f'<span>{label}</span><strong>{value} {unit}</strong>'
        "</div>"
        for label, value, unit in daily_values
    )
    return (
        '<details class="daily-completion-details">'
        f'<summary class="daily-completion-card{bonus_class}" '
        'aria-label="今日記錄完成度，點擊查看今日輸入數值">'
        '<div class="daily-completion-heading"><span>今日記錄完成度</span>'
        f'<strong>{completion.percentage}%</strong></div>'
        '<div class="daily-completion-track" role="progressbar" aria-valuemin="0" '
        f'aria-valuemax="100" aria-valuenow="{completion.percentage}">'
        f'<span style="width: {completion.percentage}%"></span></div>'
        '<div class="daily-completion-footer">'
        f'<div class="daily-completion-meta">目標達成 {completion.completed_count} / 3 項</div>'
        f'<div class="daily-completion-items" role="list">{"".join(items)}</div></div>'
        '</summary>'
        '<div class="daily-completion-values" role="region" '
        'aria-label="今日輸入數值">'
        '<div class="daily-completion-values-title">今日輸入</div>'
        f'{value_rows}</div>'
        '</details>'
    )


def open_daily_record_tab(tab: str) -> None:
    """將學員導向日常紀錄頁的指定分頁。"""
    tab = LEGACY_DAILY_RECORD_TABS.get(tab, tab)
    if tab not in DAILY_RECORD_TABS:
        raise ValueError("未知的日常紀錄分頁")
    st.session_state.page = "記錄飲食"
    st.session_state[DAILY_RECORD_TAB_TARGET_KEY] = tab


def _save_initial_registration_weight(
    timestamp: str, user_id: str, initial_weight: float
) -> str | None:
    """Persist the registration weight without turning a partial write into failure."""
    try:
        sheets.append_weight(timestamp, user_id, float(initial_weight))
    except Exception:
        return "帳號已建立，但初始體重尚未儲存，請到日常紀錄補填體重。"
    return None


def page_tdee_questionnaire() -> None:

    st.header("📋 設定你的營養目標")

    st.caption("回答以下問題，讓系統為你計算個人化的營養目標")

    with st.form("tdee_form"):

        st.subheader("基本資料")

        col1, col2 = st.columns(2)

        with col1:

            weight = st.number_input("體重 (kg)", value=60.0, step=0.1, min_value=30.0, max_value=200.0)

            height = st.number_input("身高 (cm)", value=165.0, step=0.1, min_value=100.0, max_value=250.0)

        with col2:

            age = st.number_input("年齡", value=25, step=1, min_value=10, max_value=100)

            gender = st.radio("性別", ["男", "女"], horizontal=True)

        st.subheader("活動程度")

        exercise_level = st.selectbox("每週運動頻率", EXERCISE_LEVELS, index=1)

        st.subheader("健身目標")

        goal_type = st.radio("你的目標是？", ["減脂", "維持", "增肌"], horizontal=True, index=1)

        submitted = st.form_submit_button("計算並儲存目標", width="stretch")

    if submitted:

        bmr = calculate_bmr(weight, height, age, gender)

        tdee = calculate_tdee(bmr, exercise_level)

        goals = calculate_goals(weight, tdee, goal_type)

        goals["bmr"] = bmr

        goals["carb"] = 0.0

        goals["fat"] = 0.0

        try:

            uid = st.session_state.user_id

            application.update_student_bmr(current_auth_context(), uid, bmr)

            application.update_student_goals(current_auth_context(), uid, goals)

            sheets.set_user_record_mode(uid, "simple")

            _clear_analysis_cache()

            st.success("目標設定完成！")

            st.balloons()

            st.session_state.page = "個人"

            st.rerun()

        except Exception as exc:

            st.error(safe_failure_message("tdee.save", exc))

# =============================================================================

# 登入頁面

# =============================================================================


def page_login() -> None:
    # Ensure the route marker exists before deciding whether to render the brand.
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    brand_html = (
        '<div class="auth-brand-lockup">'
        '<div role="heading" aria-level="1" class="auth-brand-title">'
        '<span class="auth-brand-english">Project Prime</span>'
        '<span class="auth-brand-divider">|</span>'
        '<span class="auth-brand-chinese">巔峰計畫</span>'
        "</div>"
        '<p class="auth-brand-tagline">'
        "<span>練對、吃對</span>"
        "<span>剩下交給時間</span>"
        "<span>把自己推向人生最好的狀態</span>"
        "</p>"
        "</div>"
    )
    if st.session_state.auth_mode != "register":
        with st.container(key="auth_brand"):
            st.markdown(brand_html, unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        # ==================== 登入表單 ====================
        with st.container(key="login_panel"):
            with st.form("login_form"):
                username = st.text_input("帳號", key="login_user")
                password = st.text_input("密碼", type="password", key="login_pwd")
                submit = st.form_submit_button("登入", width="stretch")

        if submit:
            if LOGIN_RATE_LIMITER.is_blocked(username):
                st.error("登入嘗試過於頻繁，請稍後再試")
                return
            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error(safe_failure_message("login.read_users", exc))
                return
            user = auth.find_user(rows, username)
            if not user or not auth.verify_password(password, user.get("password_hash", "")):
                blocked = LOGIN_RATE_LIMITER.register_failure(username)
                log_event("login.failure", result="blocked" if blocked else "denied")
                st.error(
                    "登入嘗試過於頻繁，請稍後再試"
                    if blocked
                    else "帳號或密碼錯誤"
                )
                return

            LOGIN_RATE_LIMITER.register_success(username)
            log_event("login.success", result="success", actor_id=str(user.get("user_id") or ""))

            st.session_state.user_id = user.get("user_id")
            st.session_state.username = user.get("username")
            st.session_state.name = str(user.get("name") or "").strip() or "學員"
            st.session_state.role = sheets.get_user_role(str(user.get("user_id") or ""))

            if st.session_state.role in ("coach", "admin"):
                st.session_state.page = "學員狀態"
            else:
                st.session_state.page = "個人"
            st.success("登入成功！")
            st.rerun()

        # 切換到註冊
        with st.container(key="login_secondary_action"):
            if st.button("註冊新學員", key="nav_to_register"):
                st.session_state.auth_mode = "register"
                st.rerun()
            if st.button("忘記密碼", key="nav_to_forgot_password"):
                st.session_state.auth_mode = "forgot"
                st.rerun()

    elif st.session_state.auth_mode == "register":
        # ==================== 註冊表單 ====================
        with st.container(key="registration_page", gap="small"):
            st.subheader("註冊學員帳號", text_alignment="center")

            with st.form("signup_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_user = st.text_input("帳號", placeholder="輸入帳號")
                    new_name = st.text_input("姓名", placeholder="輸入真實姓名")
                    new_pwd = st.text_input("密碼", type="password")
                    new_pwd2 = st.text_input("確認密碼", type="password")
                with col2:
                    initial_weight = st.number_input("目前體重 (kg)", value=60.0, step=0.1, min_value=30.0, max_value=200.0)
                    goal_type = st.selectbox("目標", ["減脂", "維持", "增肌"], index=1)

                submitted = st.form_submit_button("註冊並登入", width="stretch")

        if submitted:
            if not new_user or not new_name or not new_pwd:
                st.error("帳號、姓名和密碼都不能為空")
                return
            if new_pwd != new_pwd2:
                st.error("兩次密碼不一致")
                return
            if len(new_pwd) < 4:
                st.warning("密碼建議至少 4 個字元")

            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error(safe_failure_message("registration.read_users", exc))
                return

            if auth.find_user(rows, new_user):
                st.error("此帳號已被使用")
                return

            try:
                uid = auth.make_user_id()
                pwd_hash = auth.hash_password(new_pwd)

                estimated_tdee = initial_weight * 30
                if goal_type == "減脂":
                    calorie = estimated_tdee - 300
                elif goal_type == "增肌":
                    calorie = estimated_tdee + 300
                else:
                    calorie = estimated_tdee

                protein = initial_weight * 2
                water = initial_weight * 40

                goals = {
                    "calorie": calorie,
                    "protein": protein,
                    "carb": 0,
                    "fat": 0,
                    "water": water,
                }

                primary_coach_id = sheets.get_primary_coach_id()
                registration_timestamp = auth.now_iso()
                sheets.append_user_with_initial_weight(
                    uid,
                    new_user,
                    new_name,
                    pwd_hash,
                    registration_timestamp,
                    goals=goals,
                    coach_id=primary_coach_id,
                    initial_weight=initial_weight,
                    record_mode="simple",
                    weekly_training=4,
                )
                st.session_state.initial_weight_save_warning = None

                st.session_state.user_id = uid
                st.session_state.username = new_user
                st.session_state.name = new_name.strip()
                st.session_state.role = "student"
                st.session_state.needs_tdee_setup = True
                st.success("註冊成功！請先填寫 TDEE 問卷完成設定")
                st.rerun()

            except Exception as exc:
                st.error(safe_failure_message("registration.create", exc))

        # 切換回登入
        if st.button("← 返回登入頁", key="nav_to_login"):
            st.session_state.auth_mode = "login"
            st.rerun()

    else:
        st.subheader("忘記密碼")
        st.info("送出申請後，請聯絡教練協助核對身分。")
        with st.form("forgot_password_form"):
            reset_username = st.text_input("帳號", key="reset_username")
            reset_submitted = st.form_submit_button(
                "送出重設申請", width="stretch"
            )
        if reset_submitted:
            if not PASSWORD_RESET_RATE_LIMITER.is_blocked(reset_username):
                PASSWORD_RESET_RATE_LIMITER.register_failure(reset_username)
                try:
                    application.request_password_reset(reset_username)
                except Exception as exc:
                    safe_failure_message("password_reset.request", exc)
            st.success("若帳號資料正確，教練將收到密碼重設申請。")
        if st.button("← 返回登入頁", key="forgot_back_to_login"):
            st.session_state.auth_mode = "login"
            st.rerun()


def page_force_password_change() -> None:
    """Block normal navigation until a temporary password is replaced."""
    st.header("設定新密碼")
    st.info("你目前使用臨時密碼，請先設定新密碼才能繼續。")
    with st.form("force_password_change_form"):
        new_password = st.text_input("新密碼", type="password")
        confirm_password = st.text_input("確認新密碼", type="password")
        submitted = st.form_submit_button("更新密碼", width="stretch")
    if not submitted:
        return
    if new_password != confirm_password:
        st.error("兩次輸入的密碼不一致")
        return
    try:
        updated = application.change_own_password(
            current_auth_context(), new_password
        )
    except ValueError as exc:
        st.warning(str(exc))
    except Exception as exc:
        st.error(safe_failure_message("password.change", exc))
    else:
        if not updated:
            st.error("找不到目前帳號，請重新登入。")
            return
        st.session_state.password_changed_notice = "密碼已更新"
        st.rerun()



def _resolve_student_name() -> str:
    """取得正式姓名，並為更新前建立的 session 補上 name。"""
    session_name = str(st.session_state.get("name") or "").strip()
    if session_name:
        return session_name

    user_id = str(st.session_state.get("user_id") or "").strip()
    if not user_id:
        return "學員"
    try:
        user = next(
            (
                row for row in sheets.get_users_rows()
                if str(row.get("user_id") or "").strip() == user_id
            ),
            None,
        )
    except Exception:
        return "學員"

    resolved_name = str((user or {}).get("name") or "").strip()
    if not resolved_name:
        return "學員"
    st.session_state.name = resolved_name
    return resolved_name


def _build_student_welcome_html(display_name: str, avatar_source: str) -> str:
    safe_name = html.escape(display_name, quote=True)
    safe_avatar = html.escape(avatar_source, quote=True)
    return f'<div class="student-home-welcome" style="display: flex; align-items: center; gap: 16px; margin-top: 0; margin-bottom: 25px; width: 100%;"><img src="{safe_avatar}" style="width: 56px; height: 56px; border-radius: 50%; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.05);" alt="avatar"><span style="font-size: 24px; font-weight: 700; color: #1a1a1a; font-family: system-ui, -apple-system, sans-serif; white-space: nowrap;">Hello, {safe_name}!</span></div>'


def page_personal() -> None:

    password_notice = st.session_state.pop("password_changed_notice", None)
    if password_notice:
        st.success(password_notice)

    # ============================================================
    # 👋 1. 個人化頭像歡迎區 (單行無縮排安全版)
    # ============================================================
    user_name = _resolve_student_name()
    avatar_source = get_default_avatar_source()
    welcome_html = _build_student_welcome_html(user_name, avatar_source)

    with st.container(key="student_home_header"):
        st.markdown(welcome_html, unsafe_allow_html=True)
        st.header("Overview")

    initial_weight_warning = st.session_state.pop(
        "initial_weight_save_warning", None
    )
    if initial_weight_warning:
        st.warning(initial_weight_warning)

    uid = st.session_state.user_id

    try:

        records = _fetch_records_cached(uid)

        goals = _fetch_goals_cached(uid)

    except Exception as exc:

        st.error(safe_failure_message("student_home.read", exc))

        return

    bmr = goals.get("bmr", 0)

    calorie_goal = goals.get("calorie", 0)

    if bmr <= 0 or calorie_goal <= 0:

        st.warning("你尚未設定營養目標")

        st.info("請先回答 TDEE 問卷，系統會為你計算個人化的營養目標")

        if st.button("前往 TDEE 問卷", width="stretch"):

            st.session_state.page = "TDEE 問卷"

            st.rerun()

        return

    ws, we = _today_range()

    today_records = metrics.filter_records(records, ws, we)

    totals = metrics.sum_totals(today_records).as_dict()

    weight_records = sheets.get_weight_records(uid)
    latest_weight, trend_content = _weight_summary(weight_records, end_date=we)
    weight_logged_today = any(
        str(record.get("timestamp", ""))[:10] == ws.isoformat()
        for record in weight_records
    )
    weight_display_str = f"{latest_weight:.1f}" if latest_weight else "--.-"

    card_html = f"""
    <div class="weight-card">
        <div class="weight-title">體重</div>
        <div class="weight-value">
            {weight_display_str}<span class="weight-unit">Kg</span>
        </div>"""

    if trend_content:
        card_html += f"""
        <div class="weight-trend">
            {trend_content}
        </div>"""

    card_html += """
    </div>"""

    with st.container(key="daily_summary_cards"):
        weight_column, calorie_column = st.columns(2, gap="small")

        with weight_column:
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(
                "新增體重",
                key="weight_add_btn",
                help="新增體重",
                icon=":material/add:",
            ):
                open_daily_record_tab("體重")
                st.rerun()

        with calorie_column:
            with st.container(key="calorie_goal_card", gap=None):
                st.html(_goal_tooltip_html("熱量", calorie_goal, "kcal"))
                st.plotly_chart(
                    build_calorie_figure(totals.get("calories", 0), calorie_goal),
                    key="daily_summary_calories",
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )

    progress_cards = (
        (
            "water",
            "水量",
            totals.get("water", 0),
            goals.get("water", 0),
            "ml",
        ),
        (
            "protein",
            "蛋白質",
            totals.get("protein", 0),
            goals.get("protein", 0),
            "g",
        ),
    )
    with st.container(key="daily_progress_cards"):
        columns = st.columns(2, gap="small")
        for column, (key, label, actual, goal, unit) in zip(columns, progress_cards):
            with column:
                with st.container(key=f"{key}_goal_card", gap=None):
                    st.html(_goal_tooltip_html(label, goal, unit))
                    st.plotly_chart(
                        build_daily_progress_figure(label, actual, goal, unit),
                        key=f"daily_progress_{key}",
                        width="stretch",
                        config={"displayModeBar": False, "responsive": True},
                    )

    completion = calculate_daily_completion(
        totals,
        goals,
        weight_logged=weight_logged_today,
    )
    with st.container(key="daily_completion_card"):
        st.markdown(
            build_daily_completion_html(completion, totals),
            unsafe_allow_html=True,
        )


# =============================================================================

# 學員端：體重記錄

# =============================================================================

def _append_water_record(user_id: str, water_ml: float) -> None:
    """新增一筆可累加的飲水紀錄。"""
    water_value = float(water_ml)
    if not math.isfinite(water_value) or water_value <= 0:
        raise ValueError("飲水量必須大於 0")
    application.append_student_record(
        current_auth_context(),
        timestamp=auth.now_iso(), user_id=user_id,
        meal_type="飲水", food_summary="飲水",
        calories=0, protein=0, carb=0, fat=0, water_ml=water_value,
        image_url="", portion=1,
    )
    _clear_analysis_cache()


def _append_food_record(
    user_id: str, food_summary: str, calories: float, protein: float
) -> None:
    """新增只保存熱量與蛋白質的食物紀錄。"""
    calorie_value = float(calories)
    protein_value = float(protein)
    if any(
        not math.isfinite(value) or value < 0
        for value in (calorie_value, protein_value)
    ):
        raise ValueError("熱量與蛋白質必須是非負有限數字")
    if calorie_value == 0 and protein_value == 0:
        raise ValueError("熱量與蛋白質至少一項必須大於 0")
    application.append_student_record(
        current_auth_context(),
        timestamp=auth.now_iso(), user_id=user_id,
        meal_type="食物", food_summary=food_summary.strip() or "手動紀錄",
        calories=calorie_value, protein=protein_value,
        carb=0, fat=0, water_ml=0, image_url="", portion=1,
    )
    _clear_analysis_cache()


def _clear_pending_food_analysis() -> None:
    st.session_state.pending_analysis = None
    st.session_state.pop("pending_analysis_image_hash", None)


def _set_record_success(record_tab: str) -> None:
    st.session_state.daily_record_flash = {
        "tab": record_tab,
        "message": "紀錄完成",
    }


def _render_record_success(record_tab: str) -> None:
    flash = st.session_state.get("daily_record_flash")
    if not isinstance(flash, dict) or flash.get("tab") != record_tab:
        return
    st.session_state.pop("daily_record_flash", None)
    st.success(str(flash.get("message") or "紀錄完成"))


def _render_water_records() -> None:
    uid = st.session_state.user_id
    _render_record_success("飲水")
    st.caption("記錄這次喝下的水量，今日進度會自動累加。")
    form_version = int(st.session_state.get("water_form_version", 0))
    with st.form(f"water_record_form_{form_version}"):
        water_ml = st.number_input(
            "飲水量 (ml)",
            min_value=0,
            value=None,
            step=100,
            key=f"water_ml_{form_version}",
        )
        submitted = st.form_submit_button("儲存飲水紀錄", width="stretch")
    if submitted:
        try:
            _append_water_record(uid, water_ml or 0)
        except ValueError as exc:
            st.warning(str(exc))
        except Exception:
            st.error("飲水紀錄儲存失敗，請稍後再試。")
        else:
            st.session_state.water_form_version = form_version + 1
            _set_record_success("飲水")
            st.rerun()


def _reset_food_camera() -> None:
    version = int(st.session_state.get("food_camera_version", 0))
    st.session_state.food_camera_version = version + 1


def _selected_food_image_bytes(source: str) -> bytes | None:
    if source == "拍照":
        camera_version = int(st.session_state.get("food_camera_version", 0))
        return camera_capture(key=f"food_camera_{camera_version}")
    image_file = st.file_uploader(
        "從相簿選擇食物照片", type=["jpg", "jpeg", "png"],
        key="food_image_upload",
    )
    return image_file.getvalue() if image_file is not None else None


def _render_photo_food_input(uid: str) -> None:
    source = st.segmented_control(
        "照片來源", ("拍照", "相簿"), default="拍照", key="food_photo_source"
    )
    previous_source = st.session_state.get("food_photo_source_previous")
    if previous_source is not None and previous_source != source:
        _clear_pending_food_analysis()
        _reset_food_camera()
    st.session_state.food_photo_source_previous = source
    image_bytes = _selected_food_image_bytes(source or "拍照")
    image_hash = hashlib.sha256(image_bytes).hexdigest() if image_bytes else None
    pending_hash = st.session_state.get("pending_analysis_image_hash")
    if image_hash and pending_hash and image_hash != pending_hash:
        _clear_pending_food_analysis()

    if st.button(
        "分析照片", key="analyze_food_photo", width="stretch",
        disabled=image_bytes is None,
    ):
        try:
            image = Image.open(BytesIO(image_bytes))
            image.load()
            result = gemini.analyze_image(image)
        except Exception:
            _clear_pending_food_analysis()
            st.error("照片分析失敗，請重新拍照或稍後再試。")
        else:
            if not result["is_food"]:
                _clear_pending_food_analysis()
                st.warning("無法可靠辨識食物，請重新拍照或改用手動輸入。")
            else:
                st.session_state.pending_analysis = result
                st.session_state.pending_analysis_image_hash = image_hash

    result = st.session_state.get("pending_analysis")
    if result and (
        not result.get("is_food")
        or not {"food_summary", "calories", "protein"}.issubset(result)
    ):
        _clear_pending_food_analysis()
        result = None
    if not result:
        return
    st.subheader("分析結果")
    st.write(result["food_summary"])
    calorie_col, protein_col = st.columns(2)
    calorie_col.metric("熱量", f'{result["calories"]:.0f} kcal')
    protein_col.metric("蛋白質", f'{result["protein"]:.0f} g')
    save_col, cancel_col = st.columns(2)
    if save_col.button("確認儲存", key="save_analyzed_food", width="stretch"):
        try:
            _append_food_record(
                uid, result["food_summary"], result["calories"], result["protein"]
            )
        except Exception:
            st.error("食物紀錄儲存失敗，請稍後再試。")
        else:
            _clear_pending_food_analysis()
            _reset_food_camera()
            _set_record_success("食物")
            st.rerun()
    if cancel_col.button("取消", key="cancel_analyzed_food", width="stretch"):
        _clear_pending_food_analysis()
        _reset_food_camera()
        st.rerun()


def _render_manual_food_input(uid: str) -> None:
    form_version = int(st.session_state.get("manual_food_form_version", 0))
    with st.form(f"manual_food_form_{form_version}"):
        calories = st.number_input(
            "熱量 (kcal)", min_value=0, value=None, step=10,
            key=f"manual_calories_{form_version}",
        )
        protein = st.number_input(
            "蛋白質 (g)", min_value=0, value=None, step=1,
            key=f"manual_protein_{form_version}",
        )
        submitted = st.form_submit_button("儲存食物紀錄", width="stretch")
    if submitted:
        try:
            _append_food_record(
                uid, "手動紀錄", calories or 0, protein or 0
            )
        except ValueError as exc:
            st.warning(str(exc))
        except Exception:
            st.error("食物紀錄儲存失敗，請稍後再試。")
        else:
            st.session_state.manual_food_form_version = form_version + 1
            _set_record_success("食物")
            st.rerun()


def _render_food_records() -> None:
    uid = st.session_state.user_id
    with st.container(key="food_record_panel"):
        _render_record_success("食物")
        input_mode = st.segmented_control(
            "輸入方式", ("照片辨識", "手動輸入"),
            default="手動輸入", key="food_input_mode",
        )
        if input_mode == "手動輸入":
            _render_manual_food_input(uid)
        else:
            _render_photo_food_input(uid)


TRAINING_DETAIL_LABELS = {
    "重量訓練": ("strength_detail", "重量訓練內容"),
    "有氧訓練": ("cardio_detail", "有氧訓練內容"),
    "其他": ("other_detail", "其他訓練內容"),
}
TRAINING_WIDGET_KEYS = (
    "training_types",
    "training_strength_detail",
    "training_cardio_detail",
    "training_other_detail",
)


def _training_fields_for_types(selected_types: list[str]) -> list[tuple[str, str, str]]:
    """依固定顯示順序回傳目前應呈現的訓練內容欄位。"""
    return [
        (training_type, *TRAINING_DETAIL_LABELS[training_type])
        for training_type in TRAINING_TYPES
        if training_type in selected_types
    ]


def _clear_training_form_state() -> None:
    for key in TRAINING_WIDGET_KEYS:
        st.session_state.pop(key, None)


def _prepare_daily_record_tab(current_tab: str) -> bool:
    """在真正進入訓練分頁時清空一次表單，回傳是否剛進入。"""
    entered_page = bool(st.session_state.pop("_entered_daily_record_page", False))
    previous_tab = st.session_state.get("_last_daily_record_tab")
    entered_training = current_tab == "訓練" and (
        entered_page or previous_tab != "訓練"
    )
    if entered_training:
        _clear_training_form_state()
    st.session_state["_last_daily_record_tab"] = current_tab
    return entered_training


def _render_training_records() -> None:
    uid = st.session_state.user_id
    _render_record_success("訓練")
    today = auth.today_date()
    today_training = sheets.get_training_by_date(uid, today)
    if today_training:
        st.info("今日已有訓練紀錄，再次儲存將覆蓋原紀錄。")
    selected_types = st.pills(
        "訓練類型 (可複選)",
        TRAINING_TYPES,
        selection_mode="multi",
        default=[],
        key="training_types",
        width="stretch",
    ) or []

    with st.form("training_form"):
        st.caption(f'{today.strftime("%Y/%m/%d")} 訓練內容')
        details = {field: "" for field in sheets.TRAINING_TYPE_FIELDS.values()}
        for training_type, field, label in _training_fields_for_types(selected_types):
            details[field] = st.text_input(
                label,
                value="",
                key=f"training_{field}",
            )
        submitted = st.form_submit_button("儲存訓練紀錄", width="stretch")
    if submitted:
        try:
            application.update_student_training(
                current_auth_context(),
                timestamp=today.isoformat(),
                user_id=uid,
                training_types=selected_types,
                **details,
            )
        except ValueError as exc:
            st.warning(str(exc))
        except Exception:
            st.error("訓練紀錄儲存失敗，請稍後再試。")
        else:
            _set_record_success("訓練")
            st.rerun()


def _render_weight_records() -> None:
    st.subheader("體重")
    uid = st.session_state.user_id
    _render_record_success("體重")
    form_version = int(st.session_state.get("weight_form_version", 0))
    with st.form(f"weight_form_{form_version}"):
        weight = st.number_input(
            "今日體重 (kg)", value=None, step=0.1,
            min_value=30.0, max_value=300.0,
            key=f"weight_kg_{form_version}",
        )
        submitted = st.form_submit_button("儲存體重紀錄", width="stretch")
    if submitted:
        try:
            application.append_student_weight(
                current_auth_context(), uid,
                timestamp=auth.now_iso(), weight_kg=weight or 0,
            )
        except ValueError as exc:
            st.warning(str(exc))
        except Exception:
            st.error("體重紀錄儲存失敗，請稍後再試。")
        else:
            _clear_analysis_cache()
            st.session_state.weight_form_version = form_version + 1
            _set_record_success("體重")
            st.rerun()


def _weight_history_summary(
    points: list[WeightHistoryPoint],
) -> tuple[float, float, int] | None:
    valid_points = [point for point in points if point.weight_kg is not None]
    if not valid_points:
        return None
    current = float(valid_points[-1].weight_kg)
    change = current - float(valid_points[0].weight_kg)
    measured_count = sum(point.measured for point in points)
    return current, change, measured_count


def build_weight_history_card_header_html(
    points: list[WeightHistoryPoint],
) -> str:
    summary = _weight_history_summary(points)
    if summary is None:
        return ""
    current, change, _ = summary
    if change > 0.05:
        change_text = f"↑ +{change:.1f} kg"
        change_class = "is-up"
    elif change < -0.05:
        change_text = f"↓ {change:.1f} kg"
        change_class = "is-down"
    else:
        change_text = "0.0 kg"
        change_class = "is-flat"
    return (
        '<div class="weight-history-card-heading" aria-label="體重期間摘要">'
        f'<strong>{current:.1f} <span>kg</span></strong>'
        f'<span class="weight-history-change {change_class}">'
        f"{change_text}</span></div>"
    )


def _weight_history_tick_values(
    x_values: list[date], day_count: int
) -> list[date]:
    if not x_values:
        return []
    desired_count = 4 if day_count <= 7 else 5
    if len(x_values) <= desired_count:
        return x_values
    last_index = len(x_values) - 1
    indexes = {
        round(index * last_index / (desired_count - 1))
        for index in range(desired_count)
    }
    return [x_values[index] for index in sorted(indexes)]


def build_weight_history_figure(
    points: list[WeightHistoryPoint], day_count: int
) -> go.Figure:
    x_values = [point.day for point in points]
    y_values = [point.weight_kg for point in points]
    point_labels = [
        f"{point.weight_kg:.1f}" if point.weight_kg is not None else ""
        for point in points
    ]
    hover_status = [
        (
            "實際紀錄"
            if point.measured
            else (
                f"沿用自 {point.source_date:%m/%d}"
                if point.source_date
                else "尚無紀錄"
            )
        )
        for point in points
    ]
    measured_points = [
        point
        for point in points
        if point.measured and point.weight_kg is not None
    ]

    weights = [float(value) for value in y_values if value is not None]
    y_range = None
    if weights:
        low, high = min(weights), max(weights)
        spread = high - low
        if spread == 0:
            y_range = [low - 0.5, high + 0.5]
        else:
            visible_span = max(spread * 1.3, 0.6)
            padding = (visible_span - spread) / 2
            y_range = [low - padding, high + padding]

    fill_gradient: dict[str, object] = {
        "type": "vertical",
        "colorscale": [
            [0.0, "rgba(168,213,194,0.00)"],
            [0.55, "rgba(168,213,194,0.22)"],
            [1.0, "rgba(168,213,194,0.72)"],
        ],
    }
    if y_range is not None:
        fill_gradient.update(start=y_range[0], stop=y_range[1])

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers+text",
            line={
                "color": HISTORY_PRIMARY,
                "width": 3,
                "shape": "spline",
                "smoothing": 1.05,
            },
            fill="tozeroy",
            fillgradient=fill_gradient,
            marker={"size": 5, "color": HISTORY_PRIMARY},
            text=point_labels,
            textposition="top center",
            textfont={"size": 9, "color": HISTORY_PRIMARY_DARK},
            cliponaxis=False,
            customdata=hover_status,
            connectgaps=False,
            hovertemplate=(
                "%{x|%m/%d}<br>%{y:.1f} kg<br>%{customdata}<extra></extra>"
            ),
            name="體重",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[point.day for point in measured_points],
            y=[point.weight_kg for point in measured_points],
            mode="markers",
            marker={
                "size": 7,
                "color": HISTORY_PRIMARY,
                "line": {"color": "#ffffff", "width": 1.5},
            },
            hovertemplate=(
                "%{x|%m/%d}<br>%{y:.1f} kg<br>實際紀錄<extra></extra>"
            ),
            name="實際紀錄",
        )
    )

    tick_values = _weight_history_tick_values(x_values, day_count)

    figure.update_layout(
        height=220,
        margin={"l": 18, "r": 18, "t": 22, "b": 22},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="closest",
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "tickvals": tick_values,
            "tickformat": "%m/%d",
            "tickfont": {"size": 11, "color": HISTORY_SECONDARY_TEXT},
            "range": [x_values[0], x_values[-1]] if x_values else None,
            "automargin": False,
            "fixedrange": True,
        },
        yaxis={
            "visible": False,
            "showgrid": False,
            "zeroline": False,
            "range": y_range,
            "fixedrange": True,
        },
        font={"family": "system-ui, -apple-system, sans-serif"},
    )
    return figure


def _render_student_weight_history(user_id: str) -> None:
    with st.container(key="student_weight_history"):
        selected_range = st.session_state.get("weight_history_range", "7 天")
        if selected_range not in ("7 天", "30 天"):
            selected_range = "7 天"
        day_count = 30 if selected_range == "30 天" else 7
        start_date, end_date = history_date_range(auth.today_date(), day_count)

        try:
            weight_records = sheets.get_weight_records(user_id)
        except Exception:
            st.error("取得體重紀錄失敗，請稍後再試。")
            return

        points = build_weight_history_series(
            weight_records, start_date, end_date
        )
        if _weight_history_summary(points) is None:
            st.info("目前尚無體重紀錄。")
            if st.button(
                "新增體重紀錄",
                key="history_add_weight",
                width="stretch",
            ):
                open_daily_record_tab("體重")
                st.rerun()
            return

        with st.container(key="student_weight_history_card"):
            heading_column, range_column = st.columns(
                [1.2, 1], gap="small", vertical_alignment="center"
            )
            with heading_column:
                st.markdown(
                    build_weight_history_card_header_html(points),
                    unsafe_allow_html=True,
                )
            with range_column:
                st.segmented_control(
                    "期間",
                    ("7 天", "30 天"),
                    default=selected_range,
                    key="weight_history_range",
                    required=True,
                    label_visibility="collapsed",
                    width="stretch",
                )
            st.plotly_chart(
                build_weight_history_figure(points, day_count),
                key="student_weight_history_chart",
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )


def build_training_calendar_html(
    cells: list[TrainingCalendarDay], *, view: str
) -> str:
    weekdays = "".join(
        f'<span role="columnheader">{day}</span>'
        for day in ("一", "二", "三", "四", "五", "六", "日")
    )
    day_cells: list[str] = []
    for cell in cells:
        if cell.day is None:
            day_cells.append(
                '<span class="training-calendar-day is-empty" '
                'aria-hidden="true"></span>'
            )
            continue
        status = "有訓練" if cell.has_training else "未訓練"
        label = f"{cell.day:%Y年%m月%d日}，{status}"
        completed_class = " is-complete" if cell.has_training else ""
        day_cells.append(
            f'<time class="training-calendar-day{completed_class}" '
            f'role="listitem" datetime="{cell.day.isoformat()}" '
            f'aria-label="{html.escape(label)}" title="{html.escape(label)}">'
            f"{cell.day.day}</time>"
        )
    return (
        f'<section class="training-calendar is-{html.escape(view)}" '
        'aria-label="訓練紀錄日曆">'
        f'<div class="training-calendar-weekdays" role="row">{weekdays}</div>'
        '<div class="training-calendar-grid" role="list">'
        + "".join(day_cells)
        + "</div></section>"
    )


def _training_period_label(anchor_date: date, view: str) -> str:
    start, end = training_period_bounds(anchor_date, view)
    if view == "月":
        return f"{start.year} 年 {start.month} 月"
    if start.year == end.year:
        return f"{start:%Y/%m/%d} – {end:%m/%d}"
    return f"{start:%Y/%m/%d} – {end:%Y/%m/%d}"


def _render_student_training_history(user_id: str) -> None:
    today = auth.today_date()
    selected_view = st.session_state.get("training_history_view", "週")
    if selected_view not in ("週", "月"):
        selected_view = "週"
        st.session_state["training_history_view"] = selected_view

    anchor_date = st.session_state.get("training_history_anchor", today)
    if not isinstance(anchor_date, date) or anchor_date > today:
        anchor_date = today
        st.session_state["training_history_anchor"] = anchor_date

    with st.container(key="student_training_history"):
        try:
            records = sheets.get_training_records(user_id)
        except Exception:
            st.error("取得訓練紀錄失敗，請稍後再試。")
            return

        with st.container(key="student_training_history_card"):
            selected_view = st.segmented_control(
                "顯示期間",
                ("週", "月"),
                default=selected_view,
                key="training_history_view",
                required=True,
                label_visibility="collapsed",
                width="stretch",
            )
            selected_view = selected_view or "週"
            period_start, _ = training_period_bounds(anchor_date, selected_view)
            current_start, _ = training_period_bounds(today, selected_view)

            previous_column, label_column, next_column = st.columns(
                [0.22, 1, 0.22], gap="small", vertical_alignment="center"
            )
            with previous_column:
                if st.button(
                    ":material/chevron_left:",
                    key="training_history_previous",
                    help="上一個期間",
                    width="stretch",
                ):
                    st.session_state["training_history_anchor"] = (
                        shift_training_period(
                            anchor_date,
                            view=selected_view,
                            direction=-1,
                            today=today,
                        )
                    )
                    st.rerun()
            with label_column:
                st.markdown(
                    '<div class="training-calendar-period">'
                    f"{html.escape(_training_period_label(anchor_date, selected_view))}"
                    "</div>",
                    unsafe_allow_html=True,
                )
            with next_column:
                if st.button(
                    ":material/chevron_right:",
                    key="training_history_next",
                    help="下一個期間",
                    disabled=period_start >= current_start,
                    width="stretch",
                ):
                    st.session_state["training_history_anchor"] = (
                        shift_training_period(
                            anchor_date,
                            view=selected_view,
                            direction=1,
                            today=today,
                        )
                    )
                    st.rerun()

            cells = build_training_calendar(
                records,
                anchor_date=anchor_date,
                view=selected_view,
                today=today,
            )
            st.markdown(
                build_training_calendar_html(cells, view=selected_view),
                unsafe_allow_html=True,
            )


def build_nutrition_history_summary_html(
    points: list[NutritionHistoryPoint],
) -> str:
    averages = nutrition_history_averages(points)
    if averages is None:
        return ""
    calories, protein, _ = averages
    return (
        '<section class="nutrition-history-summary" '
        'aria-label="期間每日平均攝取">'
        '<div class="is-calories"><span>平均熱量</span>'
        f'<strong>{calories:.0f}</strong><small>kcal／日</small></div>'
        '<div class="is-protein"><span>平均蛋白質</span>'
        f'<strong>{protein:.1f}</strong><small>g／日</small></div>'
        "</section>"
    )


def build_nutrition_history_figure(
    points: list[NutritionHistoryPoint], day_count: int
) -> go.Figure:
    x_values = [point.day for point in points]
    calorie_values = [point.calories for point in points]
    protein_values = [point.protein for point in points]
    seven_day_view = day_count <= 7
    tick_values = (
        x_values
        if seven_day_view
        else _weight_history_tick_values(x_values, day_count)
    )
    tick_text = (
        [("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[day.weekday()]
         for day in tick_values]
        if seven_day_view
        else None
    )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=calorie_values,
            mode="lines+markers",
            line={
                "color": HISTORY_PRIMARY,
                "width": 3,
                "shape": "spline",
                "smoothing": 1.0,
            },
            marker={
                "size": 6,
                "color": HISTORY_PRIMARY,
                "line": {"color": "#ffffff", "width": 1.2},
            },
            connectgaps=False,
            hovertemplate="熱量 %{y:.0f} kcal<extra></extra>",
            name="熱量",
            yaxis="y",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=protein_values,
            mode="lines+markers",
            line={
                "color": HISTORY_ACCENT,
                "width": 3,
                "shape": "spline",
                "smoothing": 1.0,
            },
            marker={
                "size": 6,
                "color": HISTORY_ACCENT,
                "line": {"color": "#ffffff", "width": 1.2},
            },
            connectgaps=False,
            hovertemplate="蛋白質 %{y:.1f} g<extra></extra>",
            name="蛋白質",
            yaxis="y2",
        )
    )
    figure.update_layout(
        height=250,
        margin={"l": 28, "r": 28, "t": 10, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "tickvals": tick_values,
            "ticktext": tick_text,
            "tickformat": "%m/%d",
            "tickfont": {"size": 11, "color": HISTORY_SECONDARY_TEXT},
            "fixedrange": True,
        },
        yaxis={
            "tickfont": {"size": 10, "color": HISTORY_PRIMARY_DARK},
            "ticklabelposition": "inside",
            "showgrid": False,
            "zeroline": False,
            "rangemode": "tozero",
            "automargin": False,
            "fixedrange": True,
        },
        yaxis2={
            "tickfont": {"size": 10, "color": HISTORY_ACCENT_DARK},
            "ticklabelposition": "inside",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "zeroline": False,
            "rangemode": "tozero",
            "automargin": False,
            "fixedrange": True,
        },
        font={"family": "system-ui, -apple-system, sans-serif"},
    )
    return figure


def _render_student_nutrition_history(user_id: str) -> None:
    with st.container(key="student_nutrition_history"):
        selected_range = st.session_state.get(
            "nutrition_history_range", "7 天"
        )
        if selected_range not in ("7 天", "30 天"):
            selected_range = "7 天"
        day_count = 30 if selected_range == "30 天" else 7
        today = auth.today_date()
        start_date, end_date = history_date_range(today, day_count)

        try:
            records = _fetch_records_cached(user_id)
        except Exception:
            st.error("取得飲食紀錄失敗，請稍後再試。")
            return

        points = build_nutrition_history_series(
            records,
            start_date,
            end_date,
            today=today,
        )
        with st.container(key="student_nutrition_history_card"):
            st.segmented_control(
                "期間",
                ("7 天", "30 天"),
                default=selected_range,
                key="nutrition_history_range",
                required=True,
                label_visibility="collapsed",
                width="stretch",
            )
            if nutrition_history_averages(points) is None:
                st.info("所選期間尚無飲食紀錄。")
                return
            st.markdown(
                build_nutrition_history_summary_html(points),
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                build_nutrition_history_figure(points, day_count),
                key="student_nutrition_history_chart",
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )


def build_water_history_summary_html(points: list[WaterHistoryPoint]) -> str:
    average = water_history_average(points)
    if average is None:
        return ""
    average_ml, _ = average
    return (
        '<section class="water-history-summary" '
        'aria-label="期間每日平均飲水量">'
        '<span>平均飲水量</span>'
        f'<div><strong>{average_ml:.0f}</strong><small>ml／日</small></div>'
        "</section>"
    )


def build_water_history_figure(
    points: list[WaterHistoryPoint], day_count: int
) -> go.Figure:
    x_values = [point.day for point in points]
    water_values = [point.water_ml for point in points]
    seven_day_view = day_count <= 7
    tick_values = (
        x_values
        if seven_day_view
        else _weight_history_tick_values(x_values, day_count)
    )
    tick_text = (
        [("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[day.weekday()]
         for day in tick_values]
        if seven_day_view
        else None
    )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=water_values,
            mode="lines+markers",
            line={
                "color": WATER_HISTORY_PRIMARY,
                "width": 3,
                "shape": "spline",
                "smoothing": 1.0,
            },
            marker={
                "size": 6,
                "color": WATER_HISTORY_PRIMARY,
                "line": {"color": "#ffffff", "width": 1.2},
            },
            fill="tozeroy",
            fillgradient={
                "type": "vertical",
                "colorscale": [
                    [0.0, "rgba(215,230,245,0.00)"],
                    [1.0, "rgba(215,230,245,0.72)"],
                ],
            },
            connectgaps=False,
            hovertemplate="飲水量 %{y:.0f} ml<extra></extra>",
            name="飲水量",
        )
    )
    figure.update_layout(
        height=250,
        margin={"l": 28, "r": 28, "t": 10, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "tickvals": tick_values,
            "ticktext": tick_text,
            "tickformat": "%m/%d",
            "tickfont": {"size": 11, "color": WATER_HISTORY_SECONDARY},
            "fixedrange": True,
        },
        yaxis={
            "tickfont": {"size": 10, "color": WATER_HISTORY_SECONDARY},
            "ticklabelposition": "inside",
            "showgrid": False,
            "zeroline": False,
            "rangemode": "tozero",
            "automargin": False,
            "fixedrange": True,
        },
        font={"family": "system-ui, -apple-system, sans-serif"},
    )
    return figure


def _render_student_water_history(user_id: str) -> None:
    with st.container(key="student_water_history"):
        selected_range = st.session_state.get("water_history_range", "7 天")
        if selected_range not in ("7 天", "30 天"):
            selected_range = "7 天"
        day_count = 30 if selected_range == "30 天" else 7
        today = auth.today_date()
        start_date, end_date = history_date_range(today, day_count)

        try:
            records = _fetch_records_cached(user_id)
        except Exception:
            st.error("取得飲水紀錄失敗，請稍後再試。")
            return

        points = build_water_history_series(
            records,
            start_date,
            end_date,
            today=today,
        )
        with st.container(key="student_water_history_card"):
            st.segmented_control(
                "期間",
                ("7 天", "30 天"),
                default=selected_range,
                key="water_history_range",
                required=True,
                label_visibility="collapsed",
                width="stretch",
            )
            if water_history_average(points) is None:
                st.info("所選期間尚無飲水紀錄。")
                return
            st.markdown(
                build_water_history_summary_html(points),
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                build_water_history_figure(points, day_count),
                key="student_water_history_chart",
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )


def page_log_meal() -> None:
    """學員日常紀錄入口，只渲染目前開啟的分段。"""
    target_tab = st.session_state.pop(DAILY_RECORD_TAB_TARGET_KEY, None)
    target_tab = LEGACY_DAILY_RECORD_TABS.get(target_tab, target_tab)
    stored_tab = st.session_state.get("daily_record_tab", DAILY_RECORD_TABS[0])
    stored_tab = LEGACY_DAILY_RECORD_TABS.get(stored_tab, stored_tab)
    current_tab = target_tab or stored_tab
    if current_tab not in DAILY_RECORD_TABS:
        current_tab = DAILY_RECORD_TABS[0]
    if target_tab:
        st.session_state.pop("daily_record_tab", None)

    _prepare_daily_record_tab(current_tab)

    with st.container(key="daily_record_page"):
        st.header("日常紀錄")
        food_tab, water_tab, training_tab, weight_tab = st.tabs(
            DAILY_RECORD_TABS, default=current_tab,
            key="daily_record_tab", on_change="rerun",
        )
        if food_tab.open:
            with food_tab:
                _render_food_records()
        elif water_tab.open:
            with water_tab:
                _render_water_records()
        elif training_tab.open:
            with training_tab:
                _render_training_records()
        elif weight_tab.open:
            with weight_tab:
                _render_weight_records()

# =============================================================================


# 學員端：歷史記錄

# =============================================================================

def page_history() -> None:
    with st.container(key="student_history_page"):
        st.header("歷史紀錄")

        uid = st.session_state.user_id
        history_tab, edit_tab = st.tabs(
            ("歷史紀錄", "修改紀錄"),
            default="歷史紀錄",
            key="student_history_tabs",
            on_change="rerun",
        )
        if history_tab.open:
            with history_tab:
                _render_student_weight_history(uid)
                _render_student_nutrition_history(uid)
                _render_student_water_history(uid)
                _render_student_training_history(uid)
        elif edit_tab.open:
            with edit_tab:
                try:
                    render_daily_record_manager(uid, _clear_analysis_cache)
                except Exception:
                    st.error("取得每日紀錄失敗，請稍後再試。")

# =============================================================================

# 學員端：TDEE 頁面

# =============================================================================

def page_tdee() -> None:

    st.header("🧮 TDEE 計算機")

    uid = st.session_state.user_id

    goals = sheets.get_user_goals(uid)

    bmr = goals.get("bmr", 0)

    calorie_goal = goals.get("calorie", 0)

    if bmr > 0:

        col1, col2 = st.columns(2)

        with col1:

            st.metric("基礎代謝率 (BMR)", f"{bmr:.0f} 大卡")

        with col2:

            st.metric("每日建議攝取", f"{calorie_goal:.0f} 大卡")

        st.info("以上為你目前設定的目標，可由教練調整")

    else:

        st.warning("你尚未設定營養目標")

        if st.button("前往 TDEE 問卷"):

            st.session_state.page = "TDEE 問卷"

            st.rerun()

# =============================================================================

# 主程式

# =============================================================================
