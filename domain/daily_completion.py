"""Pure rules for the student home's daily completion summary."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Any


@dataclass(frozen=True)
class DailyCompletion:
    weight_logged: bool
    water_logged: bool
    protein_logged: bool
    calories_logged: bool
    completed_count: int
    percentage: int
    bonus: bool


def _non_negative_number(value: Any) -> float:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return max(number, 0.0) if math.isfinite(number) else 0.0


def calculate_daily_completion(
    totals: Mapping[str, Any],
    goals: Mapping[str, Any],
    *,
    weight_logged: bool,
) -> DailyCompletion:
    """Calculate three-part nutrition progress plus an independent weight status."""
    water = _non_negative_number(totals.get("water"))
    protein = _non_negative_number(totals.get("protein"))
    calories = _non_negative_number(totals.get("calories"))
    protein_goal = _non_negative_number(goals.get("protein"))
    calorie_goal = _non_negative_number(goals.get("calorie"))

    water_goal = _non_negative_number(goals.get("water"))
    water_on_goal = water_goal > 0 and water >= water_goal
    protein_on_goal = protein_goal > 0 and protein >= protein_goal
    calorie_in_range = (
        calorie_goal > 0 and 0.9 <= calories / calorie_goal <= 1.1
    )
    nutrition_statuses = (water_on_goal, protein_on_goal, calorie_in_range)
    completed_count = sum(nutrition_statuses)
    return DailyCompletion(
        weight_logged=bool(weight_logged),
        water_logged=nutrition_statuses[0],
        protein_logged=nutrition_statuses[1],
        calories_logged=nutrition_statuses[2],
        completed_count=completed_count,
        percentage=round(completed_count / 3 * 100),
        bonus=completed_count == 3,
    )
