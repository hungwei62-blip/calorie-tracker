from __future__ import annotations

from datetime import date

from ui.history_calendar import (
    _HISTORY_CALENDAR_CSS,
    _HISTORY_CALENDAR_HTML,
    _HISTORY_CALENDAR_JS,
    build_history_calendar_cells,
    normalize_history_calendar_selection,
)


TODAY = date(2026, 7, 22)


def test_month_calendar_is_monday_first_fixed_six_weeks_and_marks_records():
    cells = build_history_calendar_cells(
        date(2026, 7, 1),
        today=TODAY,
        record_dates={date(2026, 7, 1), date(2026, 7, 22)},
    )

    assert len(cells) == 42
    assert [cell["day"] for cell in cells[:3]] == ["", "", 1]
    july_first = next(cell for cell in cells if cell.get("date") == "2026-07-01")
    today = next(cell for cell in cells if cell.get("date") == "2026-07-22")
    future = next(cell for cell in cells if cell.get("date") == "2026-07-23")
    assert july_first["has_records"] is True
    assert today["is_today"] is True
    assert future["disabled"] is True


def test_month_calendar_supports_leap_year_and_blank_padding():
    cells = build_history_calendar_cells(
        date(2028, 2, 1), today=date(2028, 2, 29), record_dates=[]
    )

    assert len(cells) == 42
    assert any(cell.get("date") == "2028-02-29" for cell in cells)
    assert sum(1 for cell in cells if not cell["date"]) == 13


def test_calendar_selection_rejects_future_and_cross_month_dates():
    default = normalize_history_calendar_selection(None, today=TODAY)
    future_month = normalize_history_calendar_selection(
        {"view_month": "2026-08-01", "selected_date": "2026-08-01"},
        today=TODAY,
    )
    cross_month = normalize_history_calendar_selection(
        {"view_month": "2026-06-01", "selected_date": "2026-07-01"},
        today=TODAY,
    )

    assert default.view_month == date(2026, 7, 1)
    assert default.selected_date is None
    assert future_month.view_month == date(2026, 7, 1)
    assert future_month.selected_date is None
    assert cross_month.view_month == date(2026, 6, 1)
    assert cross_month.selected_date is None


def test_calendar_uses_ccv2_controlled_state_and_accessible_buttons():
    assert "setStateValue(\"selection\"" in _HISTORY_CALENDAR_JS
    assert 'selected_date: ""' in _HISTORY_CALENDAR_JS
    assert "Streamlit.setComponentValue" not in _HISTORY_CALENDAR_JS
    assert "window.Streamlit" not in _HISTORY_CALENDAR_JS
    assert 'aria-label="上一個月"' in _HISTORY_CALENDAR_HTML
    assert 'aria-label="下一個月"' in _HISTORY_CALENDAR_HTML
    assert 'role="grid"' in _HISTORY_CALENDAR_HTML
    assert ".history-calendar__day.has-records" in _HISTORY_CALENDAR_CSS
    assert ".history-calendar__day.is-selected" in _HISTORY_CALENDAR_CSS
    assert "color: #6a558f" in _HISTORY_CALENDAR_CSS
    assert "background: rgba(183, 161, 230, 0.24)" in _HISTORY_CALENDAR_CSS
    assert "background: rgba(183, 161, 230, 0.38)" in _HISTORY_CALENDAR_CSS
    assert "background: rgba(151, 124, 207, 0.48)" in _HISTORY_CALENDAR_CSS
    assert "width: 36px" in _HISTORY_CALENDAR_CSS
    assert "height: 36px" in _HISTORY_CALENDAR_CSS
    assert "@media (max-width: 480px)" in _HISTORY_CALENDAR_CSS
