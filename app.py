"""AI 智能多人熱量與飲水紀錄 Web App。

依照專案開發需求書：Streamlit + Gemini 2.5 Flash + Google Sheets + Firebase Storage。
支援 5 個餐別、AI 文字/照片分析、份數微調、今日/週進度儀表板。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO

import streamlit as st
from PIL import Image

from services import auth, firebase, gemini, metrics, sheets

MEAL_TYPES = ["早餐", "午餐", "晚餐", "小點", "飲水"]
MEAL_EMOJI = {"早餐": "", "午餐": "", "晚餐": "", "小點": "", "飲水": ""}
NUTRIENT_KEYS = ("calorie", "protein", "carb", "fat")
CACHE_TTL = 60
DEFAULT_GOALS = {"calorie": 2000.0, "protein": 60.0, "carb": 250.0, "fat": 65.0, "water": 2000.0}

# ---------- TDEE 計算常數 ----------
TDEE_MULTIPLIERS = {
    "幾乎不運動": 1.2,
    "每週運動 1-3 天": 1.375,
    "每週運動 3-5 天": 1.55,
    "每週運動 6-7 天": 1.72,
}


def _calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """計算基礎代謝率 (BMR)。"""
    if gender == "男":
        return 66 + (13.7 * weight) + (5.0 * height) - (6.8 * age)
    else:
        return 655 + (9.6 * weight) + (1.8 * height) - (4.7 * age)


def _calculate_tdee(bmr: float, exercise_level: str) -> float:
    """計算每日總熱量消耗 (TDEE)。"""
    multiplier = TDEE_MULTIPLIERS.get(exercise_level, 1.2)
    return bmr * multiplier


def _calculate_goals(weight: float, tdee: float) -> dict[str, float]:
    """計算所有營養目標。"""
    protein = weight * 2
    fat = weight * 0.8
    carb = ((tdee - 100) - (protein * 4) - (fat * 9)) / 4
    calorie = tdee - 200  # 減重目標
    water = weight * 40
    
    return {
        "bmr": 0,  # BMR 單獨更新
        "calorie": max(0, calorie),
        "protein": protein,
        "carb": max(0, carb),
        "fat": fat,
        "water": water,
    }


def init_session() -> None:
    """初始化所有 session_state key。"""
    defaults = {
        "user_id": None,
        "username": None,
        "role": None,
        "page": "個人",
        "pending_meal_type": None,
        "input_mode": None,
        "pending_analysis": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(ttl=CACHE_TTL)
def _fetch_records_cached(user_id: str) -> list:
    """帶 60 秒快取的紀錄讀取，避免 Sheets 429。"""
    return sheets.get_records(user_id=user_id)


@st.cache_data(ttl=CACHE_TTL)
def _fetch_goals_cached(user_id: str) -> dict:
    return sheets.get_user_goals(user_id)


def _clear_analysis_cache() -> None:
    """寫入新紀錄後清掉快取，下次讀取會重新抓。"""
    try:
        _fetch_records_cached.clear()
    except Exception:
        pass
    try:
        _fetch_goals_cached.clear()
    except Exception:
        pass


def _run_analysis(image_bytes, content_type, text):
    """呼叫 Gemini 分析照片或文字，回傳結構化 dict。"""
    if image_bytes is not None:
        image = Image.open(BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return gemini.analyze_image(image)
    return gemini.analyze_text(text)


def _today_range() -> tuple:
    today = date.today()
    return today, today


def _week_range() -> tuple:
    today = date.today()
    start = metrics.week_start(today)
    return start, today



def page_login() -> None:
    """登入 / 註冊頁，無登入時的入口。"""
    st.title("熱量與飲水紀錄")
    st.caption("請先登入或註冊以開始紀錄。")

    tab_login, tab_signup = st.tabs(["登入", "註冊"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("帳號", key="login_user")
            password = st.text_input("密碼", type="password", key="login_pwd")
            submit = st.form_submit_button("登入", use_container_width=True)
        if submit:
            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error("讀取使用者資料失敗: " + str(exc))
                return
            user = auth.find_user(rows, username)
            if not user:
                st.error("找不到此帳號。")
                return
            if not auth.verify_password(password, user.get("password_hash", "")):
                st.error("密碼錯誤。")
                return
            st.session_state.user_id = user.get("user_id")
            st.session_state.username = user.get("username")
            try:
                _role_value = auth.is_coach(str(user.get("user_id") or ""))
                from services import sheets as _sheets_dbg
                _raw_role = _sheets_dbg.get_user_role(str(user.get("user_id") or ""))
                st.session_state.role = _role_value
                st.session_state._dbg_raw = _raw_role
            except Exception as _e2:
                st.session_state.role = False
                st.session_state._dbg_raw = f"EXC:{_e2}"
            st.success("登入成功！")
            st.rerun()

    with tab_signup:
        with st.form("signup_form"):
            new_user = st.text_input("新帳號", key="signup_user")
            new_pwd = st.text_input("新密碼", type="password", key="signup_pwd")
            new_pwd2 = st.text_input("再次輸入密碼", type="password", key="signup_pwd2")
            submit2 = st.form_submit_button("建立帳號", use_container_width=True)
        if submit2:
            if not new_user or not new_pwd:
                st.error("帳號與密碼不可為空。")
                return
            if new_pwd != new_pwd2:
                st.error("兩次密碼不一致。")
                return
            if len(new_pwd) < 4:
                st.warning("建議密碼至少 4 個字元。")
            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error("讀取使用者資料失敗: " + str(exc))
                return
            if auth.find_user(rows, new_user):
                st.error("此帳號已被使用。")
                return
            try:
                uid = auth.make_user_id()
                pwd_hash = auth.hash_password(new_pwd)
                sheets.append_user(uid, new_user, pwd_hash, auth.now_iso(), DEFAULT_GOALS)
            except Exception as exc:
                st.error("建立帳號失敗: " + str(exc))
                return
            st.session_state.user_id = uid
            st.session_state.username = new_user
            st.session_state.role = "student"
            st.success("註冊成功並已登入！")
            st.rerun()


def page_personal() -> None:
    """個人首頁：顯示 BMR、TDEE 目標、今日達成率。"""
    st.header("個人首頁")
    uid = st.session_state.user_id
    
    try:
        records = _fetch_records_cached(uid)
        goals = _fetch_goals_cached(uid)
    except Exception as exc:
        st.error("讀取資料失敗: " + str(exc))
        return
    
    # 檢查是否已設定 TDEE
    bmr = goals.get("bmr", 0)
    calorie_goal = goals.get("calorie", 0)
    
    if bmr <= 0 or calorie_goal <= 0:
        # 尚未設定 TDEE，顯示引導訊息
        st.warning("您尚未設定個人營養目標")
        st.info("請先進行 TDEE 計算，以獲得個人化的營養建議。")
        if st.button("前往 TDEE 計算", use_container_width=True):
            st.session_state.page = "TDEE 計算"
            st.rerun()
        return
    
    st.subheader("個人基礎資料")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("基礎代謝率 (BMR)", f"{bmr:.0f} 大卡")
    with col2:
        st.metric("建議熱量攝取", f"{calorie_goal:.0f} 大卡")
    with col3:
        st.metric("飲水目標", f"{goals.get('water', 0):.0f} ml")
    
    # 第二行：蛋白質、碳水、脂肪
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("蛋白質目標", f"{goals.get('protein', 0):.0f} g")
    with col5:
        st.metric("碳水目標", f"{goals.get('carb', 0):.0f} g")
    with col6:
        st.metric("脂肪目標", f"{goals.get('fat', 0):.0f} g")
    
    # 今日達成率 - Seattle Weather 風格改造
    st.subheader("今日達成率")
    start, end = _today_range()
    today_records = metrics.filter_records(records, start, end)
    totals = metrics.sum_totals(today_records).as_dict()
    
    # 計算整體達成率（熱量為主）
    total_cal = float(totals.get("calorie", 0.0))
    total_pro = float(totals.get("protein", 0.0))
    total_carb = float(totals.get("carb", 0.0))
    total_fat = float(totals.get("fat", 0.0))
    total_water = float(totals.get("water", 0.0))
    
    cal_goal = goals.get("calorie", 0.0)
    pro_goal = goals.get("protein", 0.0)
    carb_goal = goals.get("carb", 0.0)
    fat_goal = goals.get("fat", 0.0)
    water_goal = goals.get("water", 0.0)
    
    # 整體達成率
    cal_ratio = (total_cal / cal_goal) if cal_goal > 0 else 0.0
    overall_pct = int(cal_ratio * 100)
    
    # 頂部：整體達成率總覽
    col_overview, col_progress = st.columns([1, 2])
    with col_overview:
        st.metric(
            "整體達成率",
            f"{overall_pct}%",
            delta=f"{total_cal - cal_goal:+.0f} kcal" if cal_goal > 0 else None,
        )
    with col_progress:
        st.progress(min(cal_ratio, 1.0), text=f"熱量: {total_cal:.0f} / {cal_goal:.0f} kcal")
    
    st.markdown("---")
    
    # 主體：5 個 st.metric 網格（2行：3+2）
    st.write("各項營養攝取")
    cols_row1 = st.columns(3)
    with cols_row1[0]:
        st.metric("熱量", f"{total_cal:.0f} kcal", delta=f"{total_cal - cal_goal:+.0f}")
    with cols_row1[1]:
        st.metric("蛋白質", f"{total_pro:.0f} g", delta=f"{total_pro - pro_goal:+.0f}")
    with cols_row1[2]:
        st.metric("碳水", f"{total_carb:.0f} g", delta=f"{total_carb - carb_goal:+.0f}")
    
    cols_row2 = st.columns(3)
    with cols_row2[0]:
        st.metric("脂肪", f"{total_fat:.0f} g", delta=f"{total_fat - fat_goal:+.0f}")
    with cols_row2[1]:
        st.metric("飲水", f"{total_water:.0f} ml", delta=f"{total_water - water_goal:+.0f}")
    
    # 今日記錄列表 - Seattle Weather 風格卡片化
    st.subheader("今日記錄")
    if today_records:
        # 使用 st.container 當卡片包覆每筆記錄
        for r in today_records:
            ts = r.get("timestamp", "")
            meal_type = r.get("meal_type", "")
            summary = r.get("food_summary", "")
            cal = r.get("calories", 0)
            pro = r.get("protein", 0)
            carb = r.get("carb", 0)
            fat = r.get("fat", 0)
            water = r.get("water_ml", 0)
            
            # 格式化時間
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except:
                time_str = ts[11:16] if len(ts) > 16 else ts
            
            # 卡片化呈現
            with st.container(border=True):
                col_rec, col_del = st.columns([4, 1])
                with col_rec:
                    st.write(f"**{time_str}** {MEAL_EMOJI.get(meal_type, '')} {meal_type}: {summary}")
                    st.caption(f"熱量 {cal:.0f} | 蛋白 {pro:.0f}g | 碳水 {carb:.0f}g | 脂肪 {fat:.0f}g | 飲水 {water:.0f}ml")
                with col_del:
                    if st.button("刪除", key=f"del_today_{ts}"):
                        try:
                            sheets.delete_record(ts, uid)
                            _clear_analysis_cache()
                            st.success("記錄已刪除！")
                            st.rerun()
                        except Exception as exc:
                            st.error("刪除失敗: " + str(exc))
    else:
        st.info("今天還沒有任何記錄。")
    
    st.caption(f"基礎代謝率 (BMR): {bmr:.0f} 大卡")



def page_log_meal() -> None:
    """主流程：選餐別 → 選輸入方式 → AI 分析 → 份數微調 → 確認送出。"""
    st.header("記一餐")
    meal = st.session_state.pending_meal_type

    if meal is None:
        _render_meal_picker()
        return

    _hdr_emoji = MEAL_EMOJI.get(meal, "")
    st.subheader(_hdr_emoji + " 記錄: " + meal)
    if st.button("← 重選餐別", key="reset_meal"):
        st.session_state.pending_meal_type = None
        st.session_state.input_mode = None
        st.session_state.pending_analysis = None
        st.rerun()
        return

    if meal == "飲水":
        _render_water_section(meal)
        return

    if st.session_state.pending_analysis is None:
        _render_input_section(meal)
        return

    _render_review_section(meal)


def _render_water_section(meal) -> None:
    """飲水簡化流程：單一 ml 輸入 + 確認鈕，直接寫入 Sheets，不送 Gemini。"""
    st.subheader("飲水")
    with st.form("water_form"):
        water_ml = st.number_input("飲水量 (ml)", min_value=0.0, value=500.0, step=50.0, format="%.0f")
        confirm = st.form_submit_button("確認送出", use_container_width=True)
        if confirm:
            # 使用 session_state 跨過 form 變數作用域的限制
            st.session_state["_water_form_submitted"] = True
            st.session_state["_water_form_ml"] = float(water_ml)
            st.rerun()

    if not st.session_state.get("_water_form_submitted", False):
        return
    # 取出後立刻清除，避免重複處理
    st.session_state.pop("_water_form_submitted", None)
    submitted_ml = float(st.session_state.pop("_water_form_ml", 0.0))

    summary = "飲水 " + str(int(submitted_ml)) + "ml"
    try:
        _commit_record(meal, summary, {}, 1.0, submitted_ml, {})
    except Exception as exc:
        st.error("寫入 Sheets 失敗: " + str(exc))
        return
    st.success("已送出！")
    st.session_state.pending_meal_type = None
    st.session_state.input_mode = None
    st.session_state.pending_analysis = None
    st.balloons()
    st.rerun()


def _render_meal_picker() -> None:
    """5 個入口卡片。"""
    st.write("請選擇一餐：")
    cols = st.columns(5)
    for i, meal in enumerate(MEAL_TYPES):
        emoji = MEAL_EMOJI.get(meal, "")
        with cols[i]:
            label = emoji + " " + meal
            if st.button(label, key="pick_meal_"+meal, use_container_width=True):
                st.session_state.pending_meal_type = meal
                st.session_state.input_mode = None
                st.session_state.pending_analysis = None
                st.rerun()


def _render_input_section(meal) -> None:
    """Step 1: 讓使用者選輸入方式；Step 2: 依選擇呈現對應 widget。"""
    mode = st.session_state.input_mode
    if mode is None:
        st.write("請選擇輸入方式：")
        cols = st.columns(3)
        if cols[0].button("拍照", use_container_width=True, key="mode_photo"):
            st.session_state.input_mode = "photo"
            st.rerun()
        if cols[1].button("從圖庫上傳", use_container_width=True, key="mode_upload"):
            st.session_state.input_mode = "upload"
            st.rerun()
        if cols[2].button("手打文字", use_container_width=True, key="mode_text"):
            st.session_state.input_mode = "text"
            st.rerun()
        return

    mode_label = {"photo": "拍照", "upload": "從圖庫上傳", "text": "手打文字"}.get(mode, mode)
    st.write("已選輸入方式: " + mode_label)
    if st.button("← 重選輸入方式", key="reset_mode"):
        st.session_state.input_mode = None
        st.rerun()
        return

    image_bytes = None
    content_type = None
    text = ""
    with st.form("input_form_"+meal, clear_on_submit=False):
        if mode == "photo":
            shot = st.camera_input("拍照", key="cam_"+meal)
            if shot is not None:
                image_bytes = shot.getvalue()
                content_type = shot.type or "image/jpeg"
        elif mode == "upload":
            upload = st.file_uploader("上傳照片", type=["jpg", "jpeg", "png", "webp"], key="up_"+meal)
            if upload is not None:
                image_bytes = upload.getvalue()
                content_type = upload.type or "image/jpeg"
        else:
            text = st.text_area("食物描述", placeholder="例如: 一個便當含炒麵、雞腿、三式青菜", key="txt_"+meal)
        send = st.form_submit_button("送出分析", use_container_width=True)
    if send:
        if image_bytes is None and not text.strip():
            st.error("請提供照片或文字描述")
            return
        with st.spinner("Gemini 分析中..."):
            try:
                result = _run_analysis(image_bytes, content_type, text)
            except Exception as exc:
                _err = "分析失敗: "
                st.error(_err + str(exc))
                return
        st.session_state.pending_analysis = {
            "raw": result,
            "image_bytes": image_bytes,
            "content_type": content_type,
            "meal": meal,
        }
        st.rerun()


def _render_review_section(meal) -> None:
    """顯示 AI 結果 + 份數微調 + 飲水量手動輸入 + 確認送出。"""
    pending = st.session_state.pending_analysis
    raw = pending.get("raw", {})
    if not raw:
        st.error("沒有分析結果，請重新上傳。")
        if st.button("← 重新開始"):
            st.session_state.pending_analysis = None
            st.rerun()
        return
    summary = str(raw.get("food_summary", ""))
    st.success("AI 結果: " + summary)

    with st.form("review_form"):
        portion = st.number_input("份數", min_value=0.0, value=1.0, step=0.25, format="%.2f")
        edited_summary = st.text_input("食物摘要（可修改）", value=summary)
        if meal == "飲水":
            water_ml = st.number_input("飲水量 (ml)", min_value=0.0, value=500.0, step=50.0, format="%.0f")
        else:
            water_ml = st.number_input("額外飲水量 (ml, 可選)", min_value=0.0, value=0.0, step=50.0, format="%.0f")
        st.write("**最終送出值**")
        final_rows = []
        for key, label, unit in metrics.METRIC_FIELDS:
            if key == "water":
                base = water_ml
            else:
                _val = raw.get(key, 0)
                base = float(_val) if _val is not None else 0.0
            final = base * portion if key != "water" else base
            _line = f"- {label}: {final:.1f} {unit}"
            final_rows.append(_line)
        st.markdown(chr(10).join(final_rows))
        col1, col2 = st.columns(2)
        confirm = col1.form_submit_button("確認送出", use_container_width=True)
        reedit = col2.form_submit_button("重新編輯描述", use_container_width=True)
        if confirm:
            # 使用 session_state 跨過 form 變數作用域的限制
            st.session_state["_review_form_action"] = "confirm"
            st.session_state["_review_form_portion"] = float(portion)
            st.session_state["_review_form_summary"] = edited_summary
            st.session_state["_review_form_water_ml"] = float(water_ml)
            st.rerun()
        elif reedit:
            st.session_state["_review_form_action"] = "reedit"
            st.rerun()

    action = st.session_state.pop("_review_form_action", None)
    if action == "reedit":
        st.session_state.pending_analysis = None
        st.session_state.input_mode = "text"
        st.rerun()
        return
    if action == "confirm":
        submitted_portion = float(st.session_state.pop("_review_form_portion", 1.0))
        submitted_summary = st.session_state.pop("_review_form_summary", summary)
        submitted_water = float(st.session_state.pop("_review_form_water_ml", 0.0))
        try:
            _commit_record(meal, submitted_summary, raw, submitted_portion, submitted_water, pending)
        except Exception as exc:
            st.error("寫入 Sheets 失敗: " + str(exc))
            return
        st.success("已送出！")
        st.session_state.pending_meal_type = None
        st.session_state.input_mode = None
        st.session_state.pending_analysis = None
        st.balloons()
        st.rerun()


def _commit_record(meal, summary, raw, portion, water_ml, pending) -> None:
    """把 AI 結果 × portion 寫入 Sheets。"""
    uid = st.session_state.user_id
    image_url = ""
    if pending.get("image_bytes"):
        try:
            image_url = firebase.upload_image(pending["image_bytes"], pending.get("content_type") or "image/jpeg", uid)
        except Exception as exc:
            st.warning("照片上傳失敗，僅寫入文字結果: " + str(exc))
    _get = raw.get
    cal = float(_get("calories", 0) or 0) * portion
    pro = float(_get("protein", 0) or 0) * portion
    crb = float(_get("carb", 0) or 0) * portion
    fat = float(_get("fat", 0) or 0) * portion
    sheets.append_record(
        auth.now_iso(),
        uid,
        meal,
        summary,
        cal,
        pro,
        crb,
        fat,
        water_ml,
        image_url,
        portion,
    )
    _clear_analysis_cache()


def page_tdee() -> None:
    """TDEE 計算頁面：輸入基本資料計算 BMR 與營養目標。"""
    st.header("TDEE 與基礎代謝率計算")

    uid = st.session_state.user_id
    goals = _fetch_goals_cached(uid)

    # 初始化 session_state 來記住「已確認重新計算」的狀態，
    # 避免使用者每次重來都要重複點確認鈕
    if "tdee_recalc_confirmed" not in st.session_state:
        st.session_state.tdee_recalc_confirmed = False

    # 檢查是否已設定 TDEE
    current_bmr = goals.get("bmr", 0)
    has_existing = current_bmr > 0
    # 走過警告的條件 = 有舊值 且 使用者未確認要重算
    show_recalc_warning = has_existing and not st.session_state.tdee_recalc_confirmed

    if show_recalc_warning:
        st.warning("您已經計算過 TDEE，重新計算會覆蓋之前的設定。")
        col_confirm = st.columns([1, 1])
        with col_confirm[0]:
            confirm_recalc = st.button("確認重新計算", use_container_width=True, key="tdee_confirm_recalc")
        with col_confirm[1]:
            cancel_recalc = st.button("取消", use_container_width=True, key="tdee_cancel_recalc")

        if cancel_recalc:
            st.session_state.tdee_recalc_confirmed = False
            st.session_state.page = "個人"
            st.rerun()
            return

        if confirm_recalc:
            st.session_state.tdee_recalc_confirmed = True
            st.rerun()
            return

        # 使用者未確認、也未取消 → 停在警告畫面
        return

    # 顯示當前 BMR（如果有的話）
    if has_existing:
        st.info(f"您目前設定的 BMR：{current_bmr:.0f} 大卡")

    with st.form("tdee_form"):
        st.subheader("請填寫您的基本資料")

        col1, col2 = st.columns(2)
        with col1:
            gender = st.radio("性別", ["男", "女"], horizontal=True, index=0)
            age = st.number_input("年齡（歲）", min_value=10, max_value=120, value=30, step=1)
        with col2:
            height = st.number_input("身高（cm）", min_value=100.0, max_value=250.0, value=170.0, step=1.0)
            weight = st.number_input("體重（kg）", min_value=30.0, max_value=200.0, value=65.0, step=0.5)

        exercise_level = st.select_slider(
            "每週運動頻率",
            options=list(TDEE_MULTIPLIERS.keys()),
            value="每週運動 1-3 天"
        )

        submitted = st.form_submit_button("計算 BMR 與目標", use_container_width=True)
        if submitted:
            # 用 session_state 跨過 form 變數作用域的限制
            st.session_state["_tdee_form_submitted"] = True
            st.session_state["_tdee_form_data"] = {
                "gender": gender,
                "age": int(age),
                "height": float(height),
                "weight": float(weight),
                "exercise_level": exercise_level,
            }
            st.rerun()

    if not st.session_state.pop("_tdee_form_submitted", False):
        return
    tdee_data = st.session_state.pop("_tdee_form_data", None)
    if not tdee_data:
        return

    # 計算 BMR
    bmr = _calculate_bmr(tdee_data["weight"], tdee_data["height"], tdee_data["age"], tdee_data["gender"])

    # 計算 TDEE
    tdee = _calculate_tdee(bmr, tdee_data["exercise_level"])

    # 計算所有目標
    calculated_goals = _calculate_goals(tdee_data["weight"], tdee)

    # 顯示結果
    st.success("計算完成！以下是您的個人化營養目標：")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("基礎代謝率 (BMR)", f"{bmr:.0f} 大卡")
        st.metric("每日總消耗 (TDEE)", f"{tdee:.0f} 大卡")
        st.metric("建議熱量攝取", f"{calculated_goals['calorie']:.0f} 大卡（減重目標）")
    with col2:
        st.metric("飲水量目標", f"{calculated_goals['water']:.0f} ml")
        st.metric("蛋白質目標", f"{calculated_goals['protein']:.0f} g")
        st.metric("脂質目標", f"{calculated_goals['fat']:.0f} g")
        st.metric("碳水化合物目標", f"{calculated_goals['carb']:.0f} g")

    # 更新到 Google Sheets
    try:
        # 更新 BMR
        sheets.update_user_bmr(uid, bmr)

        # 更新所有目標
        sheets.update_user_goals(uid, calculated_goals)

        # 清除快取
        _clear_analysis_cache()

        # 計算完成，重置重新計算確認狀態
        st.session_state.tdee_recalc_confirmed = False

        st.success("目標已同步更新到您的帳戶！")
        st.rerun()
    except Exception as exc:
        st.error("更新失敗: " + str(exc))



def _show_records_table(records, show_actions: bool = False) -> None:
    """把 list[dict] 整理成 dataframe 給使用者看，支援編輯/刪除。"""
    uid = st.session_state.user_id
    
    rows = []
    for r in records:
        row_data = {
            "時間": r.get("timestamp", ""),
            "餐別": r.get("meal_type", ""),
            "摘要": r.get("food_summary", ""),
            "熱量": r.get("calories", 0),
            "蛋白": r.get("protein", 0),
            "碳水": r.get("carb", 0),
            "脂質": r.get("fat", 0),
            "飲水": r.get("water_ml", 0),
            "份數": r.get("portion", 1),
        }
        rows.append(row_data)
    
    rows.sort(key=lambda x: str(x.get("時間", "")), reverse=True)
    
    if not show_actions:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        return
    
    # 顯示可編輯的版本
    st.dataframe(rows, use_container_width=True, hide_index=True)
    
    # 編輯/刪除操作
    for r in records:
        ts = r.get("timestamp", "")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"編輯", key=f"edit_{ts}"):
                st.session_state[f"edit_mode_{ts}"] = True
        with col2:
            if st.button(f"刪除", key=f"delete_{ts}"):
                try:
                    sheets.delete_record(ts, uid)
                    _clear_analysis_cache()
                    st.success("記錄已刪除！")
                    st.rerun()
                except Exception as exc:
                    st.error("刪除失敗: " + str(exc))
        
        # 編輯表單
        if st.session_state.get(f"edit_mode_{ts}", False):
            with st.expander(f"編輯記錄 - {ts}"):
                with st.form(f"edit_form_{ts}"):
                    new_summary = st.text_input("食物摘要", value=r.get("food_summary", ""))
                    new_portion = st.number_input("份數", min_value=0.0, value=float(r.get("portion", 1)), step=0.25, format="%.2f")
                    
                    # 營養數值（根據份數重新計算）
                    base_cal = float(r.get("calories", 0)) / float(r.get("portion", 1)) if r.get("portion", 1) > 0 else 0
                    base_pro = float(r.get("protein", 0)) / float(r.get("portion", 1)) if r.get("portion", 1) > 0 else 0
                    base_carb = float(r.get("carb", 0)) / float(r.get("portion", 1)) if r.get("portion", 1) > 0 else 0
                    base_fat = float(r.get("fat", 0)) / float(r.get("portion", 1)) if r.get("portion", 1) > 0 else 0
                    
                    new_cal = st.number_input("熱量", value=base_cal, step=1.0)
                    new_pro = st.number_input("蛋白質 (g)", value=base_pro, step=1.0)
                    new_carb = st.number_input("碳水化合物 (g)", value=base_carb, step=1.0)
                    new_fat = st.number_input("脂質 (g)", value=base_fat, step=1.0)
                    new_water = st.number_input("飲水量 (ml)", value=float(r.get("water_ml", 0)), step=10.0)
                    
                    col_save, col_cancel = st.columns(2)
                    submitted = col_save.form_submit_button("儲存", use_container_width=True)
                    cancelled = col_cancel.form_submit_button("取消", use_container_width=True)
                
                if submitted:
                    try:
                        # 重新計算營養值（乘上新份數）
                        sheets.update_record(ts, uid, {
                            "food_summary": new_summary,
                            "portion": new_portion,
                            "calories": new_cal * new_portion,
                            "protein": new_pro * new_portion,
                            "carb": new_carb * new_portion,
                            "fat": new_fat * new_portion,
                            "water_ml": new_water,
                        })
                        _clear_analysis_cache()
                        st.session_state[f"edit_mode_{ts}"] = False
                        st.success("記錄已更新！")
                        st.rerun()
                    except Exception as exc:
                        st.error("更新失敗: " + str(exc))
                
                if cancelled:
                    st.session_state[f"edit_mode_{ts}"] = False
                    st.rerun()



def page_history() -> None:
    """歷史分頁：每日達成率 + 趨勢圖。"""
    st.header("歷史與週進度")
    uid = st.session_state.user_id
    try:
        records = _fetch_records_cached(uid)
        goals = _fetch_goals_cached(uid)
    except Exception as exc:
        st.error("讀取記錄失敗: " + str(exc))
        return
    
    # 檢查是否已設定 TDEE
    bmr = goals.get("bmr", 0)
    calorie_goal = goals.get("calorie", 0)
    
    if bmr <= 0 or calorie_goal <= 0:
        st.warning("請先在「個人」頁面設定您的 TDEE 目標")
        return
    
    ws, we = _week_range()
    days = (we - ws).days + 1
    
    # 取得每日目標
    daily_calorie = goals.get("calorie", 0.0)
    daily_protein = goals.get("protein", 0.0)
    
    # 建立每日達成率表格
    st.subheader("本週每日達成率")
    daily_data = []
    for i in range(days):
        d = ws + timedelta(days=i)
        day_recs = metrics.filter_records(records, d, d)
        day_totals = metrics.sum_totals(day_recs).as_dict()
        
        day_cal = float(day_totals.get("calorie", 0.0))
        day_pro = float(day_totals.get("protein", 0.0))
        
        cal_ratio = (day_cal / daily_calorie) if daily_calorie > 0 else 0.0
        pro_ratio = (day_pro / daily_protein) if daily_protein > 0 else 0.0
        
        # 格式化日期顯示
        date_str = d.strftime("%m/%d")
        weekday = ["一", "二", "三", "四", "五", "六", "日"][d.weekday()]
        
        daily_data.append({
            "日期": f"{date_str}({weekday})",
            "熱量": day_cal,
            "熱量目標": daily_calorie,
            "熱量達成率": f"{cal_ratio:.0%}",
            "蛋白質": day_pro,
            "蛋白質目標": daily_protein,
            "蛋白質達成率": f"{pro_ratio:.0%}",
        })
    
    # 顯示每日達成率表格
    st.dataframe(daily_data, use_container_width=True, hide_index=True)
    
    # 視覺化：每日熱量達成率長條圖
    st.subheader("本週熱量達成率")
    calorie_chart = {
        "日期": [],
        "達成率 (%)": [],
    }
    for i in range(days):
        d = ws + timedelta(days=i)
        day_recs = metrics.filter_records(records, d, d)
        day_totals = metrics.sum_totals(day_recs).as_dict()
        day_cal = float(day_totals.get("calorie", 0.0))
        cal_ratio = (day_cal / daily_calorie * 100) if daily_calorie > 0 else 0.0
        calorie_chart["日期"].append(d.strftime("%m/%d"))
        calorie_chart["達成率 (%)"].append(min(cal_ratio, 100))  # 最多顯示 100%
    
    st.bar_chart(calorie_chart, x="日期", y="達成率 (%)")
    
    # 視覺化：每日蛋白質達成率長條圖
    st.subheader("本週蛋白質達成率")
    protein_chart = {
        "日期": [],
        "達成率 (%)": [],
    }
    for i in range(days):
        d = ws + timedelta(days=i)
        day_recs = metrics.filter_records(records, d, d)
        day_totals = metrics.sum_totals(day_recs).as_dict()
        day_pro = float(day_totals.get("protein", 0.0))
        pro_ratio = (day_pro / daily_protein * 100) if daily_protein > 0 else 0.0
        protein_chart["日期"].append(d.strftime("%m/%d"))
        protein_chart["達成率 (%)"].append(min(pro_ratio, 100))
    
    st.bar_chart(protein_chart, x="日期", y="達成率 (%)")

    # 本週營養攝取趨勢
    st.subheader("本週每日趨勢")
    chart = {
        "date": [],
        "熱量": [],
        "蛋白": [],
        "碳水": [],
        "脂質": [],
        "飲水": [],
    }
    for i in range(days):
        d = ws + timedelta(days=i)
        day_recs = metrics.filter_records(records, d, d)
        day_totals = metrics.sum_totals(day_recs).as_dict()
        chart["date"].append(d.isoformat())
        chart["熱量"].append(float(day_totals.get("calorie", 0.0)))
        chart["蛋白"].append(float(day_totals.get("protein", 0.0)))
        chart["碳水"].append(float(day_totals.get("carb", 0.0)))
        chart["脂質"].append(float(day_totals.get("fat", 0.0)))
        chart["飲水"].append(float(day_totals.get("water", 0.0)))
    st.line_chart(chart, x="date")
    
    # 取得本週記錄用於顯示明細
    week_records = metrics.filter_records(records, ws, we)
    
    st.subheader("本週明細")
    if week_records:
        _show_records_table(week_records, show_actions=False)
    else:
        st.info("本週還沒有任何紀錄。")

    with st.expander("完整歷史"):
        all_recs = [r for r in records]
        if all_recs:
            _show_records_table(all_recs, show_actions=False)
        else:
            st.info("尚無任何紀錄。")



def _coach_overview_stub() -> None:
    st.info("學員總覽（Phase 2 待實作）")

def _coach_notes_stub() -> None:
    st.info("加備註（Phase 2 待實作）")

def _coach_goals_stub() -> None:
    st.info("設定學生目標（Phase 2 待實作）")

def main() -> None:
    """App 入口：未登入 → 登入頁；已登入 → 側邊欄切換分頁。"""
    st.set_page_config(page_title="熱量與飲水紀錄", layout="wide")
    
    # 自訂「清新燕麥減脂風」樣式
    st.markdown("""
    <style>
        /* 引入 Line Seed 字體 */
        @import url('https://fonts.googleapis.com/css2?family=Line+Seed+JP:wght@400&display=swap');
        
        /* 1. 全域背景與文字優化 */
        .stApp {
            background-color: #FFFFFF !important;
            color: #2F3E46 !important;
            font-family: 'Line Seed JP', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        }

        /* 2. 標題與副標題顏色調和 */
        h1, h2, h3, h4, h5, h6 {
            color: #2F3E46 !important;
            font-weight: 400 !important;
        }

        /* 3. 今日儀表板 st.metric 卡片化（暖白輕盈風格） */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            padding: 20px 24px !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 24px rgba(149, 157, 165, 0.06) !important;
            border: 1px solid #EAE8E4 !important;
        }
        /* 微調 metric 裡面的標題與數字間距 */
        div[data-testid="stMetricLabel"] {
            color: #6C7A89 !important;
            font-size: 0.9rem !important;
        }
        div[data-testid="stMetricValue"] {
            color: #2F3E46 !important;
            font-size: 1.8rem !important;
            font-weight: 400 !important;
        }

        /* 4. 輸入區塊與食物內容的 Container 卡片化 */
        div[data-testid="stElementContainer"] > div[class*="stVerticalBlock"] > div[style*="border"] {
            background-color: #FFFFFF !important;
            border-radius: 16px !important;
            border: 1px solid #EAE8E4 !important;
            padding: 20px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
        }

        /* 5. 主要按鈕 (Primary Button) 樣式 - 森林薄荷綠 */
        div.stButton > button[kind="primary"] {
            background-color: #4A7C59 !important;
            color: #FFFFFF !important;
            border-radius: 12px !important;
            border: none !important;
            padding: 0.6rem 2rem !important;
            font-weight: 400 !important;
            width: 100%;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 12px rgba(74, 124, 89, 0.2) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #385E43 !important;
            box-shadow: 0 6px 16px rgba(74, 124, 89, 0.3) !important;
            transform: translateY(-1px);
        }

        /* 6. 次要按鈕 / 一般按鈕 樣式 */
        div.stButton > button[kind="secondary"] {
            background-color: #FFFFFF !important;
            color: #4A7C59 !important;
            border: 1px solid #4A7C59 !important;
            border-radius: 12px !important;
            padding: 0.6rem 2rem !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            background-color: #F4F7F5 !important;
            color: #385E43 !important;
            border-color: #385E43 !important;
        }

        /* 7. 進度條 (st.progress) 變得更圓潤 */
        div[data-testid="stProgress"] > div > div > div {
            background-color: #4A7C59 !important; /* 已達成進度顏色 */
        }
        div[data-testid="stProgress"] {
            height: 8px !important;
            border-radius: 4px !important;
        }

        /* 8. 調整 Tab 標籤頁的樣式 */
        button[data-baseweb="tab"] {
            color: #6C7A89 !important;
            font-size: 1rem !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #4A7C59 !important;
            font-weight: 400 !important;
            border-bottom-color: #4A7C59 !important;
        }

        /* 9. 強制淺色模式（覆蓋深色設定） */
        * {
            color: #2F3E46 !important;
        }

        /* 10. 側邊欄樣式 */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #EAE8E4 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            background-color: #FFFFFF !important;
        }

        /* 11. 輸入框樣式 */
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea {
            background-color: #FFFFFF !important;
            border: 1px solid #EAE8E4 !important;
            border-radius: 8px !important;
            color: #2F3E46 !important;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stNumberInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: #4A7C59 !important;
            box-shadow: 0 0 0 2px rgba(74, 124, 89, 0.1) !important;
        }

        /* 12. Radio 按鈕樣式 */
        div[data-testid="stRadio"] label {
            color: #2F3E46 !important;
        }

        /* 13. Slider 樣式 */
        div[data-testid="stSlider"] .stSlider > div > div > div[style*="background-color: rgb(74, 124, 89)"] {
            background-color: #4A7C59 !important;
        }

        /* 14. Selectbox 下拉選單樣式 */
        div[data-testid="stSelectbox"] {
            background-color: #FFFFFF !important;
        }
        div[data-testid="stSelectbox"] select {
            background-color: #FFFFFF !important;
            border: 1px solid #EAE8E4 !important;
            border-radius: 8px !important;
            color: #2F3E46 !important;
        }

        /* 15. Dataframe 表格樣式 */
        div[data-testid="stDataFrame"] {
            background-color: #FFFFFF !important;
            border-radius: 12px !important;
            border: 1px solid #EAE8E4 !important;
        }

        /* 16. Expander 摺疊面板樣式 */
        details[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border-radius: 12px !important;
            border: 1px solid #EAE8E4 !important;
        }

        /* 17. 成功/警告/錯誤提示樣式 */
        div[data-testid="stSuccess"] {
            background-color: #E8F5E9 !important;
            color: #2E7D32 !important;
            border-radius: 8px !important;
        }
        div[data-testid="stWarning"] {
            background-color: #FFF3E0 !important;
            color: #E65100 !important;
            border-radius: 8px !important;
        }
        div[data-testid="stError"] {
            background-color: #FFEBEE !important;
            color: #C62828 !important;
            border-radius: 8px !important;
        }
        div[data-testid="stInfo"] {
            background-color: #E3F2FD !important;
            color: #1565C0 !important;
            border-radius: 8px !important;
        }

        /* 18. 修正文字可能被遮擋的問題 */
        .main .block-container {
            padding-bottom: 3rem !important;
        }

        /* 19. Camera input 拍照框 */
        div[data-testid="stCameraInput"] {
            background-color: #FFFFFF !important;
            border-radius: 12px !important;
            border: 1px solid #EAE8E4 !important;
        }

        /* 20. File uploader */
        div[data-testid="stFileUploader"] {
            background-color: #FFFFFF !important;
            border-radius: 12px !important;
            border: 2px dashed #EAE8E4 !important;
        }

        /* 21. Form submit button */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #4A7C59 !important;
            color: #FFFFFF !important;
            border-radius: 12px !important;
            border: none !important;
            padding: 0.6rem 2rem !important;
            font-weight: 400 !important;
            width: 100%;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #385E43 !important;
        }

        /* 22. Metric 卡片所有內部元素統一白底 */
        div[data-testid="stMetric"] * {
            background-color: #FFFFFF !important;
        }
        div[data-testid="stMetric"] > div {
            background-color: #FFFFFF !important;
        }

        /* 23. 手機響應式設計 */
        @media (max-width: 768px) {
            /* Metric 卡片手機適配 */
            div[data-testid="stMetric"] {
                margin-bottom: 12px !important;
                padding: 16px !important;
            }
            
            /* 側邊欄手機寬度 */
            [data-testid="stSidebar"] {
                width: 220px !important;
                min-width: 220px !important;
            }
            
            /* Columns 手機適配 */
            .stColumns > div {
                flex-wrap: wrap !important;
            }
            
            /* 調整文字大小 */
            h1 { font-size: 1.5rem !important; }
            h2 { font-size: 1.3rem !important; }
            h3 { font-size: 1.1rem !important; }
            
            /* 按鈕全寬 */
            div.stButton > button,
            div[data-testid="stFormSubmitButton"] button {
                width: 100% !important;
            }
            
            /* 表格水平滾動 */
            div[data-testid="stDataFrame"] {
                overflow-x: auto !important;
            }
        }

        /* 24. 統一全域背景為白色（覆蓋所有可能產生色差的元素） */
        body, .stApp, .stApp > div, .main, .main > div,
        .block-container, section.main > div,
        [data-testid="stSidebar"], [data-testid="stSidebarContent"],
        div[data-testid="stVerticalBlock"], div[data-testid="stHorizontalBlock"],
        .stTabs, div[data-testid="stTabContent"],
        .stForm, [data-testid="stFormSubmitButton"],
        .streamlit-expanderHeader, details[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
        }

        /* 登入頁面特殊處理 */
        [data-testid="stTabsContent"] {
            background-color: #FFFFFF !important;
        }

        /* 移除 Tab 和 Form 內部所有子元素的預設背景 */
        .stTabs * {
            background-color: #FFFFFF !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    init_session()
    if not st.session_state.user_id:
        page_login()
        return
    with st.sidebar:
        _uname = str(st.session_state.username or "")
        _role = st.session_state.get("role", None)
        _role_label = "教練" if _role == "coach" else "學員"
        st.write("👤 " + _uname + " (" + _role_label + ")")
        st.caption("_raw=" + str(st.session_state.get("_dbg_raw")))
        if st.session_state.get("user_id"):
            try:
                _dbg_uid = str(st.session_state.user_id)
                from services import sheets as _dbg_sheets
                _dbg_rows = [r for r in _dbg_sheets.get_users_rows() if r.get("user_id") == _dbg_uid]
                _dbg_match = _dbg_rows[0] if _dbg_rows else None
                st.caption(f"debug: uid={_dbg_uid} | row_found={bool(_dbg_match)} | role_in_sheet={(_dbg_match.get('role') if _dbg_match else None)!r}")
            except Exception as _e:
                st.caption(f"debug-err: {_e}")
        if _role == "coach":
            _pages = ["學員總覽", "加備註", "設定學生目標"]
            _default = "學員總覽"
        else:
            _pages = ["個人", "記錄", "歷史", "TDEE 計算"]
            _default = "個人"
        try:
            _idx = _pages.index(st.session_state.get("page", _default))
        except ValueError:
            _idx = 0
        page = st.radio("切換分頁", _pages, index=_idx)
        st.session_state.page = page
        if st.button("登出", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k != "page":
                    del st.session_state[k]
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    _is_coach_now = st.session_state.get("role") == "coach"
    if _is_coach_now:
        if st.session_state.page == "學員總覽":
            _coach_overview_stub()
        elif st.session_state.page == "加備註":
            _coach_notes_stub()
        elif st.session_state.page == "設定學生目標":
            _coach_goals_stub()
    elif st.session_state.page == "個人":
        page_personal()
    elif st.session_state.page == "記錄":
        page_log_meal()
    elif st.session_state.page == "歷史":
        page_history()
    else:
        page_tdee()


if __name__ == "__main__":
    main()
