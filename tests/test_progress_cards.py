from __future__ import annotations

from datetime import date

import pages.student as student_pages
from pages.student import _progress_percentage, build_daily_progress_figure
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


def test_progress_cards_have_scoped_desktop_and_mobile_column_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-daily_progress_cards" in value
    )

    assert '.st-key-daily_progress_cards [data-testid="stHorizontalBlock"]' in stylesheet
    assert 'flex: 0 0 calc(50% - 5px) !important;' in stylesheet
    assert 'width: calc(50% - 5px) !important;' in stylesheet
    assert 'max-width: calc(50% - 5px) !important;' in stylesheet
    assert 'min-width: 0 !important;' in stylesheet


def test_raw_html_progress_card_renderer_was_removed():
    assert not hasattr(student_pages, "build_daily_progress_cards_html")
    assert not hasattr(student_pages, "render_daily_progress_cards")


def test_progress_container_renders_three_plotly_components():
    app = AppTest.from_string(
        '''
import streamlit as st
from pages.student import build_daily_progress_figure

with st.container(key="daily_progress_cards"):
    columns = st.columns(3, gap="small")
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
    assert len(app.get("plotly_chart")) == 3
