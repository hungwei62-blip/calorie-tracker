"""Pure helpers for removing legacy meal-period records."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


LEGACY_MEAL_TYPES = frozenset({"早餐", "午餐", "晚餐", "宵夜"})


def legacy_record_row_numbers(rows: Sequence[dict[str, Any]]) -> list[int]:
    """Return 1-based worksheet row numbers, including the header row offset."""
    return [
        index
        for index, row in enumerate(rows, start=2)
        if str(row.get("meal_type", "")).strip() in LEGACY_MEAL_TYPES
    ]


def build_legacy_record_audit(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    row_numbers = legacy_record_row_numbers(rows)
    counts = {
        meal_type: sum(
            str(row.get("meal_type", "")).strip() == meal_type for row in rows
        )
        for meal_type in sorted(LEGACY_MEAL_TYPES)
    }
    return {
        "total_records": len(rows),
        "legacy_records": len(row_numbers),
        "remaining_records": len(rows) - len(row_numbers),
        "counts_by_meal_type": counts,
        "worksheet_row_numbers": row_numbers,
    }
