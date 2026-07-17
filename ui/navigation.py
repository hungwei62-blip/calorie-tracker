"""角色自適應的固定底部導覽。"""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class NavigationItem:
    """單一底部導覽項目。"""

    key: str
    page: str
    label: str
    icon: str
    help_text: str


_COACH_ITEMS = (
    NavigationItem("students", "學員狀態", "學員", ":material/groups:", "查看學員狀態"),
    NavigationItem(
        "student_history",
        "學員歷史",
        "學員歷史",
        ":material/calendar_month:",
        "查看學員歷史",
    ),
)

_STUDENT_ITEMS = (
    NavigationItem("personal", "個人", "個人", ":material/person:", "個人首頁"),
    NavigationItem("meal", "記錄飲食", "飲食", ":material/restaurant:", "記錄飲食"),
    NavigationItem("history", "歷史", "歷史", ":material/history:", "飲食歷史"),
)


def get_navigation_items(role: str, current_page: str) -> tuple[NavigationItem, ...]:
    """回傳角色可用的導覽項目；目前頁面不影響按鈕外觀。"""
    del current_page
    is_manager = (role or "student").strip().lower() in ("coach", "admin")
    return _COACH_ITEMS if is_manager else _STUDENT_ITEMS


def render_bottom_navigation(role: str, current_page: str) -> None:
    """渲染固定於視窗底部、可水平捲動的角色導覽。"""
    items = get_navigation_items(role, current_page)

    with st.container(key="bottom_navigation", width="content"):
        columns = st.columns(len(items), gap="small")
        for column, item in zip(columns, items):
            with column:
                if st.button(
                    item.label,
                    key=f"bottom_nav_{item.key}",
                    help=item.help_text,
                    type="secondary",
                    icon=item.icon,
                    width="content",
                ):
                    st.session_state.page = item.page
                    st.rerun()
