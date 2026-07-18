"""Pure validation helpers shared by UI and persistence services."""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any


ALLOWED_MEAL_TYPES = frozenset({"食物", "飲水"})
TEXT_LIMITS = {
    "username": 64,
    "name": 80,
    "food_summary": 500,
    "note": 2000,
    "training_detail": 500,
}


def valid_timestamp(value: Any, field_name: str = "timestamp") -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} 不可為空")
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} 格式無效") from exc
    return text


def finite_non_negative(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} 必須是數字")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} 必須是數字") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{field_name} 必須是有限數字")
    if parsed < 0:
        raise ValueError(f"{field_name} 不可小於 0")
    return parsed


def positive_number(value: Any, field_name: str) -> float:
    parsed = finite_non_negative(value, field_name)
    if parsed <= 0:
        raise ValueError(f"{field_name} 必須大於 0")
    return parsed


def bounded_text(
    value: Any,
    field_name: str,
    *,
    limit: int,
    required: bool = True,
) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{field_name} 不可為空")
    if len(text) > limit:
        raise ValueError(f"{field_name} 不可超過 {limit} 個字元")
    return text


def meal_type(value: Any) -> str:
    text = str(value or "").strip()
    if text not in ALLOWED_MEAL_TYPES:
        raise ValueError("紀錄種類只能是食物或飲水")
    return text


def safe_csv_cell(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    normalized = value.replace("\x00", "")
    if normalized.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + normalized
    return normalized
