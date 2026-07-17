from __future__ import annotations

import pytest

import app
from streamlit.testing.v1 import AppTest

from ui.navigation import get_navigation_items


def test_manager_navigation_has_two_items():
    expected_pages = ["學員狀態", "學員歷史"]

    for role in ("coach", "admin"):
        items = get_navigation_items(role, "學員狀態")
        assert [item.page for item in items] == expected_pages
        assert sum(item.active for item in items) == 1


def test_student_navigation_has_three_mapped_items():
    expected_pages = [
        "個人",
        "記錄飲食",
        "歷史",
    ]
    items = get_navigation_items("student", "個人")

    assert [item.page for item in items] == expected_pages
    assert len({item.key for item in items}) == 3
    assert [item.page for item in items if item.active] == ["個人"]


def test_each_student_page_can_be_selected():
    pages = [item.page for item in get_navigation_items("student", "")]

    for page in pages:
        items = get_navigation_items("student", page)
        assert [item.page for item in items if item.active] == [page]


def test_student_detail_keeps_students_navigation_selected():
    items = get_navigation_items("coach", "學員資料")
    assert [item.page for item in items if item.active] == ["學員狀態"]


def test_rendered_navigation_click_updates_page_and_active_button():
    navigation_app = AppTest.from_string(
        """
import streamlit as st
from ui.navigation import render_bottom_navigation

st.session_state.setdefault("page", "個人")
render_bottom_navigation("student", st.session_state.page)
"""
    ).run(timeout=20)

    assert len(navigation_app.button) == 3
    assert navigation_app.button[0].proto.type == "primary"

    navigation_app.button[1].click().run(timeout=20)

    assert navigation_app.session_state["page"] == "記錄飲食"
    assert navigation_app.button[1].proto.type == "primary"


@pytest.mark.parametrize(
    ("legacy_page", "expected_tab"),
    [
        ("體重記錄", "⚖️ 體重"),
        ("訓練記錄", "🏋️ 訓練"),
    ],
)
def test_legacy_record_pages_redirect_to_daily_records(legacy_page, expected_tab):
    page, tab = app.normalize_student_page(legacy_page)
    assert page == "記錄飲食"
    assert tab == expected_tab


def test_normal_student_page_is_unchanged():
    assert app.normalize_student_page("歷史") == ("歷史", None)


@pytest.mark.parametrize(
    ("legacy_page", "expected_tab"),
    [
        ("體重記錄", "⚖️ 體重"),
        ("訓練記錄", "🏋️ 訓練"),
    ],
)
def test_main_routes_legacy_record_page_to_integrated_page(monkeypatch, legacy_page, expected_tab):
    fake_st = _FakeStreamlit()
    fake_st.session_state.page = legacy_page
    rendered_pages = []
    rendered_navigation = []

    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "apply_global_styles", lambda: None)
    monkeypatch.setattr(app, "init_session", lambda: None)
    monkeypatch.setattr(app.sheets, "get_user_goals", lambda _user_id: {"bmr": 1500, "calorie": 2000})
    monkeypatch.setattr(
        app,
        "render_bottom_navigation",
        lambda role, page: rendered_navigation.append((role, page)),
    )
    monkeypatch.setattr(app, "page_log_meal", lambda: rendered_pages.append("記錄飲食"))

    app.main()

    assert fake_st.session_state.page == "記錄飲食"
    assert fake_st.session_state.daily_record_tab_target == expected_tab
    assert rendered_navigation == [("student", "記錄飲食")]
    assert rendered_pages == ["記錄飲食"]


class _FakeSessionState(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class _FakeStreamlit:
    def __init__(self):
        self.session_state = _FakeSessionState(
            user_id="student_1",
            role="student",
            page="歷史",
        )
        self.warnings = []

    def set_page_config(self, **_kwargs):
        return None

    def warning(self, message):
        self.warnings.append(message)

    def button(self, *_args, **_kwargs):
        return False

    def rerun(self):  # pragma: no cover - button is false in this scenario
        raise AssertionError("不應重新執行")


def test_navigation_renders_when_tdee_goals_are_missing(monkeypatch):
    fake_st = _FakeStreamlit()
    rendered_navigation = []

    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "apply_global_styles", lambda: None)
    monkeypatch.setattr(app, "init_session", lambda: None)
    monkeypatch.setattr(
        app,
        "render_bottom_navigation",
        lambda role, page: rendered_navigation.append((role, page)),
    )
    monkeypatch.setattr(app.sheets, "get_user_goals", lambda _user_id: {"bmr": 0, "calorie": 0})
    monkeypatch.setattr(app, "page_history", lambda: (_ for _ in ()).throw(AssertionError("不應渲染歷史頁")))

    app.main()

    assert rendered_navigation == [("student", "歷史")]
    assert fake_st.warnings == ["請先設定營養目標"]
