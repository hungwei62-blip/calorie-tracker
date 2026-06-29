"""\u4eba\u5de5\u667a\u80fd\u4eba\u54e1\u591a\u4eba\u71b1\u91cf\u8207\u98f2\u6c34\u8a18\u9304 Web App\u3002

\u4f9d\u64da\u300a\u5c08\u6848\u958b\u767c\u9700\u6c42\u66f8\u300b\uff0c\u4f7f\u7528 Streamlit \u55ae\u9801\u5e0c\u67b6\u69cb + Gemini 2.5 Flash + Google Sheets + Firebase Storage\u3002
"""

from __future__ import annotations

import io
from datetime import date, datetime, timedelta

import streamlit as st
from PIL import Image

from services import auth, firebase, gemini, metrics, sheets


MEAL_TYPES = ["\u65e9\u9910", "\u5348\u9910", "\u665a\u9910", "\u5c0f\u9ede", "\u98f2\u6c34"]


def init_session() -> None:
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "pending_analysis" not in st.session_state:
        st.session_state.pending_analysis = None
    if "pending_meal_type" not in st.session_state:
        st.session_state.pending_meal_type = None


def page_login() -> None:
    st.title("🍱 \u4eba\u5de5\u667a\u80fd\u591a\u4eba\u71b1\u91cf\u8a18\u9304")
    st.caption("\u4f7f\u7528 Gemini 2.5 Flash \u4ee5 Google Sheets \u4f5c\u70ba\u500b\u4eba\u4ee5\u53ca\u8a18\u9304\u4e2d\u5fc3\u3002")

    tab_login, tab_register = st.tabs(["\u767b\u5165", "\u8a3b\u518a"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("\u5e33\u865f")
            password = st.text_input("\u5bc6\u78bc", type="password")
            submitted = st.form_submit_button("\u767b\u5165", use_container_width=True)
        if submitted:
            if not username or not password:
                st.error("\u8acb\u586b\u5165\u5e33\u865f\u8207\u5bc6\u78bc")
                return
            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error(f"\u8b80\u53d6\u4f7f\u7528\u8005\u8868\u5931\u6557: {exc}")
                return
            user = auth.find_user(rows, username)
            if not user or not auth.verify_password(password, user.get("password_hash", "")):
                st.error("\u5e33\u865f\u6216\u5bc6\u78bc\u4e0d\u6b63\u78ba")
                return
            st.session_state.user_id = user["user_id"]
            st.session_state.username = user["username"]
            st.success(f"\u6b61\u8fce\u56de\u4f86\uff0c{user['username']}")
            st.rerun()

    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("\u65b0\u5e33\u865f")
            new_pw = st.text_input("\u5bc6\u78bc", type="password")
            new_pw2 = st.text_input("\u78ba\u8a8d\u5bc6\u78bc", type="password")
            submitted = st.form_submit_button("\u8a3b\u518a", use_container_width=True)
        if submitted:
            if not new_user or not new_pw:
                st.error("\u5e33\u865f\u8207\u5bc6\u78bc\u4e0d\u53ef\u4ee5\u662f\u7a7a")
                return
            if new_pw != new_pw2:
                st.error("\u5169\u6b21\u5bc6\u78bc\u4e0d\u4e00\u81f4")
                return
            if len(new_pw) < 6:
                st.error("\u5bc6\u78bc\u9577\u5ea6\u9700\u4ee5\u516d\u500b\u5b57\u5143\u4ee5\u4e0a")
                return
            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error(f"\u9023\u7dda Sheets \u5931\u6557: {exc}")
                return
            if auth.find_user(rows, new_user):
                st.error("\u5e33\u865f\u5df2\u88ab\u4f7f\u7528")
                return
            try:
                user_id = auth.make_user_id()
                pw_hash = auth.hash_password(new_pw)
                sheets.append_user(
                    user_id=user_id,
                    username=new_user.strip(),
                    password_hash=pw_hash,
                    created_at=auth.now_iso(),
                    goals={},  # \u4f7f\u7528\u9810\u8a2d\u76ee\u6a19
                )
            except Exception as exc:
                st.error(f"\u8a3b\u518a\u5931\u6557: {exc}")
                return
            st.session_state.user_id = user_id
            st.session_state.username = new_user.strip()
            st.success("\u8a3b\u518a\u6210\u529f\uff0c\u81ea\u52d5\u767b\u5165")
            st.rerun()


def page_logout_sidebar() -> None:
    with st.sidebar:
        st.write(f"👤 {st.session_state.username}")
        if st.button("\u767b\u51fa", use_container_width=True):
            for k in ("user_id", "username", "pending_analysis", "pending_meal_type"):
                st.session_state[k] = None
            st.rerun()


def _run_analysis(image_bytes: bytes | None, content_type: str | None, text: str) -> dict:
    if image_bytes is not None:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return gemini.analyze_image(img)
    return gemini.analyze_text(text)


def _upload_image_safely(image_bytes: bytes, content_type: str, user_id: str) -> str:
    try:
        return firebase.upload_image(image_bytes, content_type, user_id)
    except Exception as exc:
        st.warning(f"\u7167\u7247\u4e0a\u50b3\u5931\u6557 ({exc})\uff0c\u5c07\u4ee5\u7a7a\u4f86\u7e7c\u7e8c\u3002\u8a18\u9304\u4ecd\u6703\u4fdd\u7559\u3002")
        return ""


def page_log_meal() -> None:
    st.header("📝 \u8a18\u4e00\u9910")

    if st.session_state.pending_analysis is None:
        st.subheader("\u9078\u64c7\u9910\u5225")
        cols = st.columns(len(MEAL_TYPES))
        for col, meal in zip(cols, MEAL_TYPES):
            if col.button(meal, key=f"meal_{meal}", use_container_width=True):
                st.session_state.pending_meal_type = meal
                st.rerun()

    if st.session_state.pending_meal_type and st.session_state.pending_analysis is None:
        meal = st.session_state.pending_meal_type
        st.subheader(f"\u8a18\u9304: {meal}")
        mode = st.radio(
            "\u8f38\u5165\u65b9\u5f0f",
            ["📷 \u62cd\u7167", "🖼\ufe0f \u5f9e\u5716\u5eab\u4e0a\u50b3", "\u270d\ufe0f \u624b\u6253\u6587\u5b57"],
            horizontal=True,
        )
        image_bytes: bytes | None = None
        content_type: str | None = None
        text: str = ""
        with st.form("input_form"):
            if mode == "📷 \u62cd\u7167":
                shot = st.camera_input("\u62cd\u7167")
                if shot is not None:
                    image_bytes = shot.getvalue()
                    content_type = shot.type or "image/jpeg"
            elif mode == "🖼\ufe0f \u5f9e\u5716\u5eab\u4e0a\u50b3":
                upload = st.file_uploader("\u4e0a\u50b3\u7167\u7247", type=["jpg", "jpeg", "png", "webp"])
                if upload is not None:
                    image_bytes = upload.getvalue()
                    content_type = upload.type or "image/jpeg"
            else:
                text = st.text_area("\u98df\u7269\u63cf\u8ff0", placeholder="\u4f8b\u5982\uff1a\u4e00\u500b\u4fbf\u7576\u542b\u6eff\u9eb5\u9eb5\u3001\u9d3b\u8089\u3001\u4e09\u5f0f\u9752\u83dc")
            send = st.form_submit_button("\u9001\u51fa\u5206\u6790", use_container_width=True)
        if send:
            if image_bytes is None and not text.strip():
                st.error("\u8acb\u63d0\u4f9b\u7167\u7247\u6216\u6587\u5b57\u63cf\u8ff0")
                return
            with st.spinner("Gemini \u5206\u6790\u4e2d..."):
                try:
                    result = _run_analysis(image_bytes, content_type, text)
                except Exception as exc:
                    st.error(f"\u5206\u6790\u5931\u6557: {exc}")
                    return
            st.session_state.pending_analysis = {
                "raw": result,
                "image_bytes": image_bytes,
                "content_type": content_type,
            }
            st.rerun()
        if st.button("\u2190 \u91cd\u9078\u9910\u5225"):
            st.session_state.pending_meal_type = None
            st.rerun()
        return

    # \u5206\u6790\u7d50\u679c\u4ee5\u53ca\u4efd\u6578\u7ba1\u7406
    # 保護: 未選餐別亦無分析結果時 (如剛登入), 避免 KeyError
    if not st.session_state.pending_meal_type or st.session_state.pending_analysis is None:
        return

    meal = st.session_state.pending_meal_type
    pending = st.session_state.pending_analysis
    raw: dict = pending["raw"]

    st.subheader(f"\u5206\u6790\u7d50\u679c: {meal}")
    st.markdown(f"**\u98df\u7269\u6458\u8981**\uff1a{raw.get('food_summary', '')}")

    portion = st.number_input(
        "\u4efd\u6578 (\u9810\u8a2d 1.0 = \u4e00\u6b63\u4efd\uff0c0.5 = \u4e00\u534a\uff0c1.5 = \u4e00\u6b21\u5403 1.5 \u500b\u4fbf\u7576\u90a3\u9ebc\u591a)",
        min_value=0.0,
        max_value=10.0,
        value=1.0,
        step=0.1,
    )

    water_ml = st.number_input(
        "飲水量 (ml)。若本餐不含飲料，請填 0；難以估算的飲料可以不填。",
        min_value=0,
        max_value=5000,
        value=0,
        step=50,
    )

    final = {
        "calorie": float(raw.get("calories", 0) or 0) * portion,
        "protein": float(raw.get("protein", 0) or 0) * portion,
        "carb": float(raw.get("carb", 0) or 0) * portion,
        "fat": float(raw.get("fat", 0) or 0) * portion,
        "water_ml": water_ml,  # 使用者手動輸入，不再以 Gemini 回傳為主
    }

    cols = st.columns(5)
    for col, (key, label, unit) in zip(cols, metrics.METRIC_FIELDS):
        with col:
            val = final["water_ml" if key == "water" else key]
            st.metric(label, f"{val:.1f} {unit}")

    cols2 = st.columns(2)
    if cols2[0].button("\u270d\ufe0f \u91cd\u65b0\u7de8\u8f2f\u63cf\u8ff0", use_container_width=True):
        st.session_state.pending_analysis = None
        st.rerun()
    if cols2[1].button("\u2705 \u78ba\u8a8d\u9001\u51fa", use_container_width=True, type="primary"):
        image_url = ""
        if pending.get("image_bytes") and pending.get("content_type"):
            image_url = _upload_image_safely(pending["image_bytes"], pending["content_type"], st.session_state.user_id)
        try:
            sheets.append_record(
                timestamp=auth.now_iso(),
                user_id=st.session_state.user_id,
                meal_type=meal,
                food_summary=raw.get("food_summary", ""),
                calories=final["calorie"],
                protein=final["protein"],
                carb=final["carb"],
                fat=final["fat"],
                water_ml=final["water_ml"],
                image_url=image_url,
                portion=portion,
            )
        except Exception as exc:
            st.error(f"\u5beb\u5165 Sheets \u5931\u6557: {exc}")
            return
        st.success("\u5df2\u4fdd\u7559\u8a18\u9304")
        st.session_state.pending_analysis = None
        st.session_state.pending_meal_type = None
        st.rerun()


def page_today() -> None:
    st.header("📅 \u4eca\u65e5\u9032\u5ea6")
    try:
        records = sheets.get_records(st.session_state.user_id)
        goals = sheets.get_user_goals(st.session_state.user_id)
    except Exception as exc:
        st.error(f"\u8b80\u53d6\u8a18\u9304\u5931\u6557: {exc}")
        return

    today = date.today()
    today_records = metrics.filter_records(records, today, today)
    totals = metrics.sum_totals(today_records)

    fields = [
        ("\u71b1\u91cf", "calorie", "kcal"),
        ("\u86cb\u767d\u8cea", "protein", "g"),
        ("\u7cd6\u985e", "carb", "g"),
        ("\u8102\u8cea", "fat", "g"),
        ("\u98f2\u6c34\u91cf", "water", "ml"),
    ]
    cols = st.columns(5)
    for col, (label, key, unit) in zip(cols, fields):
        with col:
            cur = getattr(totals, key)
            goal = goals.get(key, 0)
            st.metric(label, f"{cur:.0f} / {goal:.0f} {unit}")

    st.subheader("\u8a08\u7b97\u9032\u5ea6")
    for label, key, _ in fields:
        cur = getattr(totals, key)
        goal = goals.get(key, 0) or 1
        ratio = min(max(cur / goal, 0.0), 1.0)
        st.write(f"{label}\uff1a{cur:.0f} / {goals.get(key, 0):.0f}")
        st.progress(ratio)

    st.subheader("\u4eca\u65e5\u660e\u7d30")
    if not today_records:
        st.info("\u4eca\u5929\u9084\u6c92\u6709\u8a18\u9304")
    else:
        rows = [
            {
                "\u6642\u9593": r.get("timestamp", "")[:16],
                "\u9910\u5225": r.get("meal_type", ""),
                "\u6458\u8981": r.get("food_summary", ""),
                "\u71b1\u91cf": float(r.get("calories", 0) or 0),
                "\u86cb\u767d": float(r.get("protein", 0) or 0),
                "\u7cd6": float(r.get("carb", 0) or 0),
                "\u8102": float(r.get("fat", 0) or 0),
                "\u98f2\u6c34": float(r.get("water_ml", 0) or 0),
            }
            for r in sorted(today_records, key=lambda r: r.get("timestamp", ""))
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)


def page_history() -> None:
    st.header("📊 \u6b77\u53f2\u8207\u9031\u9032\u5ea6")
    try:
        records = sheets.get_records(st.session_state.user_id)
        goals = sheets.get_user_goals(st.session_state.user_id)
    except Exception as exc:
        st.error(f"\u8b80\u53d6\u8a18\u9304\u5931\u6557: {exc}")
        return

    today = date.today()
    default_start = metrics.week_start(today)
    col_a, col_b = st.columns(2)
    with col_a:
        start = st.date_input("\u8d77\u59cb\u65e5", value=default_start)
    with col_b:
        end = st.date_input("\u7d50\u675f\u65e5", value=today)

    in_range = metrics.filter_records(records, start, end)
    if not in_range:
        st.info("\u9019\u500b\u5340\u9593\u5167\u6c92\u6709\u8a18\u9304")
        return

    # \u9031\u7d71\u8a08 (\u4f7f\u7528\u4f7f\u7528\u8005\u8a2d\u5b9a\u7684\u5340\u9593\u8d77\u59cb\u65e5\u4f5c\u70ba\u4e00\u9031\u4e00\u8d77\u9ede\uff0c\u4f46\u53ea\u7d71\u8a08\u300c\u9031\u76ee\u6a19\u300d\u4e0a\u9650)
    ws = metrics.week_start(start)
    we = ws + timedelta(days=6)
    week_records = metrics.filter_records(in_range, ws, min(we, end))
    week_totals = metrics.sum_totals(week_records)
    days_passed = (min(end, we) - ws).days + 1

    st.subheader(f"\u672c\u9031\u7d71\u8a08 ({ws} \u81f3 {min(end, we)}\uff0c\u5171 {days_passed} \u5929)")
    cols = st.columns(5)
    field_def = [
        ("\u71b1\u91cf", "calorie", "kcal"),
        ("\u86cb\u767d\u8cea", "protein", "g"),
        ("\u7cd6\u985e", "carb", "g"),
        ("\u8102\u8cea", "fat", "g"),
        ("\u98f2\u6c34\u91cf", "water", "ml"),
    ]
    statuses: dict[str, tuple[str, float]] = {}
    for col, (label, key, unit) in zip(cols, field_def):
        cur = getattr(week_totals, key)
        goal = goals.get(key, 0) * days_passed
        with col:
            st.metric(label, f"{cur:.0f} / {goal:.0f} {unit}")
        ratio = cur / goal if goal else 0
        statuses[key] = metrics.classify(ratio)

    # \u72c0\u614b\u6a19\u7c64
    for label, key, _ in field_def:
        status, pct = statuses[key]
        diff = metrics.format_pct(pct)
        msg = f"**{label}**\uff1a{status} ({diff})"
        if status == "\u9054\u6210":
            st.success(msg)
        elif status == "\u672a\u9054":
            st.warning(msg)
        else:
            st.error(msg)

    # \u8d70\u52e2\u5716
    st.subheader("\u6bcf\u65e5\u8d70\u52e2")
    by_day: dict[date, metrics.Totals] = {}
    for r in in_range:
        d = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).date() if r.get("timestamp") else None
        if d is None:
            continue
        t = by_day.setdefault(d, metrics.Totals())
        t.calorie += float(r.get("calories", 0) or 0)
        t.protein += float(r.get("protein", 0) or 0)
        t.carb += float(r.get("carb", 0) or 0)
        t.fat += float(r.get("fat", 0) or 0)
        t.water += float(r.get("water_ml", 0) or 0)
    days_sorted = sorted(by_day.keys())
    chart_data = {
        "\u71b1\u91cf": [by_day[d].calorie for d in days_sorted],
        "\u86cb\u767d\u8cea": [by_day[d].protein for d in days_sorted],
        "\u7cd6\u985e": [by_day[d].carb for d in days_sorted],
        "\u8102\u8cea": [by_day[d].fat for d in days_sorted],
        "\u98f2\u6c34\u91cf": [by_day[d].water for d in days_sorted],
    }
    st.line_chart({"x": [d.isoformat() for d in days_sorted], **chart_data}, x="x")

    st.subheader("\u8a18\u9304\u660e\u7d30")
    rows = [
        {
            "\u65e5\u671f": r.get("timestamp", "")[:10],
            "\u9910\u5225": r.get("meal_type", ""),
            "\u6458\u8981": r.get("food_summary", ""),
            "\u71b1\u91cf": float(r.get("calories", 0) or 0),
            "\u86cb\u767d": float(r.get("protein", 0) or 0),
            "\u7cd6": float(r.get("carb", 0) or 0),
            "\u8102": float(r.get("fat", 0) or 0),
            "\u98f2\u6c34": float(r.get("water_ml", 0) or 0),
            "\u4efd\u6578": float(r.get("portion", 1) or 1),
        }
        for r in sorted(in_range, key=lambda r: r.get("timestamp", ""), reverse=True)
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="\u4eba\u5de5\u667a\u80fd\u71b1\u91cf\u8a18\u9304", page_icon="🍱", layout="wide")
    init_session()

    if not st.session_state.user_id:
        page_login()
        return

    page_logout_sidebar()
    tab1, tab2, tab3 = st.tabs(["📝 \u8a18\u4e00\u9910", "📅 \u4eca\u65e5", "📊 \u6b77\u53f2"])
    with tab1:
        page_log_meal()
    with tab2:
        page_today()
    with tab3:
        page_history()


if __name__ == "__main__":
    main()
else:
    # Streamlit runs app.py as module
    main()


