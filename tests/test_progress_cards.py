from __future__ import annotations

from datetime import date
import inspect

import pages.student as student_pages
from pages.student import (
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


def test_progress_figure_contains_expected_values_labels_and_units():
    figure = build_daily_progress_figure(
        "飲食進度",
        actual=1260,
        goal=2000,
        unit="kcal",
        display_date=date(2026, 7, 18),
    )

    assert list(figure.data[0].values) == [63, 37]
    assert figure.data[0].hole == 0.68
    assert figure.layout.height == 150
    annotation_text = [annotation.text for annotation in figure.layout.annotations]
    assert annotation_text == [
        "<b>飲食進度</b>",
        "<b>63%</b>",
        "18 July",
        "<b>1260</b>",
        "kcal",
    ]


def test_progress_figure_clamps_over_goal_and_handles_zero_goal():
    over_goal = build_daily_progress_figure("水量進度", 3000, 2000, "ml")
    zero_goal = build_daily_progress_figure("蛋白質進度", 50, 0, "g")

    assert list(over_goal.data[0].values) == [100, 0]
    assert list(zero_goal.data[0].values) == [0, 100]


def test_calorie_figure_contains_expected_values_and_labels():
    figure = build_calorie_figure(actual=1260, goal=2000)

    assert list(figure.data[0].values) == [63, 37]
    assert figure.data[0].hole == 0.76
    assert figure.layout.height == 180
    annotation_text = [annotation.text for annotation in figure.layout.annotations]
    assert "Calories" in annotation_text[0]
    assert ">1260</b>" in annotation_text[1]
    assert "Kcal" in annotation_text[2]


def test_calorie_figure_clamps_invalid_values():
    over_goal = build_calorie_figure(2500, 2000)
    invalid_goal = build_calorie_figure(-20, 0)

    assert list(over_goal.data[0].values) == [100, 0]
    assert list(invalid_goal.data[0].values) == [0, 100]


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
    assert 'height: 180px !important;' in stylesheet
    assert '.st-key-daily_summary_cards .st-key-weight_lightning_btn button' in stylesheet


def test_raw_html_progress_card_renderer_was_removed():
    assert not hasattr(student_pages, "build_daily_progress_cards_html")
    assert not hasattr(student_pages, "render_daily_progress_cards")


def test_personal_page_uses_two_progress_cards_and_one_summary_calorie_card():
    source = inspect.getsource(student_pages.page_personal)

    assert '"飲食進度"' not in source
    assert '"水量進度"' in source
    assert '"蛋白質進度"' in source
    assert 'key="daily_summary_calories"' in source
    assert source.count("build_calorie_figure(") == 1


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
