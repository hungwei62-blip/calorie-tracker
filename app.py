"""飲食控制管理系統 Streamlit 入口與角色路由。"""
from __future__ import annotations
import streamlit as st
from services import sheets
from services.observability import configure_logging
from services.security import clear_auth_session, resolve_auth_context, safe_failure_message
from pages.common import init_session
from ui.navigation import render_bottom_navigation
from ui.styles import apply_global_styles
from pages.coach import page_coach_overview, page_coach_student_detail, page_coach_student_history
from pages.student import (
    page_history, page_log_meal, page_login, page_personal, page_tdee,
    page_tdee_questionnaire,
)


LEGACY_STUDENT_RECORD_PAGES = {
    "體重記錄": "體重",
    "訓練記錄": "訓練",
}


def normalize_student_page(page: str) -> tuple[str, str | None]:
    """將舊版獨立紀錄頁導向整合頁及對應分頁。"""
    tab = LEGACY_STUDENT_RECORD_PAGES.get(page)
    return ("記錄飲食", tab) if tab else (page, None)


def track_student_page_entry(current_page: str) -> None:
    """標記真正進入日常紀錄頁的頁面切換，不把一般 rerun 視為重進。"""
    previous_page = st.session_state.get("_last_routed_page")
    st.session_state["_entered_daily_record_page"] = (
        current_page == "記錄飲食" and previous_page != current_page
    )
    st.session_state["_last_routed_page"] = current_page


def main() -> None:

    configure_logging()

    st.set_page_config(page_title="飲食控制管理系統", layout="wide")

    apply_global_styles()

    init_session()

    if not st.session_state.user_id:

        page_login()

        return

    try:
        auth_context = resolve_auth_context(
            str(st.session_state.user_id or ""), sheets.get_users_rows()
        )
    except Exception as exc:
        st.error(safe_failure_message("auth.refresh", exc))
        return
    if auth_context is None:
        clear_auth_session(st.session_state)
        st.warning("登入狀態已失效，請重新登入")
        st.rerun()
        return

    st.session_state.role = auth_context.role
    role = auth_context.role

    is_coach = role in ("coach", "admin")

    coach_pages = ["學員狀態", "學員歷史"]

    student_pages = ["個人", "記錄飲食", "歷史", "TDEE", "TDEE 問卷"]

    if not is_coach:
        normalized_page, target_tab = normalize_student_page(st.session_state.page)
        st.session_state.page = normalized_page
        if target_tab:
            st.session_state.daily_record_tab_target = target_tab

    if is_coach:
        _available_pages = list(coach_pages) + ["學員資料"]
    else:
        _available_pages = list(student_pages)

    if st.session_state.page not in _available_pages:
        st.session_state.page = "學員狀態" if is_coach else "個人"

    if not is_coach:
        track_student_page_entry(st.session_state.page)

    # 先渲染固定導覽，確保頁面警告或提前停止內容時仍可切換頁面。
    render_bottom_navigation(role, st.session_state.page)

    if is_coach:

        if st.session_state.page == "學員狀態":

            page_coach_overview()

        elif st.session_state.page == "學員資料":

            page_coach_student_detail()

        elif st.session_state.page == "學員歷史":
            page_coach_student_history()
    else:
        can_render_page = True

        if st.session_state.page not in ["TDEE 問卷", "個人", "歷史"]:

            goals_check = sheets.get_user_goals(st.session_state.user_id)

            if goals_check.get("bmr", 0) <= 0 or goals_check.get("calorie", 0) <= 0:

                st.warning("請先設定營養目標")

                if st.button("前往 TDEE 問卷"):

                    st.session_state.page = "TDEE 問卷"

                    st.rerun()

                can_render_page = False

        if can_render_page and st.session_state.page == "個人":

            page_personal()

        elif can_render_page and st.session_state.page == "記錄飲食":

            page_log_meal()

        elif can_render_page and st.session_state.page == "歷史":

            page_history()

        elif can_render_page and st.session_state.page == "TDEE":

            page_tdee()

        elif can_render_page and st.session_state.page == "TDEE 問卷":

            page_tdee_questionnaire()
if __name__ == "__main__":

    main()

