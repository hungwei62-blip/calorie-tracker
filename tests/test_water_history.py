from __future__ import annotations

from datetime import date
import inspect

import pytest

from domain.history import build_water_history_series, water_history_average
from pages import student as student_pages
from ui import styles


START = date(2026, 7, 13)
END = date(2026, 7, 19)


def test_water_history_sums_new_and_legacy_records_and_keeps_gaps():
    points = build_water_history_series(
        [
            {
                "timestamp": "2026-07-14T08:00:00+08:00",
                "meal_type": "飲水",
                "water_ml": 300,
            },
            {
                "timestamp": "2026-07-14T18:00:00+08:00",
                "meal_type": "喝水",
                "water_ml": 500,
            },
        ],
        START,
        END,
        today=END,
    )

    assert len(points) == 7
    assert points[0].recorded is False
    assert points[0].water_ml is None
    assert points[1].recorded is True
    assert points[1].water_ml == 800


def test_water_history_ignores_invalid_future_nonwater_and_nonpositive_rows():
    points = build_water_history_series(
        [
            {"timestamp": "2026-07-14", "meal_type": "食物", "water_ml": 500},
            {"timestamp": "bad-date", "meal_type": "飲水", "water_ml": 500},
            {"timestamp": "2026-07-20", "meal_type": "飲水", "water_ml": 500},
            {"timestamp": "2026-07-18", "meal_type": "飲水", "water_ml": -1},
            {"timestamp": "2026-07-18", "meal_type": "飲水", "water_ml": 0},
            {"timestamp": "2026-07-18", "meal_type": "飲水", "water_ml": "nan"},
        ],
        START,
        date(2026, 7, 20),
        today=END,
    )

    assert all(point.recorded is False for point in points)


def test_water_average_uses_recorded_days_only():
    points = build_water_history_series(
        [
            {"timestamp": "2026-07-14", "meal_type": "飲水", "water_ml": 1000},
            {"timestamp": "2026-07-18", "meal_type": "喝水", "water_ml": 2000},
        ],
        START,
        END,
        today=END,
    )

    assert water_history_average(points) == (1500, 2)
    assert water_history_average([]) is None


def test_water_history_rejects_reversed_range():
    with pytest.raises(ValueError):
        build_water_history_series([], END, START, today=END)


def test_water_summary_and_figure_use_single_axis_blue_palette():
    points = build_water_history_series(
        [
            {"timestamp": "2026-07-14", "meal_type": "飲水", "water_ml": 1200},
            {"timestamp": "2026-07-18", "meal_type": "飲水", "water_ml": 1800},
        ],
        START,
        END,
        today=END,
    )

    markup = student_pages.build_water_history_summary_html(points)
    figure = student_pages.build_water_history_figure(points, 7)

    assert "平均飲水量" in markup
    assert "1500" in markup
    assert "ml／日" in markup
    assert len(figure.data) == 1
    assert figure.data[0].line.color == "#BFD8FF"
    assert figure.data[0].marker.color == "#BFD8FF"
    assert figure.data[0].connectgaps is False
    assert figure.data[0].fill == "tozeroy"
    assert figure.layout.yaxis.title.text is None
    assert figure.layout.yaxis.showgrid is False
    assert figure.layout.yaxis.ticklabelposition == "inside"
    assert figure.layout.hovermode == "x unified"
    assert list(figure.layout.xaxis.ticktext) == [
        "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
    ]
    assert figure.layout.margin.l == 28
    assert figure.layout.margin.r == 28


def test_thirty_day_water_figure_reduces_date_ticks():
    points = build_water_history_series(
        [], date(2026, 6, 20), END, today=END
    )

    figure = student_pages.build_water_history_figure(points, 30)

    assert len(figure.layout.xaxis.tickvals) == 5


def test_water_renderer_has_independent_controls_and_cached_records():
    source = inspect.getsource(student_pages._render_student_water_history)

    assert 'st.subheader("飲水量")' in source
    assert 'key="water_history_range"' in source
    assert 'key="student_water_history_card"' in source
    assert 'key="student_water_history_chart"' in source
    assert "_fetch_records_cached(user_id)" in source
    assert "所選期間尚無飲水紀錄" in source


def test_water_history_has_scoped_blue_card_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-student_water_history" in value
    )

    assert ".st-key-student_water_history_card" in stylesheet
    assert ".water-history-summary" in stylesheet
    assert "background: #F6F9FC" in stylesheet
    assert "border: 1px solid #E6EDF3" in stylesheet
    assert "background: #E6F0FA" in stylesheet
    assert "color: #7E8FA3" in stylesheet
    assert ".st-key-student_water_history_chart" in stylesheet
