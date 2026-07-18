from __future__ import annotations

from datetime import date
import inspect

import pytest

from domain.history import (
    build_nutrition_history_series,
    nutrition_history_averages,
)
from pages import student as student_pages
from ui import styles


START = date(2026, 7, 13)
END = date(2026, 7, 19)


def test_nutrition_history_sums_food_records_and_keeps_missing_days_empty():
    points = build_nutrition_history_series(
        [
            {
                "timestamp": "2026-07-14T08:00:00+08:00",
                "meal_type": "食物",
                "calories": 400,
                "protein": 20,
            },
            {
                "timestamp": "2026-07-14T18:00:00+08:00",
                "meal_type": "食物",
                "calories": 600,
                "protein": 35,
            },
        ],
        START,
        END,
        today=END,
    )

    assert len(points) == 7
    assert points[0].recorded is False
    assert points[0].calories is None
    assert points[1].recorded is True
    assert points[1].calories == 1000
    assert points[1].protein == 55


def test_water_invalid_dates_future_and_non_food_rows_are_ignored():
    points = build_nutrition_history_series(
        [
            {"timestamp": "2026-07-14", "meal_type": "飲水", "calories": 50},
            {"timestamp": "bad-date", "meal_type": "食物", "calories": 500},
            {"timestamp": "2026-07-20", "meal_type": "食物", "calories": 500},
            {"timestamp": "2026-07-18", "meal_type": "食物", "calories": -1},
            {"timestamp": "2026-07-18", "meal_type": "食物", "protein": "nan"},
        ],
        START,
        date(2026, 7, 20),
        today=END,
    )

    assert all(point.recorded is False for point in points)


def test_recorded_day_preserves_zero_for_the_other_metric():
    points = build_nutrition_history_series(
        [
            {
                "timestamp": "2026-07-19",
                "meal_type": "食物",
                "calories": 320,
                "protein": 0,
            }
        ],
        START,
        END,
        today=END,
    )

    assert points[-1].recorded is True
    assert points[-1].calories == 320
    assert points[-1].protein == 0


def test_nutrition_average_uses_recorded_days_only():
    points = build_nutrition_history_series(
        [
            {
                "timestamp": "2026-07-14",
                "meal_type": "食物",
                "calories": 1000,
                "protein": 50,
            },
            {
                "timestamp": "2026-07-18",
                "meal_type": "食物",
                "calories": 2000,
                "protein": 100,
            },
        ],
        START,
        END,
        today=END,
    )

    assert nutrition_history_averages(points) == (1500, 75, 2)
    assert nutrition_history_averages([]) is None


def test_nutrition_history_rejects_reversed_range():
    with pytest.raises(ValueError):
        build_nutrition_history_series([], END, START, today=END)


def test_nutrition_summary_shows_recorded_day_averages():
    points = build_nutrition_history_series(
        [
            {
                "timestamp": "2026-07-19",
                "meal_type": "食物",
                "calories": 1890,
                "protein": 112,
            }
        ],
        START,
        END,
        today=END,
    )

    markup = student_pages.build_nutrition_history_summary_html(points)

    assert "平均熱量" in markup
    assert "1890" in markup
    assert "kcal／日" in markup
    assert "平均蛋白質" in markup
    assert "112.0" in markup
    assert "記錄日計算" not in markup


def test_nutrition_figure_uses_dual_axes_colors_and_shared_dates():
    points = build_nutrition_history_series(
        [
            {
                "timestamp": "2026-07-14",
                "meal_type": "食物",
                "calories": 1200,
                "protein": 70,
            },
            {
                "timestamp": "2026-07-18",
                "meal_type": "食物",
                "calories": 1800,
                "protein": 100,
            },
        ],
        START,
        END,
        today=END,
    )

    figure = student_pages.build_nutrition_history_figure(points, 7)

    assert len(figure.data) == 2
    assert figure.data[0].line.color == "#A8D5C2"
    assert figure.data[0].yaxis == "y"
    assert figure.data[1].line.color == "#F4B183"
    assert figure.data[1].yaxis == "y2"
    assert figure.data[0].connectgaps is False
    assert figure.data[1].connectgaps is False
    assert figure.layout.yaxis.title.text is None
    assert figure.layout.yaxis2.title.text is None
    assert figure.layout.yaxis2.overlaying == "y"
    assert figure.layout.yaxis.showgrid is False
    assert figure.layout.yaxis.ticklabelposition == "inside"
    assert figure.layout.yaxis2.ticklabelposition == "inside"
    assert figure.layout.hovermode == "x unified"
    assert len(figure.layout.xaxis.tickvals) == 7
    assert list(figure.layout.xaxis.ticktext) == [
        "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
    ]
    assert figure.layout.margin.l == 28
    assert figure.layout.margin.r == 28
    assert figure.layout.height == 250


def test_thirty_day_nutrition_figure_reduces_date_ticks():
    points = build_nutrition_history_series(
        [],
        date(2026, 6, 20),
        END,
        today=END,
    )

    figure = student_pages.build_nutrition_history_figure(points, 30)

    assert len(figure.layout.xaxis.tickvals) == 5


def test_nutrition_renderer_does_not_depend_on_goals_or_legacy_charts():
    source = inspect.getsource(student_pages._render_student_nutrition_history)

    assert 'key="nutrition_history_range"' in source
    assert 'key="student_nutrition_history_card"' in source
    assert 'key="student_nutrition_history_chart"' in source
    assert "_fetch_records_cached(user_id)" in source
    assert "_fetch_goals_cached" not in source
    assert "st.dataframe" not in source
    assert "st.bar_chart" not in source
    assert "所選期間尚無飲食紀錄" in source
    assert 'st.subheader("養分攝取")' in source
    assert "攝取趨勢" not in source


def test_nutrition_history_has_scoped_dual_axis_card_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-student_nutrition_history" in value
    )

    assert ".st-key-student_nutrition_history_card" in stylesheet
    assert ".nutrition-history-summary" in stylesheet
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in stylesheet
    assert "color: var(--history-primary-dark)" in stylesheet
    assert "color: var(--history-accent-dark)" in stylesheet
    assert ".st-key-student_nutrition_history_chart" in stylesheet
    assert "padding: 16px 0 8px !important;" in stylesheet
    assert "height: 245px !important;" not in stylesheet
