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


@pytest.mark.parametrize("text", ["", "not json", "{}"])
def test_invalid_gemini_response_is_rejected(text):
    with pytest.raises(RuntimeError):
        gemini._parse_response(SimpleNamespace(text=text))


def test_gemini_atwater_fallback():
    response = SimpleNamespace(text='{"food_summary":"餐點","calories":0,"protein":10,"carb":20,"fat":5}')
    parsed = gemini._parse_response(response)
    assert parsed["calories"] == 165
