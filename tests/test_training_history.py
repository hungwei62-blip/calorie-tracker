from __future__ import annotations

from datetime import date
import inspect

import pytest

from domain.history import (
    build_training_calendar,
    shift_training_period,
    training_period_bounds,
    training_record_dates,
)
from pages import student as student_pages
from ui import styles


TODAY = date(2026, 7, 18)


def test_week_calendar_is_monday_first_and_marks_completed_dates_once():
    records = [
        {"timestamp": "2026-07-13T08:00:00+08:00", "training_types": ["重量訓練"]},
        {"timestamp": "2026-07-13T18:00:00+08:00", "training_types": ["有氧訓練"]},
        {"timestamp": "2026-07-15", "training_types": "其他"},
    ]

    cells = build_training_calendar(
        records, anchor_date=TODAY, view="週", today=TODAY
    )

    assert [cell.day for cell in cells] == [
        date(2026, 7, day) for day in range(13, 20)
    ]
    assert [cell.day for cell in cells if cell.has_training] == [
        date(2026, 7, 13),
        date(2026, 7, 15),
    ]


def test_training_dates_ignore_empty_invalid_and_future_records():
    records = [
        {"timestamp": "2026-07-17", "training_types": []},
        {"timestamp": "2026-07-17", "training_types": "  "},
        {"timestamp": "not-a-date", "training_types": ["重量訓練"]},
        {"timestamp": "2026-07-19", "training_types": ["重量訓練"]},
        {"timestamp": "2026-07-18", "training_types": ["有氧訓練"]},
    ]

    assert training_record_dates(records, today=TODAY) == frozenset({TODAY})


def test_month_calendar_uses_blank_padding_and_supports_leap_year():
    cells = build_training_calendar(
        [],
        anchor_date=date(2024, 2, 20),
        view="月",
        today=TODAY,
    )

    assert len(cells) == 35
    assert [cell.day for cell in cells[:3]] == [None, None, None]
    assert cells[3].day == date(2024, 2, 1)
    assert cells[-4].day == date(2024, 2, 29)
    assert [cell.day for cell in cells[-3:]] == [None, None, None]


def test_period_bounds_and_navigation_do_not_move_beyond_current_period():
    assert training_period_bounds(TODAY, "週") == (
        date(2026, 7, 13),
        date(2026, 7, 19),
    )
    assert training_period_bounds(TODAY, "月") == (
        date(2026, 7, 1),
        date(2026, 7, 31),
    )
    assert shift_training_period(
        TODAY, view="週", direction=1, today=TODAY
    ) == TODAY
    assert shift_training_period(
        TODAY, view="月", direction=1, today=TODAY
    ) == TODAY
    assert shift_training_period(
        TODAY, view="週", direction=-1, today=TODAY
    ) == date(2026, 7, 11)
    assert shift_training_period(
        date(2026, 1, 31), view="月", direction=-1, today=TODAY
    ) == date(2025, 12, 31)


@pytest.mark.parametrize("view", ["日", "年"])
def test_training_calendar_rejects_unknown_views(view):
    with pytest.raises(ValueError):
        build_training_calendar([], anchor_date=TODAY, view=view, today=TODAY)


def test_training_calendar_markup_has_accessible_status_and_blank_cells():
    cells = build_training_calendar(
        [{"timestamp": "2026-07-15", "training_types": ["重量訓練"]}],
        anchor_date=TODAY,
        view="週",
        today=TODAY,
    )

    markup = student_pages.build_training_calendar_html(cells, view="週")

    assert 'aria-label="訓練紀錄日曆"' in markup
    assert 'datetime="2026-07-15"' in markup
    assert "2026年07月15日，有訓練" in markup
    assert markup.count("is-complete") == 1
    assert markup.count('role="listitem"') == 7


def test_training_period_labels_match_selected_view():
    assert student_pages._training_period_label(TODAY, "週") == (
        "2026/07/13 – 07/19"
    )
    assert student_pages._training_period_label(TODAY, "月") == "2026 年 7 月"


def test_training_history_renderer_has_independent_controls_and_navigation():
    source = inspect.getsource(student_pages._render_student_training_history)

    assert '("週", "月")' in source
    assert 'key="training_history_view"' in source
    assert '"training_history_anchor"' in source
    assert 'key="training_history_previous"' in source
    assert 'key="training_history_next"' in source
    assert "disabled=period_start >= current_start" in source
    assert "sheets.get_training_records(user_id)" in source
    assert "build_training_calendar(" in source


def test_training_history_styles_keep_seven_columns_on_mobile():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-student_training_history" in value
    )

    assert ".st-key-student_training_history_card" in stylesheet
    assert "grid-template-columns: repeat(7, minmax(0, 1fr))" in stylesheet
    assert "aspect-ratio: 1 / 1" in stylesheet
    assert "background: #16a77a" in stylesheet
    assert "@media (max-width: 480px)" in stylesheet
    assert "width: min(38px, 100%)" in stylesheet
