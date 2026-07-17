from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from pages import student as student_pages


class _SessionState(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class _Tab:
    def __init__(self, is_open: bool):
        self.open = is_open

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _TabsStreamlit:
    def __init__(self, active_index: int):
        self.active_index = active_index
        self.session_state = _SessionState()
        self.tabs_call = None
        self.headers = []

    def header(self, label):
        self.headers.append(label)

    def tabs(self, labels, **kwargs):
        self.tabs_call = (tuple(labels), kwargs)
        return tuple(_Tab(index == self.active_index) for index in range(len(labels)))


@pytest.mark.parametrize(
    ("active_index", "expected_renderer"),
    [(0, "meal"), (1, "weight"), (2, "training")],
)
def test_daily_records_only_renders_active_tab(monkeypatch, active_index, expected_renderer):
    fake_st = _TabsStreamlit(active_index)
    rendered = []

    monkeypatch.setattr(student_pages, "st", fake_st)
    monkeypatch.setattr(student_pages, "_render_meal_records", lambda: rendered.append("meal"))
    monkeypatch.setattr(student_pages, "_render_weight_records", lambda: rendered.append("weight"))
    monkeypatch.setattr(student_pages, "_render_training_records", lambda: rendered.append("training"))

    student_pages.page_log_meal()

    labels, kwargs = fake_st.tabs_call
    assert labels == student_pages.DAILY_RECORD_TABS
    assert kwargs == {
        "default": "🍴 飲食",
        "key": "daily_record_tab",
        "on_change": "rerun",
    }
    assert rendered == [expected_renderer]


def test_weight_shortcut_targets_integrated_weight_tab(monkeypatch):
    fake_st = _TabsStreamlit(active_index=0)
    monkeypatch.setattr(student_pages, "st", fake_st)

    student_pages.open_daily_record_tab("⚖️ 體重")

    assert fake_st.session_state.page == "記錄飲食"
    assert fake_st.session_state.daily_record_tab_target == "⚖️ 體重"


def test_unknown_daily_record_tab_is_rejected(monkeypatch):
    fake_st = _TabsStreamlit(active_index=0)
    monkeypatch.setattr(student_pages, "st", fake_st)

    with pytest.raises(ValueError):
        student_pages.open_daily_record_tab("未知")


def test_requested_weight_tab_is_selected_by_real_streamlit_tabs():
    records_app = AppTest.from_string(
        """
import streamlit as st
from pages import student as student_pages

st.session_state.setdefault("daily_record_tab_target", "⚖️ 體重")
student_pages._render_meal_records = lambda: st.write("MEAL_RENDERED")
student_pages._render_weight_records = lambda: st.write("WEIGHT_RENDERED")
student_pages._render_training_records = lambda: st.write("TRAINING_RENDERED")
student_pages.page_log_meal()
"""
    ).run(timeout=20)

    assert not records_app.exception
    assert [tab.label for tab in records_app.tabs] == list(student_pages.DAILY_RECORD_TABS)
    assert [item.value for item in records_app.markdown] == ["WEIGHT_RENDERED"]
    assert records_app.session_state["daily_record_tab"] == "⚖️ 體重"
