from datetime import date

from domain.history import aggregate_daily
from domain.nutrition import calculate_bmr, calculate_goals, calculate_tdee


def test_tdee_and_goals_are_pure_calculations():
    bmr = calculate_bmr(70, 175, 30, "男")
    tdee = calculate_tdee(bmr, "每週運動 3-5 天")
    goals = calculate_goals(70, tdee, "減脂")
    assert bmr > 0
    assert tdee > bmr
    assert goals["calorie"] == tdee - 300
    assert goals["protein"] == 140
    assert goals["water"] == 2800


def test_history_aggregate_includes_empty_days():
    result = aggregate_daily(
        [{"timestamp": "2026-07-17T12:00:00", "calories": 500, "water_ml": 600}],
        date(2026, 7, 17),
        date(2026, 7, 18),
    )
    assert result[date(2026, 7, 17)]["calorie"] == 500
    assert result[date(2026, 7, 18)]["calorie"] == 0
