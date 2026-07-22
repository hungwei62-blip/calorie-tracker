from __future__ import annotations

import inspect
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from pages import student as student_pages
from ui import camera as camera_ui
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
    monkeypatch.setattr(
        student_pages,
        "current_auth_context",
        lambda: student_pages.application.AuthContext("student-1", "student"),
    )

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
    assert '.st-key-daily_record_page [data-testid="stTabContent"]:has(.st-key-food_record_panel)' in stylesheet
    assert '.st-key-food_record_panel > div[data-testid="stVerticalBlock"]' in stylesheet
    assert '.block-container:has(.st-key-food_record_panel)' in stylesheet
    assert 'padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px))' in stylesheet


def test_daily_record_palette_persists_across_all_tabs_and_ctas():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-daily_record_page" in value
    )
    palette_start = stylesheet.index(
        "/* ===== 學員日常紀錄：四分頁共用霧藍奶杏色票 ===== */"
    )
    palette_end = stylesheet.index("@media (max-width: 768px)", palette_start)
    palette = stylesheet[palette_start:palette_end]

    assert ".stApp:has(.st-key-daily_record_page)" in palette
    assert ".st-key-daily_record_page:has(.st-key-food_record_panel)" not in palette
    assert "--daily-record-primary-text: #27303D;" in palette
    assert "--daily-record-secondary-text: #7C8798;" in palette
    assert "--daily-record-tab-background: #EEF3F8;" in palette
    assert "--daily-record-tab-selected: #F5E7DF;" in palette
    assert "--daily-record-tab-selected-text: #B97C64;" in palette
    assert "--daily-record-border: #E7EDF3;" in palette
    assert "--daily-record-cta-background: #F6E8DE;" in palette
    assert "--daily-record-cta-text: #B88470;" in palette
    assert ".st-key-food_input_mode" in palette
    assert ".st-key-food_photo_source" in palette
    assert ".st-key-training_types" in palette
    assert ".st-key-analyze_food_photo" in palette
    assert ".st-key-save_analyzed_food" in palette
    assert ".st-key-cancel_analyzed_food" in palette
    cta_selector = (
        '.st-key-daily_record_page div[data-testid="stFormSubmitButton"] '
        'button[data-testid^="stBaseButton"]'
    )
    assert cta_selector in palette
    assert "background: #F6E8DE !important;" in palette
    assert "background-color: #F6E8DE !important;" in palette
    assert "background-image: none !important;" in palette
    assert ":hover" in palette
    assert ":active" in palette
    assert ":focus-visible" in palette
    assert ":disabled" in palette
    original_cta_selector = (
        '.st-key-daily_record_page div[data-testid="stFormSubmitButton"] button,'
    )
    assert stylesheet.index(cta_selector) > stylesheet.index(original_cta_selector)
    assert inspect.getsource(student_pages).count(
        'st.form_submit_button("儲存'
    ) == 4


def test_camera_component_replaces_mobile_only_native_switch():
    source = inspect.getsource(student_pages._selected_food_image_bytes)

    assert "camera_capture(" in source
    assert "st.camera_input" not in source
    assert "切換前後鏡頭" in camera_ui._CAMERA_HTML
    assert "navigator.mediaDevices.enumerateDevices()" in camera_ui._CAMERA_JS
    assert 'device.kind === "videoinput"' in camera_ui._CAMERA_JS
    assert "state.devices.length < 2" in camera_ui._CAMERA_JS
    assert "getTracks().forEach(track => track.stop())" in camera_ui._CAMERA_JS
    assert "background: #f6e8de" in camera_ui._CAMERA_CSS.lower()


def test_food_input_defaults_to_manual_mode():
    source = inspect.getsource(student_pages)
    food_renderer = source[source.index("def _render_food_records"):]
    assert '("照片辨識", "手動輸入")' in food_renderer
    assert 'default="手動輸入"' in food_renderer
    assert 'key="food_record_panel"' in food_renderer


def test_daily_record_sections_remove_duplicate_headings_and_simplify_weight():
    source = inspect.getsource(student_pages)
    water_renderer = source[source.index("def _render_water_records"):source.index("def _selected_food_image_bytes")]
    food_renderer = source[source.index("def _render_food_records"):source.index("def _render_training_records")]
    weight_renderer = source[
        source.index("def _render_weight_records"):
        source.index("def _weight_history_summary")
    ]

    assert 'st.subheader("飲水")' not in water_renderer
    assert "water_form_version" in water_renderer
    assert "value=None" in water_renderer
    assert "water_ml or 0" in water_renderer
    assert 'st.subheader("食物")' not in food_renderer
    assert '體重趨勢' not in weight_renderer
    assert 'get_weight_records' not in weight_renderer
    assert 'line_chart' not in weight_renderer
    assert 'value=None, step=0.1' in weight_renderer
    assert "weight_form_version" in weight_renderer
    assert '_set_record_success("體重")' in weight_renderer


@pytest.mark.parametrize(
    ("selected", "expected"),
    [
        (["重量訓練"], [("重量訓練", "strength_detail", "重量訓練內容")]),
        (
            ["有氧訓練", "其他"],
            [
                ("有氧訓練", "cardio_detail", "有氧訓練內容"),
                ("其他", "other_detail", "其他訓練內容"),
            ],
        ),
        (
            ["其他", "重量訓練", "有氧訓練"],
            [
                ("重量訓練", "strength_detail", "重量訓練內容"),
                ("有氧訓練", "cardio_detail", "有氧訓練內容"),
                ("其他", "other_detail", "其他訓練內容"),
            ],
        ),
    ],
)
def test_training_selection_maps_to_independent_detail_fields(selected, expected):
    assert student_pages._training_fields_for_types(selected) == expected


def test_training_renderer_uses_multi_select_and_no_duplicate_heading():
    module_source = Path(student_pages.__file__).read_text(encoding="utf-8")
    source = module_source[
        module_source.index("def _render_training_records"):
        module_source.index("def _render_weight_records")
    ]

    assert 'selection_mode="multi"' in source
    assert '"訓練類型 (可複選)"' in source
    assert 'default=[]' in source
    assert 'value=""' in source
    assert '今日已有訓練紀錄，再次儲存將覆蓋原紀錄。' in source
    assert 'st.subheader("訓練")' not in source
    assert 'st.text_input(' in source
    assert 'training_types=selected_types' in source
    assert '本週訓練紀錄' not in source
    assert '本週尚無訓練紀錄' not in source
    assert 'get_training_records' not in source
    assert 'st.dataframe' not in source
    for legacy_field in (
        "training_back", "training_chest", "training_legs",
        "training_core", "training_cardio",
    ):
        assert legacy_field not in source


def test_entering_training_tab_clears_previous_widget_state(monkeypatch):
    fake_st = _TabsStreamlit(active_index=2)
    fake_st.session_state.update({
        "_last_daily_record_tab": "食物",
        "training_types": ["重量訓練"],
        "training_strength_detail": "深蹲 4 組",
        "training_cardio_detail": "跑步 20 分鐘",
        "training_other_detail": "伸展",
    })
    monkeypatch.setattr(student_pages, "st", fake_st)

    assert student_pages._prepare_daily_record_tab("訓練") is True
    for key in student_pages.TRAINING_WIDGET_KEYS:
        assert key not in fake_st.session_state
    assert fake_st.session_state["_last_daily_record_tab"] == "訓練"


def test_training_widget_rerun_keeps_current_inputs(monkeypatch):
    fake_st = _TabsStreamlit(active_index=2)
    fake_st.session_state.update({
        "_last_daily_record_tab": "訓練",
        "training_types": ["重量訓練"],
        "training_strength_detail": "深蹲 4 組",
    })
    monkeypatch.setattr(student_pages, "st", fake_st)

    assert student_pages._prepare_daily_record_tab("訓練") is False
    assert fake_st.session_state["training_types"] == ["重量訓練"]
    assert fake_st.session_state["training_strength_detail"] == "深蹲 4 組"


def test_returning_from_another_page_clears_training_even_if_last_tab_matches(monkeypatch):
    fake_st = _TabsStreamlit(active_index=2)
    fake_st.session_state.update({
        "_entered_daily_record_page": True,
        "_last_daily_record_tab": "訓練",
        "training_types": ["有氧訓練"],
        "training_cardio_detail": "單車 30 分鐘",
    })
    monkeypatch.setattr(student_pages, "st", fake_st)

    assert student_pages._prepare_daily_record_tab("訓練") is True
    assert "training_types" not in fake_st.session_state
    assert "training_cardio_detail" not in fake_st.session_state
