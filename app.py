"""
AI 智能多人熱量與飲水紀錄 Web App。

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
MEAL_EMOJI = {"早餐": "🌅", "午餐": "🍱", "晚餐": "🌙", "小點": "🍪", "飲水": "💧"}
NUTRIENT_KEYS = ("calorie", "protein", "carb", "fat")
CACHE_TTL = 60
DEFAULT_GOALS = {"calorie": 2000.0, "protein": 60.0, "carb": 250.0, "fat": 65.0, "water": 2000.0}


def init_session() -> None:
    """初始化所有 session_state key。"""
    defaults = {
        "user_id": None,
        "username": None,
        "page": "記一餐",
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
    st.title("🍽️ 熱量與飲水紀錄")
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
            st.success("註冊成功並已登入！")
            st.rerun()



def page_log_meal() -> None:
    """主流程：選餐別 → 選輸入方式 → AI 分析 → 份數微調 → 確認送出。"""
    st.header("🍴 記一餐")
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
    st.subheader("💧 飲水")
    with st.form("water_form"):
        water_ml = st.number_input("飲水量 (ml)", min_value=0.0, value=500.0, step=50.0, format="%.0f")
        confirm = st.form_submit_button("✅ 確認送出", use_container_width=True)
    if not confirm:
        return
    summary = ("飲水 " + str(int(water_ml)) + "ml")
    try:
        _commit_record(meal, summary, {}, 1.0, water_ml, {})
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
        if cols[0].button("📷 拍照", use_container_width=True, key="mode_photo"):
            st.session_state.input_mode = "photo"
            st.rerun()
        if cols[1].button("🖼️ 從圖庫上傳", use_container_width=True, key="mode_upload"):
            st.session_state.input_mode = "upload"
            st.rerun()
        if cols[2].button("✍️ 手打文字", use_container_width=True, key="mode_text"):
            st.session_state.input_mode = "text"
            st.rerun()
        return

    mode_label = {"photo": "📷 拍照", "upload": "🖼️ 從圖庫上傳", "text": "✍️ 手打文字"}.get(mode, mode)
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
        confirm = col1.form_submit_button("✅ 確認送出", use_container_width=True)
        reedit = col2.form_submit_button("✏️ 重新編輯描述", use_container_width=True)

    if reedit:
        st.session_state.pending_analysis = None
        st.session_state.input_mode = "text"
        st.rerun()
        return
    if confirm:
        try:
            _commit_record(meal, edited_summary, raw, portion, water_ml, pending)
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



def page_today() -> None:
    """今日分頁：5 條進度條 + 累積/目標數字，不做視覺警示。"""
    st.header("📅 今日進度")
    uid = st.session_state.user_id
    try:
        records = _fetch_records_cached(uid)
        goals = _fetch_goals_cached(uid)
    except Exception as exc:
        st.error("讀取記錄失敗: " + str(exc))
        return
    start, end = _today_range()
    today_records = metrics.filter_records(records, start, end)
    totals = metrics.sum_totals(today_records).as_dict()
    for key, label, unit in metrics.METRIC_FIELDS:
        g = goals.get(key, 0.0)
        v = float(totals.get(key, 0.0))
        ratio = (v / g) if g > 0 else 0.0
        ratio = max(0.0, min(ratio, 1.0))
        st.metric(label=label, value="{:.1f} {}".format(v, unit), delta="目標 {:.1f} {}".format(g, unit), delta_color="off")
        st.progress(ratio)
    st.subheader("今日明細")
    if today_records:
        _show_records_table(today_records)
    else:
        st.info("今天還沒有任何紀錄。")


def page_history() -> None:
    """歷史分頁：週統計 + 評比標籤 + 折線圖。"""
    st.header("📊 歷史與週進度")
    uid = st.session_state.user_id
    try:
        records = _fetch_records_cached(uid)
        goals = _fetch_goals_cached(uid)
    except Exception as exc:
        st.error("讀取記錄失敗: " + str(exc))
        return
    ws, we = _week_range()
    days = (we - ws).days + 1
    week_records = metrics.filter_records(records, ws, we)
    totals = metrics.sum_totals(week_records).as_dict()

    st.subheader("本週累積 vs 目標")
    for key, label, unit in metrics.METRIC_FIELDS:
        g_day = goals.get(key, 0.0)
        week_goal = g_day * days
        v = float(totals.get(key, 0.0))
        ratio = (v / week_goal) if week_goal > 0 else 0.0
        status, pct = metrics.classify(ratio)
        st.metric(label=label, value="{:.1f} {}".format(v, unit), delta="目標 {:.1f} {}（{} 天）".format(week_goal, unit, days), delta_color="off")
        pct_str = "達成率 {:.0%}".format(ratio)
        if status == "未達":
            st.warning(f"本週 {label} 未達，{pct_str}")
        elif status == "超標":
            st.error(f"本週 {label} 超標，{pct_str}")
        else:
            st.success(f"本週 {label} 達成，{pct_str}")

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

    st.subheader("本週明細")
    if week_records:
        _show_records_table(week_records)
    else:
        st.info("本週還沒有任何紀錄。")

    with st.expander("🔎 完整歷史"):
        all_recs = [r for r in records]
        if all_recs:
            _show_records_table(all_recs)
        else:
            st.info("尚無任何紀錄。")


def _show_records_table(records) -> None:
    """把 list[dict] 整理成 dataframe 給使用者看。"""
    rows = []
    for r in records:
        rows.append({
            "時間": r.get("timestamp", ""),
            "餐別": r.get("meal_type", ""),
            "摘要": r.get("food_summary", ""),
            "熱量": r.get("calories", 0),
            "蛋白": r.get("protein", 0),
            "碳水": r.get("carb", 0),
            "脂質": r.get("fat", 0),
            "飲水": r.get("water_ml", 0),
            "份數": r.get("portion", 1),
        })
    rows.sort(key=lambda x: str(x.get("時間", "")), reverse=True)
    st.dataframe(rows, use_container_width=True, hide_index=True)


def main() -> None:
    """App 入口：未登入 → 登入頁；已登入 → 側邊欄切換分頁。"""
    st.set_page_config(page_title="熱量與飲水紀錄", page_icon="🍽️", layout="wide")
    init_session()
    if not st.session_state.user_id:
        page_login()
        return
    with st.sidebar:
        st.write("👤 " + str(st.session_state.username or ""))
        page = st.radio("切換分頁", ["記一餐", "今日", "歷史"], index=["記一餐", "今日", "歷史"].index(st.session_state.get("page", "記一餐")))
        st.session_state.page = page
        if st.button("🚪 登出", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k != "page":
                    del st.session_state[k]
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    if st.session_state.page == "記一餐":
        page_log_meal()
    elif st.session_state.page == "今日":
        page_today()
    else:
        page_history()


if __name__ == "__main__":
    main()

