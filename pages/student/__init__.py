"""學員端、登入與註冊頁面。"""
from __future__ import annotations
from datetime import date, datetime, timedelta
import hashlib
from io import BytesIO
import math
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from services import auth, gemini, metrics, sheets
from domain.nutrition import EXERCISE_LEVELS, calculate_bmr, calculate_goals, calculate_tdee
from pages.common import (
    DEFAULT_GOALS, TRAINING_TYPES, _clear_analysis_cache, _fetch_goals_cached,
    _fetch_records_cached, _today_range, _week_range, do_logout,
)

DAILY_RECORD_TABS = ("食物", "飲水", "訓練", "體重")
DAILY_RECORD_TAB_TARGET_KEY = "daily_record_tab_target"
LEGACY_DAILY_RECORD_TABS = {
    "🍴 飲食": "食物",
    "⚖️ 體重": "體重",
    "🏋️ 訓練": "訓練",
}


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
    tab = LEGACY_DAILY_RECORD_TABS.get(tab, tab)
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
    with st.container(key="auth_brand"):
        st.markdown(
            """
            <div class="auth-brand-lockup">
                <h1 class="auth-brand-title">
                    <span class="auth-brand-english">PROJECT PRIME</span>
                    <span class="auth-brand-divider">|</span>
                    <span class="auth-brand-chinese">巔峰計畫</span>
                </h1>
                <p class="auth-brand-tagline">
                    <span>吃對、練對持續做。</span>
                    <span>剩下交給時間，進化沒有捷徑，</span>
                    <span>但每一步都算數，把自己推向人生最好的狀態</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
                open_daily_record_tab("體重")
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

def _append_water_record(user_id: str, water_ml: float) -> None:
    """新增一筆可累加的飲水紀錄。"""
    water_value = float(water_ml)
    if not math.isfinite(water_value) or water_value <= 0:
        raise ValueError("飲水量必須大於 0")
    sheets.append_record(
        timestamp=datetime.now().isoformat(), user_id=user_id,
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
    sheets.append_record(
        timestamp=datetime.now().isoformat(), user_id=user_id,
        meal_type="食物", food_summary=food_summary.strip() or "手動紀錄",
        calories=calorie_value, protein=protein_value,
        carb=0, fat=0, water_ml=0, image_url="", portion=1,
    )
    _clear_analysis_cache()


def _clear_pending_food_analysis() -> None:
    st.session_state.pending_analysis = None
    st.session_state.pop("pending_analysis_image_hash", None)


def _render_water_records() -> None:
    uid = st.session_state.user_id
    st.subheader("飲水")
    st.caption("記錄這次喝下的水量，今日進度會自動累加。")
    with st.form("water_record_form"):
        water_ml = st.number_input("飲水量 (ml)", min_value=0, value=250, step=50)
        submitted = st.form_submit_button("儲存飲水紀錄", width="stretch")
    if submitted:
        try:
            _append_water_record(uid, water_ml)
        except ValueError as exc:
            st.warning(str(exc))
        except Exception:
            st.error("飲水紀錄儲存失敗，請稍後再試。")
        else:
            st.success("飲水紀錄已儲存")
            st.rerun()


def _selected_food_image_bytes(source: str) -> bytes | None:
    if source == "拍照":
        image_file = st.camera_input("拍攝食物照片", key="food_camera")
    else:
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
            st.success("食物紀錄已儲存")
            st.rerun()
    if cancel_col.button("取消", key="cancel_analyzed_food", width="stretch"):
        _clear_pending_food_analysis()
        st.rerun()


def _render_manual_food_input(uid: str) -> None:
    with st.form("manual_food_form"):
        calories = st.number_input(
            "熱量 (kcal)", min_value=0.0, value=0.0, step=10.0
        )
        protein = st.number_input(
            "蛋白質 (g)", min_value=0.0, value=0.0, step=1.0
        )
        submitted = st.form_submit_button("儲存食物紀錄", width="stretch")
    if submitted:
        try:
            _append_food_record(uid, "手動紀錄", calories, protein)
        except ValueError as exc:
            st.warning(str(exc))
        except Exception:
            st.error("食物紀錄儲存失敗，請稍後再試。")
        else:
            st.success("食物紀錄已儲存")
            st.rerun()


def _render_food_records() -> None:
    uid = st.session_state.user_id
    st.subheader("食物")
    input_mode = st.segmented_control(
        "輸入方式", ("照片辨識", "手動輸入"),
        default="手動輸入", key="food_input_mode",
    )
    if input_mode == "手動輸入":
        _render_manual_food_input(uid)
    else:
        _render_photo_food_input(uid)


def _render_training_records() -> None:
    st.subheader("訓練")
    uid = st.session_state.user_id
    today = date.today()
    today_training = sheets.get_training_by_date(uid, today)
    field_keys = {
        "背": "back", "胸": "chest", "腿": "legs",
        "核心": "core", "有氧": "cardio",
    }
    with st.form("training_form"):
        st.caption(f'{today.strftime("%Y/%m/%d")} 訓練項目')
        columns = st.columns(2)
        training_values: dict[str, int] = {}
        for index, training_type in enumerate(TRAINING_TYPES):
            field_key = field_keys[training_type]
            default = today_training.get(field_key, 0) if today_training else 0
            with columns[index % 2]:
                checked = st.checkbox(training_type, value=bool(default))
            training_values[field_key] = 1 if checked else 0
        submitted = st.form_submit_button("儲存訓練紀錄", width="stretch")
    if submitted:
        try:
            sheets.update_training(
                timestamp=today.isoformat(), user_id=uid,
                training_back=training_values["back"],
                training_chest=training_values["chest"],
                training_legs=training_values["legs"],
                training_core=training_values["core"],
                training_cardio=training_values["cardio"],
            )
        except Exception:
            st.error("訓練紀錄儲存失敗，請稍後再試。")
        else:
            st.success("訓練紀錄已儲存")
            st.rerun()

    st.subheader("本週訓練紀錄")
    week_start, week_end = _week_range()
    rows = []
    labels_by_key = {value: key for key, value in field_keys.items()}
    for offset in range((week_end - week_start).days + 1):
        target_date = week_start + timedelta(days=offset)
        training = sheets.get_training_by_date(uid, target_date)
        if training and any(value == 1 for value in training.values()):
            labels = [
                labels_by_key[key] for key, value in training.items()
                if value == 1 and key in labels_by_key
            ]
            rows.append({
                "日期": target_date.strftime("%m/%d"),
                "訓練項目": "、".join(labels),
            })
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("本週尚無訓練紀錄")


def _render_weight_records() -> None:
    st.subheader("體重")
    uid = st.session_state.user_id
    with st.form("weight_form"):
        weight = st.number_input(
            "今日體重 (kg)", value=60.0, step=0.1,
            min_value=30.0, max_value=300.0,
        )
        submitted = st.form_submit_button("儲存體重紀錄", width="stretch")
    if submitted:
        try:
            sheets.append_weight(
                timestamp=datetime.now().strftime("%Y-%m-%d"),
                user_id=uid, weight_kg=weight,
            )
        except Exception:
            st.error("體重紀錄儲存失敗，請稍後再試。")
        else:
            st.success("體重紀錄已儲存")
            st.rerun()

    st.subheader("體重趨勢")
    weight_records = sheets.get_weight_records(uid)
    if not weight_records:
        st.info("尚無體重紀錄")
        return
    weight_data = {"日期": [], "體重 (kg)": []}
    for record in weight_records[-30:]:
        weight_data["日期"].append(record.get("timestamp", "")[:10])
        weight_data["體重 (kg)"].append(record.get("weight_kg", 0))
    st.line_chart(weight_data, x="日期", y="體重 (kg)")
    if len(weight_data["體重 (kg)"]) >= 2:
        weights = weight_data["體重 (kg)"]
        change = weights[-1] - weights[0]
        st.caption(
            f'起始 {weights[0]:.1f} kg；目前 {weights[-1]:.1f} kg；變化 {change:+.1f} kg'
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
