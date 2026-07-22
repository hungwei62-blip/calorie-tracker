"""Interactive month calendar for student-owned history records."""

from __future__ import annotations

from calendar import Calendar
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping

import streamlit as st


@dataclass(frozen=True)
class HistoryCalendarSelection:
    view_month: date
    selected_date: date | None


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_month(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    year, month_zero_based = divmod(month_index, 12)
    return date(year, month_zero_based + 1, 1)


def build_history_calendar_cells(
    view_month: date,
    *,
    today: date,
    record_dates: Iterable[date],
) -> list[dict[str, object]]:
    """Return a stable six-week, Monday-first calendar grid."""
    month_start = _month_start(min(view_month, today))
    recorded = {day for day in record_dates if isinstance(day, date)}
    weeks = Calendar(firstweekday=0).monthdayscalendar(
        month_start.year, month_start.month
    )
    weeks.extend([[0] * 7 for _ in range(6 - len(weeks))])

    cells: list[dict[str, object]] = []
    for week in weeks:
        for day_number in week:
            if day_number == 0:
                cells.append({"date": "", "day": "", "has_records": False})
                continue
            cell_date = date(month_start.year, month_start.month, day_number)
            cells.append(
                {
                    "date": cell_date.isoformat(),
                    "day": day_number,
                    "has_records": cell_date in recorded,
                    "is_today": cell_date == today,
                    "disabled": cell_date > today,
                }
            )
    return cells


def _selection_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if value is None:
        return {}
    return {
        "view_month": getattr(value, "view_month", ""),
        "selected_date": getattr(value, "selected_date", ""),
    }


def _parse_iso_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def normalize_history_calendar_selection(
    value: object, *, today: date
) -> HistoryCalendarSelection:
    raw = _selection_mapping(value)
    view_month = _parse_iso_date(raw.get("view_month")) or _month_start(today)
    view_month = _month_start(min(view_month, today))
    selected_date = _parse_iso_date(raw.get("selected_date"))
    if (
        selected_date is None
        or selected_date > today
        or _month_start(selected_date) != view_month
    ):
        selected_date = None
    return HistoryCalendarSelection(view_month, selected_date)


_HISTORY_CALENDAR_HTML = """
<section class="history-calendar" aria-label="紀錄日期月曆">
  <header class="history-calendar__header">
    <button class="history-calendar__nav history-calendar__previous" type="button"
            aria-label="上一個月">‹</button>
    <div class="history-calendar__period" aria-live="polite"></div>
    <button class="history-calendar__nav history-calendar__next" type="button"
            aria-label="下一個月">›</button>
  </header>
  <div class="history-calendar__weekdays" role="row">
    <span role="columnheader">一</span><span role="columnheader">二</span>
    <span role="columnheader">三</span><span role="columnheader">四</span>
    <span role="columnheader">五</span><span role="columnheader">六</span>
    <span role="columnheader">日</span>
  </div>
  <div class="history-calendar__grid" role="grid"></div>
</section>
"""


_HISTORY_CALENDAR_CSS = """
:host {
  display: block;
  width: 100%;
}

.history-calendar {
  box-sizing: border-box;
  width: 100%;
  padding: 14px 16px 18px;
  color: #4e435f;
  background: #ffffff;
  border: 1px solid #ece6f3;
  border-radius: 20px;
  box-shadow: 0 8px 28px rgba(106, 88, 143, 0.08);
  font-family: system-ui, -apple-system, "Noto Sans TC", sans-serif;
}

.history-calendar__header {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) 36px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.history-calendar__period {
  overflow: hidden;
  font-size: 15px;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  line-height: 36px;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-calendar__nav {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  padding: 0;
  color: #6a558f;
  background: rgba(183, 161, 230, 0.24);
  border: 1px solid rgba(151, 124, 207, 0.34);
  border-radius: 50%;
  cursor: pointer;
  font: inherit;
  font-size: 25px;
  line-height: 1;
}

.history-calendar__nav:hover:not(:disabled) {
  color: #554075;
  background: rgba(183, 161, 230, 0.38);
  border-color: rgba(133, 101, 194, 0.48);
}

.history-calendar__nav:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(183, 161, 230, 0.42);
}

.history-calendar__day:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(183, 161, 230, 0.42);
}

.history-calendar__nav:active:not(:disabled) {
  background: rgba(151, 124, 207, 0.48);
}

.history-calendar__nav:disabled {
  color: rgba(106, 85, 143, 0.42);
  background: rgba(183, 161, 230, 0.12);
  border-color: rgba(151, 124, 207, 0.18);
  cursor: default;
}

.history-calendar__weekdays,
.history-calendar__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  width: 100%;
  column-gap: 8px;
}

.history-calendar__weekdays {
  margin-bottom: 8px;
  color: #7f718f;
  font-size: 11px;
  font-weight: 500;
  text-align: center;
}

.history-calendar__grid {
  row-gap: 7px;
}

.history-calendar__day,
.history-calendar__empty {
  display: grid;
  place-items: center;
  justify-self: center;
  box-sizing: border-box;
  width: min(40px, 100%);
  aspect-ratio: 1 / 1;
  border-radius: 50%;
}

.history-calendar__day {
  position: relative;
  padding: 0;
  color: #746b80;
  background: #f5f2f9;
  border: 0;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.history-calendar__day.has-records {
  color: #ffffff;
  background: #b7a1e6;
  box-shadow: 0 4px 12px rgba(183, 161, 230, 0.34);
}

.history-calendar__day.is-selected {
  color: #ffffff;
  background: #6a558f;
  box-shadow: 0 0 0 3px #ffffff, 0 0 0 6px rgba(106, 85, 143, 0.30);
}

.history-calendar__day.is-today:not(.is-selected)::after {
  content: "";
  position: absolute;
  bottom: 4px;
  width: 4px;
  height: 4px;
  background: currentColor;
  border-radius: 50%;
}

.history-calendar__day:disabled {
  color: #c8c2cf;
  background: #faf9fb;
  cursor: default;
  box-shadow: none;
}

@media (max-width: 480px) {
  .history-calendar {
    padding: 12px 8px 15px;
    border-radius: 18px;
  }

  .history-calendar__header {
    margin-bottom: 8px;
  }

  .history-calendar__period {
    font-size: 13px;
  }

  .history-calendar__weekdays,
  .history-calendar__grid {
    column-gap: 4px;
  }

  .history-calendar__weekdays {
    font-size: 10px;
  }

  .history-calendar__grid {
    row-gap: 5px;
  }

  .history-calendar__day,
  .history-calendar__empty {
    width: min(36px, 100%);
  }

  .history-calendar__day {
    font-size: 12px;
  }
}
"""


_HISTORY_CALENDAR_JS = """
export default function(component) {
  const { parentElement, data, setStateValue } = component
  const root = parentElement.querySelector(".history-calendar")
  const period = root?.querySelector(".history-calendar__period")
  const grid = root?.querySelector(".history-calendar__grid")
  const previous = root?.querySelector(".history-calendar__previous")
  const next = root?.querySelector(".history-calendar__next")
  if (!root || !period || !grid || !previous || !next) return

  const selection = data?.selection ?? {}
  const selectedDate = selection.selected_date ?? ""
  period.textContent = data?.period_label ?? ""
  previous.disabled = false
  next.disabled = Boolean(data?.next_disabled)

  previous.onclick = () => {
    setStateValue("selection", {
      view_month: data.previous_month,
      selected_date: "",
    })
  }
  next.onclick = () => {
    if (next.disabled) return
    setStateValue("selection", {
      view_month: data.next_month,
      selected_date: "",
    })
  }

  grid.replaceChildren()
  for (const cell of data?.cells ?? []) {
    if (!cell.date) {
      const empty = document.createElement("span")
      empty.className = "history-calendar__empty"
      empty.setAttribute("aria-hidden", "true")
      grid.appendChild(empty)
      continue
    }

    const button = document.createElement("button")
    button.type = "button"
    button.className = "history-calendar__day"
    if (cell.has_records) button.classList.add("has-records")
    if (cell.is_today) button.classList.add("is-today")
    if (cell.date === selectedDate) button.classList.add("is-selected")
    button.textContent = String(cell.day)
    button.disabled = Boolean(cell.disabled)
    button.setAttribute("role", "gridcell")
    button.setAttribute("aria-label", `${cell.date}${cell.has_records ? "，有紀錄" : "，無紀錄"}`)
    button.setAttribute("aria-pressed", String(cell.date === selectedDate))
    button.onclick = () => {
      if (button.disabled) return
      setStateValue("selection", {
        view_month: selection.view_month,
        selected_date: cell.date,
      })
    }
    grid.appendChild(button)
  }
}
"""


_HISTORY_CALENDAR = st.components.v2.component(
    "student_history_record_calendar",
    html=_HISTORY_CALENDAR_HTML,
    css=_HISTORY_CALENDAR_CSS,
    js=_HISTORY_CALENDAR_JS,
)


def history_record_calendar(
    *,
    today: date,
    record_dates: Iterable[date],
    key: str,
) -> HistoryCalendarSelection:
    """Render a controlled month calendar and return its current selection."""
    component_state = st.session_state.get(key, {})
    if isinstance(component_state, Mapping):
        raw_selection = component_state.get("selection")
    else:
        raw_selection = getattr(component_state, "selection", None)
    selection = normalize_history_calendar_selection(raw_selection, today=today)
    current_month = _month_start(today)
    previous_month = _shift_month(selection.view_month, -1)
    next_month = _shift_month(selection.view_month, 1)
    selection_data = {
        "view_month": selection.view_month.isoformat(),
        "selected_date": (
            selection.selected_date.isoformat() if selection.selected_date else ""
        ),
    }
    result = _HISTORY_CALENDAR(
        key=key,
        data={
            "selection": selection_data,
            "period_label": f"{selection.view_month.year} 年 {selection.view_month.month} 月",
            "previous_month": previous_month.isoformat(),
            "next_month": next_month.isoformat(),
            "next_disabled": selection.view_month >= current_month,
            "cells": build_history_calendar_cells(
                selection.view_month, today=today, record_dates=record_dates
            ),
        },
        default={"selection": selection_data},
        on_selection_change=lambda: None,
        width="stretch",
        height="content",
    )
    result_selection = (
        result.get("selection")
        if isinstance(result, Mapping)
        else getattr(result, "selection", None)
    )
    return normalize_history_calendar_selection(
        result_selection or selection_data, today=today
    )
