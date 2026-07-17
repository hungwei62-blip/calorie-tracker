"""角色自適應的固定底部導覽。"""
from __future__ import annotations

from dataclasses import dataclass, replace

import streamlit as st


@dataclass(frozen=True)
class NavigationItem:
    """單一底部導覽項目。"""

    key: str
    page: str
    label: str
    help_text: str
    active: bool = False


_COACH_ITEMS = (
    NavigationItem("students", "學員狀態", "👤 學員", "查看學員狀態"),
    NavigationItem("student_history", "學員歷史", "📅 歷史", "查看學員歷史"),
)

_STUDENT_ITEMS = (
    NavigationItem("personal", "個人", "👤 個人", "個人首頁"),
    NavigationItem("meal", "記錄飲食", "🍴 飲食", "記錄飲食"),
    NavigationItem("history", "歷史", "🕐 歷史", "飲食歷史"),
)


def get_navigation_items(role: str, current_page: str) -> tuple[NavigationItem, ...]:
    """回傳角色可用的導覽項目，並標記目前所在頁面。"""
    is_manager = (role or "student").strip().lower() in ("coach", "admin")
    items = _COACH_ITEMS if is_manager else _STUDENT_ITEMS
    active_page = "學員狀態" if is_manager and current_page == "學員資料" else current_page
    return tuple(replace(item, active=item.page == active_page) for item in items)


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
                    type="primary" if item.active else "secondary",
                    width="stretch",
                ):
                    st.session_state.page = item.page
                    st.rerun()
