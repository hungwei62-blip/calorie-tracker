"""\u9032\u5ea6\u8a08\u7b97\u670d\u52d9\u3002\n\n\u63d0\u4f9b\uff1a\n- daily_totals(records, date)\n- weekly_totals(records, week_start)\n- classify(pct) \u2192 (\"\u9054\u6210\" | \"\u672a\u9054\" | \"\u8d85\u6a19\", pct)\n"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

METRIC_FIELDS = [
    ("calorie", "\u71b1\u91cf", "kcal"),
    ("protein", "\u86cb\u767d\u8cea", "g"),
    ("carb", "\u7cd6\u985e", "g"),
    ("fat", "\u8102\u8cea", "g"),
    ("water", "\u98f2\u6c34\u91cf", "ml"),
]


@dataclass
class Totals:
    calorie: float = 0.0
    protein: float = 0.0
    carb: float = 0.0
    fat: float = 0.0
    water: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "calorie": self.calorie,
            "protein": self.protein,
            "carb": self.carb,
            "fat": self.fat,
            "water": self.water,
        }


def _parse_date(ts: str) -> date | None:
    if not ts:
        return None
    try:
        # \u5141\u8a31\u591a\u7a2e\u683c\u5f0f\uff0c\u53ea\u53d6\u65e5\u671f\u90e8\u5206
        if "T" in ts:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
        return datetime.strptime(ts[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def filter_records(records: list[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in records:
        d = _parse_date(r.get("timestamp", ""))
        if d is None:
            continue
        if start <= d <= end:
            out.append(r)
    return out


def sum_totals(records: list[dict[str, Any]]) -> Totals:
    t = Totals()
    for r in records:
        t.calorie += float(r.get("calories", 0) or 0)
        t.protein += float(r.get("protein", 0) or 0)
        t.carb += float(r.get("carb", 0) or 0)
        t.fat += float(r.get("fat", 0) or 0)
        t.water += float(r.get("water_ml", 0) or 0)
    return t


def week_start(d: date) -> date:
    """\u4ee5\u4e00\u9031\u4e00\u70ba\u958b\u59cb (\u4e2d\u6587\u5e38\u898b\u7d00\u9304)\u3002"""
    return d - timedelta(days=d.weekday())


def classify(pct: float) -> tuple[str, float]:
    """\u4f9d\u64da\u767c\u9054\u7387\u5206\u985e\u3002\n\n    < 0.8  \u2192 \u300c\u672a\u9054\u300d\n    0.8 \u2013 1.1 \u2192 \u300c\u9054\u6210\u300d\n    > 1.1 \u2192 \u300c\u8d85\u6a19\u300d\n    \u8fd4\u56de (\u72c0\u614b, \u767c\u9054\u7387)\u3002\n    """
    if pct < 0.8:
        return "\u672a\u9054", pct
    if pct > 1.1:
        return "\u8d85\u6a19", pct
    return "\u9054\u6210", pct


def format_pct(pct: float) -> str:
    return f"{(pct - 1) * 100:+.0f}%"
