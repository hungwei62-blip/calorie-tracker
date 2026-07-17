"""歷史資料日期解析與每日彙總。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


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
