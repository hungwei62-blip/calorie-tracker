"""學員端、登入與註冊頁面。"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from io import BytesIO
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from services import auth, gemini, metrics, sheets
from domain.nutrition import EXERCISE_LEVELS, calculate_bmr, calculate_goals, calculate_tdee
from pages.common import (
    DEFAULT_GOALS, MEAL_EMOJI, MEAL_TYPES,
    TRAINING_EMOJI, TRAINING_TYPES, _clear_analysis_cache, _fetch_goals_cached,
    _fetch_records_cached, _today_range, _week_range, do_logout,
)

DAILY_RECORD_TABS = ("🍴 飲食", "⚖️ 體重", "🏋️ 訓練")
DAILY_RECORD_TAB_TARGET_KEY = "daily_record_tab_target"


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
        paper_bgcolor="#c7edf6",
        plot_bgcolor="#c7edf6",
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


def _weight_summary(weight_records: list[dict[str, object]]) -> tuple[float | None, str]:
    """從 Weight 紀錄取得最新體重與相較前一筆的趨勢文字。"""
    weights = [
        value
        for record in weight_records
        if (value := _to_float(record.get("weight_kg"))) > 0
    ]
    if not weights:
        return None, ""

    latest_weight = weights[-1]
    if len(weights) < 2:
        return latest_weight, ""

    previous_weight = weights[-2]
    difference = latest_weight - previous_weight
    difference_percentage = difference / previous_weight * 100

    if difference < 0:
        trend = f"⇩ {abs(difference):.1f} Kg ({difference_percentage:.1f}%)"
    elif difference > 0:
        trend = f"⇧ {abs(difference):.1f} Kg (+{difference_percentage:.1f}%)"
    else:
        trend = "⬌ 體重維持持平"
    return latest_weight, trend


def open_daily_record_tab(tab: str) -> None:
    """將學員導向日常紀錄頁的指定分頁。"""
    if tab not in DAILY_RECORD_TABS:
        raise ValueError("未知的日常紀錄分頁")
    st.session_state.page = "記錄飲食"
    st.session_state[DAILY_RECORD_TAB_TARGET_KEY] = tab


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

        st.subheader("飲食記錄模式")

        record_mode = st.radio(

            "選擇飲食記錄模式",

            ["簡易模式（蛋白質/熱量/水量）", "完整模式（蛋白質/碳水/脂肪/熱量/水量）"],

            horizontal=False,

        )

        mode = "simple" if "簡易" in record_mode else "full"

        submitted = st.form_submit_button("計算並儲存目標", width="stretch")

    if submitted:

        bmr = calculate_bmr(weight, height, age, gender)

        tdee = calculate_tdee(bmr, exercise_level)

        goals = calculate_goals(weight, tdee, goal_type)

        goals["bmr"] = bmr

        try:

            uid = st.session_state.user_id

            sheets.update_user_bmr(uid, bmr)

            sheets.update_user_goals(uid, goals)

            sheets.set_user_record_mode(uid, mode)

            if mode == "simple":

                sheets.update_user_goals(uid, {"carb": 0.0, "fat": 0.0})

            _clear_analysis_cache()

            st.success("目標設定完成！")

            st.balloons()

            st.session_state.page = "個人"

            st.rerun()

        except Exception as exc:

            st.error("儲存失敗: " + str(exc))

# =============================================================================

# 登入頁面

# =============================================================================


def page_login() -> None:
    st.title("飲食控制管理系統")
    st.caption("輕鬆記錄飲食，追蹤你的營養目標")

    # 確保 auth_mode 存在
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    if st.session_state.auth_mode == "login":
        # ==================== 登入表單 ====================
        with st.form("login_form"):
            username = st.text_input("帳號", key="login_user")
            password = st.text_input("密碼", type="password", key="login_pwd")
            submit = st.form_submit_button("登入", width="stretch")

        if submit:
            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error("取得使用者失敗: " + str(exc))
                return
            user = auth.find_user(rows, username)
            if not user:
                st.error("找不到此帳號")
                return
            if not auth.verify_password(password, user.get("password_hash", "")):
                st.error("密碼錯誤")
                return

            st.session_state.user_id = user.get("user_id")
            st.session_state.username = user.get("username")
            st.session_state.role = sheets.get_user_role(str(user.get("user_id") or ""))

            if st.session_state.role in ("coach", "admin"):
                st.session_state.page = "學員狀態"
            else:
                st.session_state.page = "個人"
            st.success("登入成功！")
            st.rerun()

        # 切換到註冊
        if st.button("還沒有帳號？立即註冊", key="nav_to_register"):
            st.session_state.auth_mode = "register"
            st.rerun()

    else:
        # ==================== 註冊表單 ====================
        st.subheader("建立學員帳號")
        st.info("填寫以下資料即可建立帳號")

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
                record_mode = st.radio("記錄模式", ["簡易模式", "完整模式"], horizontal=True, index=0)

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
                st.error("取得使用者失敗: " + str(exc))
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
                sheets.append_user(
                    uid, new_user, new_name, pwd_hash, auth.now_iso(),
                    goals=goals,
                    coach_id=primary_coach_id,
                    record_mode="simple" if "簡易" in record_mode else "full",
                    weekly_training=4,
                )

                st.session_state.user_id = uid
                st.session_state.username = new_user
                st.session_state.role = "student"
                st.session_state.needs_tdee_setup = True
                st.success("註冊成功！請先填寫 TDEE 問卷完成設定")
                st.rerun()

            except Exception as exc:
                st.error("註冊失敗: " + str(exc))

        # 切換回登入
        if st.button("已經有帳號了？立即登入", key="nav_to_login"):
            st.session_state.auth_mode = "login"
            st.rerun()



def page_personal() -> None:

    # ============================================================
    # 👋 1. 個人化頭像歡迎區 (單行無縮排安全版)
    # ============================================================
    import base64
    import os

    user_name = st.session_state.get('username', '學員')
    avatar_path = './static/avatar.jpg'

    avatar_base64 = ""
    if os.path.exists(avatar_path):
        with open(avatar_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            avatar_base64 = f"data:image/jpeg;base64,{encoded_string}"
    else:
        avatar_base64 = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=200&h=200"

    welcome_html = f'<div class="student-home-welcome" style="display: flex; align-items: center; gap: 16px; margin-top: 0; margin-bottom: 25px; width: 100%;"><img src="{avatar_base64}" style="width: 56px; height: 56px; border-radius: 50%; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.05);" alt="avatar"><span style="font-size: 24px; font-weight: 700; color: #1a1a1a; font-family: system-ui, -apple-system, sans-serif; white-space: nowrap;">Hello, {user_name}!</span></div>'

    with st.container(key="student_home_header"):
        st.markdown(welcome_html, unsafe_allow_html=True)
        st.header("Overview")

    uid = st.session_state.user_id

    try:

        records = _fetch_records_cached(uid)

        goals = _fetch_goals_cached(uid)

    except Exception as exc:

        st.error("取得資料失敗: " + str(exc))

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

    latest_weight, trend_content = _weight_summary(sheets.get_weight_records(uid))
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
                open_daily_record_tab("⚖️ 體重")
                st.rerun()

        with calorie_column:
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
                st.plotly_chart(
                    build_daily_progress_figure(label, actual, goal, unit),
                    key=f"daily_progress_{key}",
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )

    st.write("<div style='height: 40px;'></div>", unsafe_allow_html=True)


# =============================================================================

# 學員端：體重記錄

# =============================================================================

def _render_weight_records() -> None:

    st.subheader("⚖️ 體重記錄")

    uid = st.session_state.user_id

    with st.form("weight_form"):

        col1, col2 = st.columns([2, 1])

        with col1:

            weight = st.number_input("今日體重 (kg)", value=60.0, step=0.1, min_value=30.0, max_value=300.0)

        with col2:

            st.write("")

            submitted = st.form_submit_button("儲存", width="stretch")

        if submitted:

            try:

                sheets.append_weight(timestamp=datetime.now().strftime("%Y-%m-%d"), user_id=uid, weight_kg=weight)

                st.success("體重已記錄！")

                st.rerun()

            except Exception as exc:

                st.error("儲存失敗: " + str(exc))

    st.divider()

    st.subheader("體重趨勢")

    weight_records = sheets.get_weight_records(uid)

    if weight_records:

        weight_data = {"日期": [], "體重 (kg)": []}

        for r in weight_records[-30:]:

            weight_data["日期"].append(r.get("timestamp", "")[:10])

            weight_data["體重 (kg)"].append(r.get("weight_kg", 0))

        st.line_chart(weight_data, x="日期", y="體重 (kg)")

        if len(weight_data["體重 (kg)"]) >= 2:

            weights = weight_data["體重 (kg)"]

            change = weights[-1] - weights[0]

            st.caption(f"起始：{weights[0]:.1f}kg → 目前：{weights[-1]:.1f}kg（{change:+.1f}kg）")

    else:

        st.info("尚無體重記錄")

# =============================================================================

# 學員端：訓練記錄

# =============================================================================

def _render_training_records() -> None:

    st.subheader("🏋️ 訓練記錄")

    uid = st.session_state.user_id

    today = date.today()

    today_str = today.isoformat()

    today_training = sheets.get_training_by_date(uid, today)

    with st.form("training_form"):

        st.subheader(f"📅 {today.strftime('%Y/%m/%d')} 訓練項目")

        cols = st.columns(len(TRAINING_TYPES))

        training_values = {}

        for idx, t_type in enumerate(TRAINING_TYPES):

            with cols[idx]:

                emoji = TRAINING_EMOJI.get(t_type, "")

                default = today_training.get(t_type.lower(), 0) if today_training else 0

                checked = st.checkbox(f"{emoji} {t_type}", value=bool(default))

                training_values[t_type.lower()] = 1 if checked else 0

        submitted = st.form_submit_button("儲存訓練記錄", width="stretch")

    if submitted:

        try:

            sheets.update_training(

                timestamp=today_str, user_id=uid,

                training_back=training_values.get("背", 0),

                training_chest=training_values.get("胸", 0),

                training_legs=training_values.get("腿", 0),

                training_core=training_values.get("核心", 0),

                training_cardio=training_values.get("有氧", 0),

            )

            st.success("訓練記錄已儲存！")

            st.rerun()

        except Exception as exc:

            st.error("儲存失敗: " + str(exc))

    st.divider()

    st.subheader("本週訓練記錄")

    ws, we = _week_range()

    training_data = []

    for i in range((we - ws).days + 1):

        d = ws + timedelta(days=i)

        training = sheets.get_training_by_date(uid, d)

        if training and any(v == 1 for v in training.values()):

            items = [TRAINING_EMOJI.get(t, "") + t for t, v in training.items() if v == 1]

            training_data.append({"日期": d.strftime("%m/%d"), "訓練項目": " ".join(items)})

    if training_data:

        st.dataframe(training_data, width="stretch", hide_index=True)

    else:

        st.info("本週尚無訓練記錄")

# =============================================================================

# 學員端：記錄飲食

# =============================================================================

def _render_meal_records() -> None:

    st.subheader("🍽️ 記錄飲食")

    uid = st.session_state.user_id

    record_mode = sheets.get_user_record_mode(uid)

    meal_type = st.selectbox("餐點類型", MEAL_TYPES)

    st.subheader("分析方式")

    input_mode = st.radio(

        "輸入模式",

        ["📝 文字輸入", "📷 拍照上傳", "📁 圖片上傳"],

        horizontal=True,

        label_visibility="collapsed",

    )

    analysis_result = None

    if input_mode == "📝 文字輸入":

        with st.form("text_input_form"):

            food_text = st.text_area("輸入食物內容", placeholder="例如：雞腿便當 + 滷蛋 + 無糖豆漿", height=100)

            submitted = st.form_submit_button("分析食物", width="stretch")

        if submitted and food_text:

            with st.spinner("AI 分析中..."):

                try:

                    analysis_result = gemini.analyze_text(food_text)

                except Exception as exc:

                    st.error("分析失敗: " + str(exc))

    elif input_mode == "📷 拍照上傳":

        camera_file = st.camera_input("拍攝食物照片")

        if camera_file:

            with st.spinner("AI 分析中..."):

                try:

                    analysis_result = gemini.analyze_image(Image.open(camera_file))

                except Exception as exc:

                    st.error("分析失敗: " + str(exc))

    else:

        uploaded_file = st.file_uploader("上傳食物照片", type=["jpg", "jpeg", "png"])

        if uploaded_file:

            with st.spinner("AI 分析中..."):

                try:

                    analysis_result = gemini.analyze_image(Image.open(uploaded_file))

                except Exception as exc:

                    st.error("分析失敗: " + str(exc))

    # 將 analysis_result 存入 session_state，確保按鈕點擊後還能取用
    if analysis_result:
        st.session_state.pending_analysis = analysis_result

    if st.session_state.get("pending_analysis"):
        analysis_result = st.session_state.pending_analysis

        st.divider()

        st.subheader("分析結果")

        cal = analysis_result.get("calories", 0)

        pro = analysis_result.get("protein", 0)

        carb = analysis_result.get("carb", 0)

        fat = analysis_result.get("fat", 0)

        if record_mode == "full":

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric("熱量", f"{cal:.0f} kcal")

            with col2:

                st.metric("蛋白質", f"{pro:.0f} g")

            with col3:

                st.metric("碳水", f"{carb:.0f} g")

            with col4:

                st.metric("脂肪", f"{fat:.0f} g")

        else:

            col1, col2 = st.columns(2)

            with col1:

                st.metric("熱量", f"{cal:.0f} kcal")

            with col2:

                st.metric("蛋白質", f"{pro:.0f} g")

        portion = st.slider("份量", 0.5, 3.0, 1.0, 0.1)

        if portion != 1.0:

            st.caption(f"× {portion} 份")

        water_ml = st.number_input("飲水量 (ml)", value=0, step=50, min_value=0)

        if st.button("✅ 存入今日記錄", width="stretch"):


            try:
                sheets.append_record(

                    timestamp=datetime.now().isoformat(),

                    user_id=uid,

                    meal_type=meal_type,

                    food_summary=analysis_result.get("food_summary", ""),

                    calories=cal * portion,

                    protein=pro * portion,

                    carb=carb * portion if record_mode == "full" else 0,

                    fat=fat * portion if record_mode == "full" else 0,

                    water_ml=water_ml,

                    image_url="",

                    portion=portion,

                )

                _clear_analysis_cache()

                # 清除 pending_analysis，讓錊單回到初始狀態
                st.session_state.pending_analysis = None

                # 顯示短暫的成功標記
                st.success("已存入！")

                st.rerun()

            except Exception as exc:

                st.error("儲存失敗: " + str(exc))


def page_log_meal() -> None:
    """學員日常紀錄入口，只渲染目前開啟的頁內分頁。"""
    target_tab = st.session_state.pop(DAILY_RECORD_TAB_TARGET_KEY, None)
    current_tab = target_tab or st.session_state.get("daily_record_tab", DAILY_RECORD_TABS[0])
    if current_tab not in DAILY_RECORD_TABS:
        current_tab = DAILY_RECORD_TABS[0]
    if target_tab:
        st.session_state.pop("daily_record_tab", None)

    st.header("📝 日常紀錄")
    meal_tab, weight_tab, training_tab = st.tabs(
        DAILY_RECORD_TABS,
        default=current_tab,
        key="daily_record_tab",
        on_change="rerun",
    )

    if meal_tab.open:
        with meal_tab:
            _render_meal_records()
    elif weight_tab.open:
        with weight_tab:
            _render_weight_records()
    elif training_tab.open:
        with training_tab:
            _render_training_records()

# =============================================================================

# 學員端：歷史記錄

# =============================================================================

def page_history() -> None:

    st.header("📜 歷史記錄")

    uid = st.session_state.user_id

    try:

        records = _fetch_records_cached(uid)

        goals = _fetch_goals_cached(uid)

    except Exception as exc:

        st.error("取得記錄失敗: " + str(exc))

        return

    bmr = goals.get("bmr", 0)

    calorie_goal = goals.get("calorie", 0)

    if bmr <= 0 or calorie_goal <= 0:

        st.warning("你尚未設定營養目標")

        return

    ws, we = _week_range()

    days = (we - ws).days + 1

    st.subheader("每日攝取")

    daily_data = []

    for i in range(days):

        d = ws + timedelta(days=i)

        day_recs = metrics.filter_records(records, d, d)

        day_totals = metrics.sum_totals(day_recs).as_dict()

        day_cal = float(day_totals.get("calories", 0.0))

        day_pro = float(day_totals.get("protein", 0.0))

        cal_ratio = (day_cal / calorie_goal) if calorie_goal > 0 else 0.0

        pro_ratio = (day_pro / goals.get("protein", 1)) if goals.get("protein", 0) > 0 else 0.0

        date_str = d.strftime("%m/%d")

        weekday = ["一", "二", "三", "四", "五", "六", "日"][d.weekday()]

        daily_data.append({

            "日期": f"{date_str}({weekday})",

            "熱量": f"{day_cal:.0f}",

            "熱量目標": f"{calorie_goal:.0f}",

            "熱量%": f"{cal_ratio:.0%}",

            "蛋白質": f"{day_pro:.0f}g",

            "蛋白質%": f"{pro_ratio:.0%}",

        })

    st.dataframe(daily_data, width="stretch", hide_index=True)

    st.subheader("熱量達成率")

    calorie_chart = {"日期": [], "達成率(%)": []}

    for i in range(days):

        d = ws + timedelta(days=i)

        day_recs = metrics.filter_records(records, d, d)

        day_totals = metrics.sum_totals(day_recs).as_dict()

        day_cal = float(day_totals.get("calories", 0.0))

        cal_ratio = (day_cal / calorie_goal * 100) if calorie_goal > 0 else 0.0

        calorie_chart["日期"].append(d.strftime("%m/%d"))

        calorie_chart["達成率(%)"].append(min(cal_ratio, 100))

    st.bar_chart(calorie_chart, x="日期", y="達成率(%)")

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
