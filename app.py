"""飲食控制管理系統 Streamlit 入口與角色路由。"""
from __future__ import annotations
import streamlit as st
from services import sheets
from pages.common import init_session
from ui.styles import apply_global_styles
from pages.coach import page_coach_overview, page_coach_student_detail, page_coach_student_history
from pages.student import (
    page_history, page_log_meal, page_login, page_personal, page_tdee,
    page_tdee_questionnaire, page_training, page_weight,
)
def main() -> None:

    st.set_page_config(page_title="飲食控制管理系統", layout="wide")

    apply_global_styles()

    init_session()

    if not st.session_state.user_id:

        page_login()

        return

    role = st.session_state.get("role", "student")

    is_coach = role in ("coach", "admin")

    coach_pages = ["學員狀態", "學員歷史"]

    student_pages = ["個人", "記錄飲食", "歷史", "體重記錄", "訓練記錄", "TDEE", "TDEE 問卷"]

    if is_coach:
        _available_pages = list(coach_pages) + ["學員資料"]
    else:
        _available_pages = list(student_pages)

    if st.session_state.page not in _available_pages:
        st.session_state.page = "學員狀態" if is_coach else "個人"

    # ----- 暫時定義 page 以維持向下相容 -----
    # ----- 路由：直接使用 st.session_state.page（Stage 2-6 簡化） -----


    if is_coach:

        if st.session_state.page == "學員狀態":

            page_coach_overview()

        elif st.session_state.page == "學員資料":

            page_coach_student_detail()

        elif st.session_state.page == "學員歷史":
            page_coach_student_history()
    else:

        if st.session_state.page not in ["TDEE 問卷", "個人"]:

            goals_check = sheets.get_user_goals(st.session_state.user_id)

            if goals_check.get("bmr", 0) <= 0 or goals_check.get("calorie", 0) <= 0:

                st.warning("請先設定營養目標")

                if st.button("前往 TDEE 問卷"):

                    st.session_state.page = "TDEE 問卷"

                    st.rerun()

                return

        if st.session_state.page == "個人":

            page_personal()

        elif st.session_state.page == "記錄飲食":

            page_log_meal()

        elif st.session_state.page == "歷史":

            page_history()

        elif st.session_state.page == "體重記錄":

            page_weight()

        elif st.session_state.page == "訓練記錄":

            page_training()

        elif st.session_state.page == "TDEE":

            page_tdee()

        elif st.session_state.page == "TDEE 問卷":

            page_tdee_questionnaire()




    # ==========================================
    # 底部導航 - 角色自適應版（教練 2 顆、學員 7 顆）
    # ==========================================
    if is_coach:
        _nav_items = [
            ("學員狀態", "👤"),
            ("學員歷史", "📅"),
        ]
        _pad_l, _nav_outer, _pad_r = st.columns([3, 1, 3])
    else:
        _nav_items = [
            ("個人", "👤"),
            ("記錄飲食", "🍴"),
            ("歷史", "🕐"),
            ("體重記錄", "⚖️"),
            ("訓練記錄", "🏋️"),
            ("TDEE", "📊"),
            ("TDEE 問卷", "📋"),
        ]
        _pad_l, _nav_outer, _pad_r = st.columns([1, 7, 1])

    with _nav_outer:
        _btn_cols = st.columns(len(_nav_items))
        for _i, (_page_name, _emoji) in enumerate(_nav_items):
            with _btn_cols[_i]:
                if st.button(_emoji, key=f"nav_{_page_name}", help=_page_name):
                    st.session_state.page = _page_name
                    st.rerun()


    # ==========================================
if __name__ == "__main__":

    main()

