"""進度計算服務。

提供：
- daily_totals(records, date)
- weekly_totals(records, week_start)
- classify(pct) → ("達成" | "未達" | "超標", pct)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

METRIC_FIELDS = [
    ("calories", "熱量", "kcal"),
    ("protein", "蛋白質", "g"),
    ("carb", "糖類", "g"),
    ("fat", "脂肪", "g"),
    ("water", "飲水量", "ml"),
]


@dataclass
class Totals:
    calories: float = 0.0
    protein: float = 0.0
    carb: float = 0.0
    fat: float = 0.0
    water: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "calories": self.calories,
            "protein": self.protein,
            "carb": self.carb,
            "fat": self.fat,
            "water": self.water,
        }


def _parse_date(ts: str) -> date | None:
    if not ts:
        return None
    try:
        # 允許多種格式，只取日期部分
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
        t.calories += float(r.get("calories", 0) or 0)
        t.protein += float(r.get("protein", 0) or 0)
        t.carb += float(r.get("carb", 0) or 0)
        t.fat += float(r.get("fat", 0) or 0)
        t.water += float(r.get("water_ml", 0) or 0)
    return t


def week_start(d: date) -> date:
    """以一週一為開始 (中文常見紀錄)。"""
    return d - timedelta(days=d.weekday())


def classify(pct: float) -> tuple[str, float]:
    """依據達成率分類。

    < 0.8  → 「未達」
    0.8 – 1.1 → 「達成」
    > 1.1 → 「超標」
    返回 (狀態, 達成率)。
    """
    if pct < 0.8:
        return "未達", pct
    if pct > 1.1:
        return "超標", pct
    return "達成", pct


def format_pct(pct: float) -> str:
    return f"{(pct - 1) * 100:+.0f}%"
