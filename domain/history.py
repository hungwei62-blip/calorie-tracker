"""歷史資料日期解析與每日彙總。"""

from __future__ import annotations

import calendar
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


@dataclass(frozen=True)
class TrainingCalendarDay:
    day: date | None
    has_training: bool


@dataclass(frozen=True)
class NutritionHistoryPoint:
    day: date
    calories: float | None
    protein: float | None
    recorded: bool


@dataclass(frozen=True)
class WaterHistoryPoint:
    day: date
    water_ml: float | None
    recorded: bool


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


def _nonnegative_finite(value: object) -> float | None:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def build_nutrition_history_series(
    records: list[dict[str, Any]],
    start_date: date,
    end_date: date,
    *,
    today: date,
) -> list[NutritionHistoryPoint]:
    """Aggregate food intake by day while leaving unrecorded days empty."""
    if end_date < start_date:
        raise ValueError("end_date must not be earlier than start_date")

    totals: dict[date, list[float]] = {}
    for record in records:
        if str(record.get("meal_type", "") or "").strip() != "食物":
            continue
        record_date = parse_record_date(record.get("timestamp", ""))
        if (
            record_date == date.min
            or record_date < start_date
            or record_date > end_date
            or record_date > today
        ):
            continue

        calories = _nonnegative_finite(record.get("calories", 0))
        protein = _nonnegative_finite(record.get("protein", 0))
        valid_calories = calories if calories is not None else 0.0
        valid_protein = protein if protein is not None else 0.0
        if valid_calories <= 0 and valid_protein <= 0:
            continue

        daily = totals.setdefault(record_date, [0.0, 0.0])
        daily[0] += valid_calories
        daily[1] += valid_protein

    points: list[NutritionHistoryPoint] = []
    current = start_date
    while current <= end_date:
        daily = totals.get(current)
        points.append(
            NutritionHistoryPoint(
                day=current,
                calories=daily[0] if daily is not None else None,
                protein=daily[1] if daily is not None else None,
                recorded=daily is not None,
            )
        )
        current += timedelta(days=1)
    return points


def nutrition_history_averages(
    points: list[NutritionHistoryPoint],
) -> tuple[float, float, int] | None:
    """Return daily calorie/protein averages over recorded food days only."""
    recorded = [point for point in points if point.recorded]
    if not recorded:
        return None
    count = len(recorded)
    return (
        sum(float(point.calories or 0) for point in recorded) / count,
        sum(float(point.protein or 0) for point in recorded) / count,
        count,
    )


def build_water_history_series(
    records: list[dict[str, Any]],
    start_date: date,
    end_date: date,
    *,
    today: date,
) -> list[WaterHistoryPoint]:
    """Aggregate water records by day while leaving unrecorded days empty."""
    if end_date < start_date:
        raise ValueError("end_date must not be earlier than start_date")

    totals: dict[date, float] = {}
    for record in records:
        if str(record.get("meal_type", "") or "").strip() not in {"飲水", "喝水"}:
            continue
        record_date = parse_record_date(record.get("timestamp", ""))
        if (
            record_date == date.min
            or record_date < start_date
            or record_date > end_date
            or record_date > today
        ):
            continue

        water_ml = _nonnegative_finite(
            record.get("water_ml", record.get("water", 0))
        )
        if water_ml is None or water_ml <= 0:
            continue
        totals[record_date] = totals.get(record_date, 0.0) + water_ml

    points: list[WaterHistoryPoint] = []
    current = start_date
    while current <= end_date:
        water_ml = totals.get(current)
        points.append(
            WaterHistoryPoint(
                day=current,
                water_ml=water_ml,
                recorded=water_ml is not None,
            )
        )
        current += timedelta(days=1)
    return points


def water_history_average(
    points: list[WaterHistoryPoint],
) -> tuple[float, int] | None:
    """Return average water intake over recorded water days only."""
    recorded = [point for point in points if point.recorded]
    if not recorded:
        return None
    count = len(recorded)
    return sum(float(point.water_ml or 0) for point in recorded) / count, count


def _has_training_types(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(str(item or "").strip() for item in value)
    return False


def training_record_dates(
    records: list[dict[str, Any]], *, today: date
) -> frozenset[date]:
    """Return valid, non-future dates that contain a training selection."""
    completed: set[date] = set()
    for record in records:
        record_date = parse_record_date(record.get("timestamp", ""))
        if record_date == date.min or record_date > today:
            continue
        if _has_training_types(record.get("training_types")):
            completed.add(record_date)
    return frozenset(completed)


def training_period_bounds(
    anchor_date: date, view: str
) -> tuple[date, date]:
    """Return Monday-based week or calendar-month bounds."""
    if view == "週":
        start = anchor_date - timedelta(days=anchor_date.weekday())
        return start, start + timedelta(days=6)
    if view == "月":
        start = anchor_date.replace(day=1)
        last_day = calendar.monthrange(start.year, start.month)[1]
        return start, start.replace(day=last_day)
    raise ValueError("view must be '週' or '月'")


def build_training_calendar(
    records: list[dict[str, Any]],
    *,
    anchor_date: date,
    view: str,
    today: date,
) -> list[TrainingCalendarDay]:
    """Build Monday-first week/month cells without adjacent-month dates."""
    if anchor_date > today:
        anchor_date = today
    start, end = training_period_bounds(anchor_date, view)
    completed = training_record_dates(records, today=today)

    cells: list[TrainingCalendarDay] = []
    if view == "月":
        cells.extend(
            TrainingCalendarDay(day=None, has_training=False)
            for _ in range(start.weekday())
        )

    current = start
    while current <= end:
        cells.append(
            TrainingCalendarDay(
                day=current,
                has_training=current in completed,
            )
        )
        current += timedelta(days=1)

    if view == "月":
        cells.extend(
            TrainingCalendarDay(day=None, has_training=False)
            for _ in range((-len(cells)) % 7)
        )
    return cells


def shift_training_period(
    anchor_date: date,
    *,
    view: str,
    direction: int,
    today: date,
) -> date:
    """Move one visible period and clamp navigation at the current period."""
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    if view == "週":
        candidate = anchor_date + timedelta(days=direction * 7)
    elif view == "月":
        month_index = anchor_date.year * 12 + anchor_date.month - 1 + direction
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        day = min(anchor_date.day, calendar.monthrange(year, month)[1])
        candidate = date(year, month, day)
    else:
        raise ValueError("view must be '週' or '月'")

    candidate_start, _ = training_period_bounds(candidate, view)
    current_start, _ = training_period_bounds(today, view)
    return today if candidate_start >= current_start else candidate
