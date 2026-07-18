from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from services import gemini, metrics


def test_daily_totals_filter_by_student_records():
    records = [
        {"timestamp": "2026-07-17T08:00:00", "calories": 500, "protein": 30, "water_ml": 500},
        {"timestamp": "2026-07-18T08:00:00", "calories": 800, "protein": 40, "water_ml": 700},
    ]
    selected = metrics.filter_records(records, date(2026, 7, 17), date(2026, 7, 17))
    totals = metrics.sum_totals(selected)
    assert (totals.calories, totals.protein, totals.water) == (500, 30, 500)


@pytest.mark.parametrize("text", ["", "not json", "{}", "[]"])
def test_invalid_gemini_response_is_rejected(text):
    with pytest.raises(RuntimeError):
        gemini._parse_response(SimpleNamespace(text=text))


def test_valid_gemini_food_response_is_normalized():
    response = SimpleNamespace(
        text='{"is_food":true,"food_summary":" 餐點 ","calories":520,"protein":31}'
    )
    parsed = gemini._parse_response(response)
    assert parsed == {
        "is_food": True,
        "food_summary": "餐點",
        "calories": 520.0,
        "protein": 31.0,
    }


def test_non_food_gemini_response_is_valid_but_has_zero_nutrition():
    response = SimpleNamespace(
        text='{"is_food":false,"food_summary":"無法辨識食物","calories":0,"protein":0}'
    )
    assert gemini._parse_response(response)["is_food"] is False


@pytest.mark.parametrize(
    "payload",
    [
        '{"is_food":true,"food_summary":"餐點","calories":-1,"protein":10}',
        '{"is_food":true,"food_summary":"餐點","calories":"bad","protein":10}',
        '{"is_food":true,"food_summary":"餐點","calories":0,"protein":0}',
        '{"is_food":"yes","food_summary":"餐點","calories":100,"protein":10}',
        '{"is_food":true,"food_summary":"","calories":100,"protein":10}',
    ],
)
def test_unreliable_gemini_values_are_rejected(payload):
    with pytest.raises(RuntimeError):
        gemini._parse_response(SimpleNamespace(text=payload))
