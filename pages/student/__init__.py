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

    welcome_html = f'<div style="display: flex; align-items: center; gap: 16px; margin-top: 10px; margin-bottom: 25px; width: 100%;"><img src="{avatar_base64}" style="width: 56px; height: 56px; border-radius: 50%; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.05);" alt="avatar"><span style="font-size: 24px; font-weight: 700; color: #1a1a1a; font-family: system-ui, -apple-system, sans-serif; white-space: nowrap;">Hello, {user_name}!</span></div>'

    st.markdown(welcome_html, unsafe_allow_html=True)

    st.header("📊 今日摘要")

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

    st.subheader("今日建議")

    col1, col2 = st.columns(2)

    with col1:

        st.metric("基礎代謝率 (BMR)", f"{bmr:.0f} 大卡")

    with col2:

        st.metric("建議熱量攝取", f"{calorie_goal:.0f} 大卡")


    st.divider()

    st.subheader("營養攝取")

    record_mode = sheets.get_user_record_mode(uid)

    if record_mode == "full":

        col1, col2, col3 = st.columns(3)

        with col1:
            # CSS for calories chart
            st.markdown("""
<style>
    .cal-chart-full div[data-testid="stPlotlyChart"] {
        border-radius: 24px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04) !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

            # Calculate calorie percentage
            cal_pct = min(totals.get("calories", 0) / calorie_goal * 100, 100) if calorie_goal > 0 else 0

            FONT_SETTING = dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
            CAL_CARD_BG = "#ffffff"

            fig_cal = go.Figure()
            fig_cal.add_trace(go.Pie(
                values=[cal_pct, 100 - cal_pct],
                hole=0.76,
                domain=dict(x=[0, 1], y=[0, 1]),
                marker=dict(colors=['#ffbfa3', '#f0f0f0']),
                sort=False,
                direction='clockwise',
                showlegend=False,
                hoverinfo='none',
                textinfo='none'
            ))
            fig_cal.update_layout(
                paper_bgcolor=CAL_CARD_BG,
                plot_bgcolor=CAL_CARD_BG,
                margin=dict(l=10, r=10, t=50, b=10),
                height=180,
                font=FONT_SETTING,
                annotations=[
                    dict(
                        x=0.02, y=1.22, xref="paper", yref="paper",
                        text="<span style='font-size:15px; color:#1a1a1a; font-weight:600; font-family: sans-serif;'>Calories</span>",
                        showarrow=False, align="left"
                    ),
                    dict(
                        x=0.5, y=0.5, xref="paper", yref="paper",
                        text=f"<b style='font-size:28px; color:#1a1a1a;'>{totals.get('calories', 0):.0f}</b>",
                        showarrow=False, align="center"
                    ),
                    dict(
                        x=0.5, y=0.22, xref="paper", yref="paper",
                        text="<span style='font-size:12px; color:#666666; font-weight:500;'>Kcal</span>",
                        showarrow=False, align="center"
                    )
                ]
            )
            st.plotly_chart(fig_cal, width="stretch", config={'displayModeBar': False})

        with col2:

            carb = totals.get("carb", 0)

            st.metric("碳水", f"{carb:.0f}g", f"{goals.get('carb', 0) - carb:.0f}g")

        with col3:

            fat = totals.get("fat", 0)

            st.metric("脂肪", f"{fat:.0f}g", f"{goals.get('fat', 0) - fat:.0f}g")

    else:

        col1, col2, col3 = st.columns(3)

        with col1:
            # CSS for calories chart
            st.markdown("""
<style>
    .cal-chart-simple div[data-testid="stPlotlyChart"] {
        border-radius: 24px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04) !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

            # Calculate calorie percentage
            cal_pct = min(totals.get("calories", 0) / calorie_goal * 100, 100) if calorie_goal > 0 else 0

            FONT_SETTING = dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
            CAL_CARD_BG = "#ffffff"

            fig_cal = go.Figure()
            fig_cal.add_trace(go.Pie(
                values=[cal_pct, 100 - cal_pct],
                hole=0.76,
                domain=dict(x=[0, 1], y=[0, 1]),
                marker=dict(colors=['#ffbfa3', '#f0f0f0']),
                sort=False,
                direction='clockwise',
                showlegend=False,
                hoverinfo='none',
                textinfo='none'
            ))
            fig_cal.update_layout(
                paper_bgcolor=CAL_CARD_BG,
                plot_bgcolor=CAL_CARD_BG,
                margin=dict(l=10, r=10, t=50, b=10),
                height=180,
                font=FONT_SETTING,
                annotations=[
                    dict(
                        x=0.02, y=1.22, xref="paper", yref="paper",
                        text="<span style='font-size:15px; color:#1a1a1a; font-weight:600; font-family: sans-serif;'>Calories</span>",
                        showarrow=False, align="left"
                    ),
                    dict(
                        x=0.5, y=0.5, xref="paper", yref="paper",
                        text=f"<b style='font-size:28px; color:#1a1a1a;'>{totals.get('calories', 0):.0f}</b>",
                        showarrow=False, align="center"
                    ),
                    dict(
                        x=0.5, y=0.22, xref="paper", yref="paper",
                        text="<span style='font-size:12px; color:#666666; font-weight:500;'>Kcal</span>",
                        showarrow=False, align="center"
                    )
                ]
            )
            st.plotly_chart(fig_cal, width="stretch", config={'displayModeBar': False})

    st.divider()

    # CSS for pie charts
    st.markdown("""
<style>
    div[data-testid="stPlotlyChart"] {
        border-radius: 24px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 24px rgba(199, 237, 246, 0.3) !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

    st.subheader("今日目標進度")

    # 定義比由變参
    cal_ratio = min(totals.get("calories", 0) / calorie_goal, 1.5) if calorie_goal > 0 else 0
    pro_ratio = min(totals.get("protein", 0) / goals.get("protein", 1), 1.5) if goals.get("protein", 0) > 0 else 0
    water_ratio = min(totals.get("water", 0) / goals.get("water", 1), 1.5) if goals.get("water", 0) > 0 else 0

    # 建立三欄，將 食飼、水量、蛋質膜質 橫向並排
    cal_pct = min(cal_ratio * 100, 100)
    water_pct = min(water_ratio * 100, 100)
    pro_pct = min(pro_ratio * 100, 100)

    # 取得今日日期字串
    today_str = date.today().strftime("%d %B")

    # 定義统一的卡粉色胊背景背能
    CARD_BG_COLOR = "#c7edf6"

    # ?????? ????????? ????
    col1, col2, col3 = st.columns(3)

    # ?????? ????????? ????
    with col1:
        fig_cal = go.Figure()
        fig_cal.add_trace(go.Pie(
            values=[cal_pct, 100 - cal_pct],
            hole=0.75,
            marker=dict(colors=['#ffffff', 'rgba(255, 255, 255, 0.3)']),
            sort=False,
            direction='clockwise',
            showlegend=False,
            hoverinfo='none',
            textinfo='none'
        ))
        fig_cal.update_layout(
            paper_bgcolor=CARD_BG_COLOR,
            plot_bgcolor=CARD_BG_COLOR,
            margin=dict(l=20, r=20, t=20, b=20),
            height=160,
            annotations=[
                dict(
                    x=0.75, y=0.5, xref="paper", yref="paper",
                    text=f"<b style='font-size:20px; color:#1a2530;'>{totals.get('calories', 0):.0f}</b><br><span style='font-size:10px; color:#5a6e7f;'>kcal</span>",
                    showarrow=False, align="center"
                ),
                dict(
                    x=0.05, y=0.90, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#5a6e7f; font-weight:600;'>飲食進度</span>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.50, xref="paper", yref="paper",
                    text=f"<b style='font-size:36px; color:#1a2530;'>{cal_pct:.0f}%</b>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.10, xref="paper", yref="paper",
                    text=f"<span style='font-size:11px; color:#5a6e7f;'>{today_str}</span>",
                    showarrow=False, align="left"
                )
            ]
        )
        st.plotly_chart(fig_cal, width="stretch", config={'displayModeBar': False})

    #
    with col2:
        fig_water = go.Figure()
        fig_water.add_trace(go.Pie(
            values=[water_pct, 100 - water_pct],
            hole=0.75,
            marker=dict(colors=['#ffffff', 'rgba(255, 255, 255, 0.3)']),
            sort=False,
            direction='clockwise',
            showlegend=False,
            hoverinfo='none',
            textinfo='none'
        ))
        fig_water.update_layout(
            paper_bgcolor=CARD_BG_COLOR,
            plot_bgcolor=CARD_BG_COLOR,
            margin=dict(l=20, r=20, t=20, b=20),
            height=160,
            annotations=[
                dict(
                    x=0.75, y=0.5, xref="paper", yref="paper",
                    text=f"<b style='font-size:18px; color:#1a2530;'>{totals.get('water', 0):.0f}</b><br><span style='font-size:10px; color:#5a6e7f;'>ml</span>",
                    showarrow=False, align="center"
                ),
                dict(
                    x=0.05, y=0.90, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#5a6e7f; font-weight:600;'>水量進度</span>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.50, xref="paper", yref="paper",
                    text=f"<b style='font-size:36px; color:#1a2530;'>{water_pct:.0f}%</b>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.10, xref="paper", yref="paper",
                    text=f"<span style='font-size:11px; color:#5a6e7f;'>{today_str}</span>",
                    showarrow=False, align="left"
                )
            ]
        )
        st.plotly_chart(fig_water, width="stretch", config={'displayModeBar': False})

    # 水量圓環卡區
    with col3:
        fig_pro = go.Figure()
        fig_pro.add_trace(go.Pie(
            values=[pro_pct, 100 - pro_pct],
            hole=0.75,
            marker=dict(colors=['#ffffff', 'rgba(255, 255, 255, 0.3)']),
            sort=False,
            direction='clockwise',
            showlegend=False,
            hoverinfo='none',
            textinfo='none'
        ))
        fig_pro.update_layout(
            paper_bgcolor=CARD_BG_COLOR,
            plot_bgcolor=CARD_BG_COLOR,
            margin=dict(l=20, r=20, t=20, b=20),
            height=160,
            annotations=[
                dict(
                    x=0.75, y=0.5, xref="paper", yref="paper",
                    text=f"<b style='font-size:20px; color:#1a2530;'>{totals.get('protein', 0):.0f}</b><br><span style='font-size:10px; color:#5a6e7f;'>g</span>",
                    showarrow=False, align="center"
                ),
                dict(
                    x=0.05, y=0.90, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#5a6e7f; font-weight:600;'>蛋白質進度</span>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.50, xref="paper", yref="paper",
                    text=f"<b style='font-size:36px; color:#1a2530;'>{pro_pct:.0f}%</b>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.10, xref="paper", yref="paper",
                    text=f"<span style='font-size:11px; color:#5a6e7f;'>{today_str}</span>",
                    showarrow=False, align="left"
                )
            ]
        )
        st.plotly_chart(fig_pro, width="stretch", config={'displayModeBar': False})

    st.divider()

    # ============================================================
    st.subheader("⚖️ 體重")

    # 注入精確定位與排版的 CSS
    st.markdown("""
    <style>
        .weight-card-container {
            position: relative !important;
            width: 100% !important;
            margin-bottom: 20px !important;
        }

        .weight-card {
            background-color: #f8f8f8 !important;
            border-radius: 24px !important;
            padding: 24px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03) !important;
            box-sizing: border-box !important;
        }

        .weight-title {
            font-size: 16px !important;
            font-weight: 500 !important;
            color: #1a1a1a !important;
            margin-bottom: 12px !important;
            font-family: system-ui, -apple-system, sans-serif !important;
        }

        .weight-value {
            font-size: 36px !important;
            font-weight: 700 !important;
            color: #1a1a1a !important;
            font-family: system-ui, -apple-system, sans-serif !important;
            line-height: 1 !important;
        }

        .weight-unit {
            font-size: 18px !important;
            font-weight: normal !important;
            color: #a0a0a0 !important;
            margin-left: 6px !important;
        }

        .weight-trend {
            font-size: 14px !important;
            color: #1a1a1a !important;
            font-weight: 500 !important;
            margin-top: 12px !important;
            display: flex !important;
            align-items: center !important;
            font-family: system-ui, -apple-system, sans-serif !important;
        }

        .stApp div[data-testid="element-container"]:has(button[key="weight_lightning_btn"]) {
            position: absolute !important;
            top: 24px !important;
            right: 24px !important;
            width: 44px !important;
            height: 44px !important;
            z-index: 999 !important;
        }

        .stApp button[key="weight_lightning_btn"] {
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            border-radius: 50% !important;
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
            font-size: 18px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }

        .stApp button[key="weight_lightning_btn"]:hover {
            transform: scale(1.08) !important;
            background-color: #f3f3f3 !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.1) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    latest_weight = sheets.get_latest_weight(uid)
    weight_display_str = f"{latest_weight:.1f}" if latest_weight else "--.-"

    # 歷史紀錄與變動計算
    weight_history = []
    if "records" in dir() and records:
        for r in records:
            w = r.get("weight") if isinstance(r, dict) else getattr(r, "weight", None)
            if w is not None:
                try:
                    w_val = float(w)
                    if w_val > 0:
                        weight_history.append(w_val)
                except (ValueError, TypeError):
                    continue

    # 計算趨勢
    trend_content = ""
    if latest_weight and len(weight_history) >= 2:
        prev_weight = weight_history[-2]
        diff = latest_weight - prev_weight
        diff_pct = (diff / prev_weight) * 100

        if diff < 0:
            trend_content = f"⇩ {abs(diff):.1f} Kg ({diff_pct:.1f}%)"
        elif diff > 0:
            trend_content = f"⇧ {abs(diff):.1f} Kg (+{diff_pct:.1f}%)"
        else:
            trend_content = "⬌ 體重維持持平"
    else:
        trend_content = ""

    st.markdown('<div class="weight-card-container">', unsafe_allow_html=True)

    card_html = f"""
    <div class="weight-card">
        <div class="weight-title">Current Weight</div>
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

    st.markdown(card_html, unsafe_allow_html=True)

    if st.button("⚡", key="weight_lightning_btn"):
        open_daily_record_tab("⚖️ 體重")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.write("<div style='height: 40px;'></div>", unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)




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
