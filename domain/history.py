"""歷史資料日期解析與每日彙總。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import math
from typing import Any


@dataclass(frozen=True)
class WeightHistoryPoint:
    day: date
    weight_kg: float | None
    measured: bool
    source_date: date | None


def parse_record_date(timestamp: Any) -> date:
    try:
        return date.fromisoformat(str(timestamp)[:10])
    except (TypeError, ValueError):
        return date.min


def aggregate_daily(records: list[dict[str, Any]], start_date: date, end_date: date) -> dict[date, dict[str, float]]:
    days: dict[date, dict[str, float]] = {}
    current = start_date
    while current <= end_date:
        days[current] = {"calorie": 0.0, "protein": 0.0, "carb": 0.0, "fat": 0.0, "water": 0.0}
        current += timedelta(days=1)
    for record in records:
        record_date = parse_record_date(record.get("timestamp", ""))
        if record_date not in days:
            continue
        totals = days[record_date]
        totals["calorie"] += float(record.get("calories", 0) or 0)
        totals["protein"] += float(record.get("protein", 0) or 0)
        totals["carb"] += float(record.get("carb", 0) or 0)
        totals["fat"] += float(record.get("fat", 0) or 0)
        totals["water"] += float(record.get("water_ml", record.get("water", 0)) or 0)
    return days


def history_date_range(end_date: date, day_count: int) -> tuple[date, date]:
    """Return an inclusive history range ending on ``end_date``."""
    if day_count <= 0:
        raise ValueError("day_count must be positive")
    return end_date - timedelta(days=day_count - 1), end_date


def _timestamp_order(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def build_weight_history_series(
    records: list[dict[str, Any]], start_date: date, end_date: date
) -> list[WeightHistoryPoint]:
    """Build a daily forward-filled weight series without mutating source data."""
    if end_date < start_date:
        raise ValueError("end_date must not be earlier than start_date")

    latest_by_day: dict[date, tuple[float, int, float]] = {}
    for index, record in enumerate(records):
        record_date = parse_record_date(record.get("timestamp", ""))
        if record_date == date.min or record_date > end_date:
            continue
        try:
            weight = float(record.get("weight_kg", 0) or 0)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(weight) or weight <= 0:
            continue

        candidate = (_timestamp_order(record.get("timestamp", "")), index, weight)
        previous = latest_by_day.get(record_date)
        if previous is None or candidate[:2] >= previous[:2]:
            latest_by_day[record_date] = candidate

    current_weight: float | None = None
    source_date: date | None = None
    for record_date in sorted(day for day in latest_by_day if day < start_date):
        current_weight = latest_by_day[record_date][2]
        source_date = record_date

    points: list[WeightHistoryPoint] = []
    current_day = start_date
    while current_day <= end_date:
        measured = current_day in latest_by_day
        if measured:
            current_weight = latest_by_day[current_day][2]
            source_date = current_day
        points.append(
            WeightHistoryPoint(
                day=current_day,
                weight_kg=current_weight,
                measured=measured,
                source_date=source_date,
            )
        )
        current_day += timedelta(days=1)
    return points
