from __future__ import annotations

import inspect
import pytest
from streamlit.testing.v1 import AppTest

from pages import student as student_pages
from ui import styles


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

    def container(self, **_kwargs):
        return _Tab(True)

    def tabs(self, labels, **kwargs):
        self.tabs_call = (tuple(labels), kwargs)
        return tuple(_Tab(index == self.active_index) for index in range(len(labels)))


@pytest.mark.parametrize(
    ("active_index", "expected_renderer"),
    [(0, "food"), (1, "water"), (2, "training"), (3, "weight")],
)
def test_daily_records_only_renders_active_tab(monkeypatch, active_index, expected_renderer):
    fake_st = _TabsStreamlit(active_index)
    rendered = []

    monkeypatch.setattr(student_pages, "st", fake_st)
    monkeypatch.setattr(student_pages, "_render_water_records", lambda: rendered.append("water"))
    monkeypatch.setattr(student_pages, "_render_food_records", lambda: rendered.append("food"))
    monkeypatch.setattr(student_pages, "_render_training_records", lambda: rendered.append("training"))
    monkeypatch.setattr(student_pages, "_render_weight_records", lambda: rendered.append("weight"))

    student_pages.page_log_meal()

    labels, kwargs = fake_st.tabs_call
    assert labels == student_pages.DAILY_RECORD_TABS
    assert kwargs == {
        "default": "食物",
        "key": "daily_record_tab",
        "on_change": "rerun",
    }
    assert rendered == [expected_renderer]


def test_weight_shortcut_targets_integrated_weight_tab(monkeypatch):
    fake_st = _TabsStreamlit(active_index=0)
    monkeypatch.setattr(student_pages, "st", fake_st)

    student_pages.open_daily_record_tab("⚖️ 體重")

    assert fake_st.session_state.page == "記錄飲食"
    assert fake_st.session_state.daily_record_tab_target == "體重"


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
student_pages._render_water_records = lambda: st.write("WATER_RENDERED")
student_pages._render_food_records = lambda: st.write("FOOD_RENDERED")
student_pages._render_weight_records = lambda: st.write("WEIGHT_RENDERED")
student_pages._render_training_records = lambda: st.write("TRAINING_RENDERED")
student_pages.page_log_meal()
"""
    ).run(timeout=20)

    assert not records_app.exception
    assert [tab.label for tab in records_app.tabs] == list(student_pages.DAILY_RECORD_TABS)
    assert [item.value for item in records_app.markdown] == ["WEIGHT_RENDERED"]
    assert records_app.session_state["daily_record_tab"] == "體重"


def test_food_and_water_records_use_new_record_categories(monkeypatch):
    appended = []
    monkeypatch.setattr(student_pages.sheets, "append_record", lambda **kwargs: appended.append(kwargs))
    monkeypatch.setattr(student_pages, "_clear_analysis_cache", lambda: None)

    student_pages._append_water_record("student-1", 350)
    student_pages._append_food_record("student-1", "手動紀錄", 420, 28)

    assert appended[0] == {
        "timestamp": appended[0]["timestamp"],
        "user_id": "student-1",
        "meal_type": "飲水",
        "food_summary": "飲水",
        "calories": 0,
        "protein": 0,
        "carb": 0,
        "fat": 0,
        "water_ml": 350.0,
        "image_url": "",
        "portion": 1,
    }
    assert appended[1]["meal_type"] == "食物"
    assert appended[1]["food_summary"] == "手動紀錄"
    assert (appended[1]["calories"], appended[1]["protein"]) == (420.0, 28.0)
    assert (appended[1]["carb"], appended[1]["fat"], appended[1]["water_ml"]) == (0, 0, 0)
    assert appended[1]["image_url"] == ""


@pytest.mark.parametrize(
    ("writer", "args"),
    [
        (student_pages._append_water_record, ("student-1", 0)),
        (student_pages._append_water_record, ("student-1", -100)),
        (student_pages._append_food_record, ("student-1", "手動紀錄", 0, 0)),
        (student_pages._append_food_record, ("student-1", "手動紀錄", -1, 10)),
    ],
)
def test_empty_daily_records_are_rejected(writer, args):
    with pytest.raises(ValueError):
        writer(*args)


def test_daily_record_page_uses_plain_labels_and_scoped_card_styles():
    source = inspect.getsource(student_pages.page_log_meal)
    assert student_pages.DAILY_RECORD_TABS == ("食物", "飲水", "訓練", "體重")
    assert 'st.header("日常紀錄")' in source
    for emoji in ("🍴", "⚖️", "🏋️", "📝"):
        assert emoji not in source

    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-daily_record_page" in value
    )
    assert '.st-key-daily_record_page [data-baseweb="tab-list"]' in stylesheet
    assert '.block-container:has(.st-key-daily_record_page)' in stylesheet
    assert '[data-testid="stMainBlockContainer"]:has(.st-key-daily_record_page)' in stylesheet
    assert stylesheet.count(
        '.main .block-container:has(.st-key-daily_record_page),'
    ) == 2
    assert 'padding-bottom: 48px !important;' not in stylesheet
    assert 'background: #f7f7f7 !important;' in stylesheet
    assert 'border-radius: 999px !important;' in stylesheet
    assert '.st-key-daily_record_page [data-testid="stForm"]' in stylesheet
    assert 'min-height: 58px !important;' in stylesheet
    assert 'min-height: 42px !important;' in stylesheet
    assert 'min-height: 46px !important;' in stylesheet
    assert 'overflow: visible !important;' in stylesheet
    assert '.st-key-daily_record_page div.stButton > button' in stylesheet
    assert 'background: #ffffff !important;' in stylesheet
    assert 'border-radius: 10px !important;' in stylesheet
    assert '.st-key-daily_record_page button [data-testid="stMarkdownContainer"]' in stylesheet
    assert 'background: transparent !important;' in stylesheet


def test_food_input_defaults_to_manual_mode():
    source = inspect.getsource(student_pages)
    food_renderer = source[source.index("def _render_food_records"):]
    assert '("照片辨識", "手動輸入")' in food_renderer
    assert 'default="手動輸入"' in food_renderer
