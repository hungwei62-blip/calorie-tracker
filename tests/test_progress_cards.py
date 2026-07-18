from __future__ import annotations

from datetime import date
import inspect

import pages.student as student_pages
from pages.student import (
    _goal_status,
    _progress_percentage,
    _weight_summary,
    build_calorie_figure,
    build_daily_progress_figure,
)
from streamlit.testing.v1 import AppTest
from ui import styles


def test_progress_percentage_is_clamped_and_handles_invalid_goals():
    assert _progress_percentage(2500, 2000) == 100
    assert _progress_percentage(-10, 2000) == 0
    assert _progress_percentage(500, 0) == 0
    assert _progress_percentage(500, None) == 0


def test_goal_status_handles_thresholds_and_invalid_goals():
    assert _goal_status(99, 100) == ("不足", "#b85c5c")
    assert _goal_status(100, 100) == ("達成", "#3f7d5a")
    assert _goal_status(101, 100) == ("達成", "#3f7d5a")
    assert _goal_status(-1, 100) == ("不足", "#b85c5c")
    assert _goal_status(1, 0) is None
    assert _goal_status(1, None) is None
    assert _goal_status(100, 100, over_only=True) is None
    assert _goal_status(101, 100, over_only=True) == ("超過", "#b85c5c")


def test_progress_figure_contains_expected_values_labels_and_units():
    figure = build_daily_progress_figure(
        "水量",
        actual=1260,
        goal=2000,
        unit="ml",
        display_date=date(2026, 7, 18),
    )

    assert list(figure.data[0].values) == [63, 37]
    assert figure.data[0].hole == 0.68
    assert figure.layout.height == 180
    assert figure.layout.paper_bgcolor == "#e0edf6"
    assert figure.layout.plot_bgcolor == "#e0edf6"
    annotation_text = [annotation.text for annotation in figure.layout.annotations]
    assert annotation_text == [
        "水量",
        "<b>63%</b>",
        "18 July",
        "<b>1260</b>",
        "ml",
        "<b>不足</b>",
    ]
    percentage, date_annotation, actual = figure.layout.annotations[1:4]
    assert percentage.font.size == 26
    assert date_annotation.font.size == 11
    assert (actual.x, actual.y) == (0.74, 0.50)
    assert (actual.xanchor, actual.yanchor) == ("center", "middle")
    assert actual.font.size == 18
    title = figure.layout.annotations[0]
    assert title.text == "水量"
    assert title.font.family == "system-ui, -apple-system, sans-serif"
    assert title.font.size == 15
    assert title.font.weight == 500
    assert title.font.color == "#1a1a1a"


def test_progress_figure_clamps_over_goal_and_handles_zero_goal():
    over_goal = build_daily_progress_figure("水量", 3000, 2000, "ml")
    zero_goal = build_daily_progress_figure("蛋白質", 50, 0, "g")

    assert list(over_goal.data[0].values) == [100, 0]
    assert list(zero_goal.data[0].values) == [0, 100]
    assert zero_goal.layout.paper_bgcolor == "#f8ebe7"
    assert zero_goal.layout.plot_bgcolor == "#f8ebe7"
    assert over_goal.layout.annotations[-1].text == "<b>達成</b>"
    assert len(zero_goal.layout.annotations) == 5
    protein_title = zero_goal.layout.annotations[0]
    assert protein_title.text == "蛋白質"
    assert protein_title.font.family == "system-ui, -apple-system, sans-serif"
    assert protein_title.font.size == 15
    assert protein_title.font.weight == 500
    assert protein_title.font.color == "#1a1a1a"


def test_calorie_figure_contains_expected_values_and_labels():
    figure = build_calorie_figure(actual=1260, goal=2000)

    assert list(figure.data[0].values) == [63, 37]
    assert figure.data[0].hole == 0.76
    assert figure.layout.height == 180
    annotation_text = [annotation.text for annotation in figure.layout.annotations]
    assert "卡路里" in annotation_text[0]
    assert ">1260</b>" in annotation_text[1]
    assert "Kcal" in annotation_text[2]
    title = figure.layout.annotations[0]
    assert title.text == "卡路里"
    assert title.font.family == "system-ui, -apple-system, sans-serif"
    assert title.font.size == 15
    assert title.font.weight == 500
    assert title.font.color == "#1a1a1a"
    assert title.xanchor == "left"
    assert title.yanchor == "top"


def test_calorie_figure_clamps_invalid_values():
    over_goal = build_calorie_figure(2500, 2000)
    invalid_goal = build_calorie_figure(-20, 0)

    assert list(over_goal.data[0].values) == [100, 0]
    assert list(invalid_goal.data[0].values) == [0, 100]
    assert over_goal.layout.annotations[-1].text == "<b>超過</b>"
    assert len(invalid_goal.layout.annotations) == 3


def test_weight_summary_uses_weight_records_for_latest_value_and_trend():
    latest, trend = _weight_summary(
        [
            {"weight_kg": 62},
            {"weight_kg": "61.0"},
        ]
    )

    assert latest == 61
    assert trend == "⇩ 1.0 Kg (-1.6%)"


def test_weight_summary_handles_missing_and_unchanged_values():
    assert _weight_summary([]) == (None, "")
    assert _weight_summary([{"weight_kg": 61}]) == (61, "")
    assert _weight_summary([{"weight_kg": 61}, {"weight_kg": 61}]) == (
        61,
        "⬌ 體重維持持平",
    )


def test_progress_cards_have_scoped_fixed_two_column_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-daily_progress_cards" in value
    )

    assert '.st-key-daily_progress_cards [data-testid="stHorizontalBlock"]' in stylesheet
    assert 'flex-wrap: nowrap !important;' in stylesheet
    assert 'flex: 0 0 calc(50% - 5px) !important;' in stylesheet
    assert 'width: calc(50% - 5px) !important;' in stylesheet
    assert 'max-width: calc(50% - 5px) !important;' in stylesheet
    assert 'min-width: 0 !important;' in stylesheet
    assert 'height: 180px !important;' in stylesheet
    assert 'min-height: 180px !important;' in stylesheet
    assert 'max-height: 180px !important;' in stylesheet


def test_daily_summary_cards_have_scoped_equal_height_two_column_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-daily_summary_cards" in value
    )

    assert '.st-key-daily_summary_cards [data-testid="stHorizontalBlock"]' in stylesheet
    assert '.st-key-daily_summary_cards [data-testid="stColumn"]' in stylesheet
    assert 'flex: 0 0 calc(50% - 5px) !important;' in stylesheet
    assert '.st-key-daily_summary_cards .weight-card' in stylesheet
    assert 'background-color: #e8e5f4 !important;' in stylesheet
    assert 'height: 180px !important;' in stylesheet
    assert '.st-key-daily_summary_cards .st-key-weight_add_btn button' in stylesheet
    assert '.st-key-daily_summary_cards .weight-title' in stylesheet
    assert 'font-family: system-ui, -apple-system, sans-serif !important;' in stylesheet
    assert 'font-size: 15px !important;' in stylesheet
    assert 'font-weight: 500 !important;' in stylesheet
    assert 'color: #1a1a1a !important;' in stylesheet
    assert 'padding: 24px 14px !important;' in stylesheet
    assert 'background-color: rgba(255, 255, 255, 0.76) !important;' in stylesheet
    assert '.st-key-weight_add_btn [data-testid="stMarkdownContainer"]' in stylesheet
    assert '.st-key-weight_add_btn [data-testid="stIconMaterial"]' in stylesheet


def test_student_home_has_scoped_desktop_and_mobile_top_spacing():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-student_home_header" in value
    )

    assert '.block-container:has(.st-key-student_home_header)' in stylesheet
    assert '[data-testid="stMainBlockContainer"]:has(.st-key-student_home_header)' in stylesheet
    assert stylesheet.count(
        '.main .block-container:has(.st-key-student_home_header),'
    ) == 2
    assert 'padding-top: 16px !important;' not in stylesheet
    assert '.st-key-student_home_header .student-home-welcome' in stylesheet


def test_raw_html_progress_card_renderer_was_removed():
    assert not hasattr(student_pages, "build_daily_progress_cards_html")
    assert not hasattr(student_pages, "render_daily_progress_cards")


def test_personal_page_is_simplified_and_orders_summary_before_progress():
    source = inspect.getsource(student_pages.page_personal)
    welcome_source = inspect.getsource(student_pages._build_student_welcome_html)

    assert 'key="student_home_header"' in source
    assert '_build_student_welcome_html(user_name, avatar_base64)' in source
    assert 'class="student-home-welcome"' in welcome_source
    assert 'margin-top: 0;' in welcome_source
    assert 'st.header("Overview")' in source
    assert '"📊 今日摘要"' not in source
    assert '"今日建議"' not in source
    assert '"基礎代謝率 (BMR)"' not in source
    assert '"建議熱量攝取"' not in source
    assert '"營養攝取"' not in source
    assert 'st.metric("碳水"' not in source
    assert 'st.metric("脂肪"' not in source
    assert "get_user_record_mode" not in source
    assert '"飲食進度"' not in source
    assert '"水量"' in source
    assert '"蛋白質"' in source
    assert '"水量進度"' not in source
    assert '"蛋白質進度"' not in source
    assert 'class="weight-title">體重' in source
    assert 'key="weight_add_btn"' in source
    assert 'icon=":material/add:"' in source
    assert 'weight_lightning_btn' not in source
    assert 'st.subheader("今日概況")' not in source
    assert 'st.subheader("今日目標進度")' not in source
    assert "st.divider()" not in source
    assert 'key="daily_summary_calories"' in source
    assert source.count("build_calorie_figure(") == 1
    assert source.index('key="daily_summary_cards"') < source.index(
        'key="daily_progress_cards"'
    )
    assert source.index('key="daily_progress_cards"') < source.index(
        'key="daily_completion_card"'
    )
    assert "height: 40px" not in source


def test_daily_completion_card_has_scoped_compact_and_bonus_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-daily_completion_card" in value
    )

    assert ".st-key-daily_completion_card .daily-completion-card" in stylesheet
    assert "min-height: 104px !important;" in stylesheet
    assert ".daily-completion-card.has-bonus .daily-completion-track > span" in stylesheet
    assert "linear-gradient(90deg" in stylesheet
    assert "@media (max-width: 768px) and (max-height: 700px)" in stylesheet
    assert "height: 158px !important;" in stylesheet
    assert "padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px))" in stylesheet


def test_student_home_cards_are_square_only_on_phone_widths():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-daily_summary_cards" in value
    )
    square_comment = "/* ===== 手機版四張首頁卡片：由欄寬推導精確 1:1 ===== */"
    square_rules = stylesheet[stylesheet.index(square_comment):]

    assert "@media (max-width: 480px)" in square_rules
    assert ".st-key-daily_summary_cards .weight-card" in square_rules
    assert '.st-key-daily_summary_cards div[data-testid="stPlotlyChart"]' in square_rules
    assert '.st-key-daily_progress_cards div[data-testid="stPlotlyChart"]' in square_rules
    assert "aspect-ratio: 1 / 1 !important;" in square_rules
    assert "height: auto !important;" in square_rules
    assert "max-height: none !important;" in square_rules
    assert stylesheet.index(square_comment) > stylesheet.index(
        "@media (max-width: 768px) and (max-height: 700px)"
    )
    assert "height: 180px !important;" in stylesheet[:stylesheet.index(square_comment)]


def test_progress_container_renders_two_plotly_components():
    app = AppTest.from_string(
        '''
import streamlit as st
from pages.student import build_daily_progress_figure

with st.container(key="daily_progress_cards"):
    columns = st.columns(2, gap="small")
    for index, column in enumerate(columns):
        with column:
            st.plotly_chart(
                build_daily_progress_figure("進度", index + 1, 10, "g"),
                key=f"progress_{index}",
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )
'''
    ).run(timeout=20)

    assert len(app.exception) == 0
    assert len(app.get("plotly_chart")) == 2
