from datetime import date

import pytest

from domain.history import aggregate_daily
from domain.nutrition import (
    CALORIE_DEFICIT_OPTIONS,
    DEFAULT_CALORIE_DEFICIT_LABEL,
    calculate_bmr,
    calculate_goals,
    calculate_tdee,
)


def test_tdee_and_goals_are_pure_calculations():
    bmr = calculate_bmr(70, 175, 30, "男")
    tdee = calculate_tdee(bmr, "每週運動 3-5 天")
    goals = calculate_goals(70, tdee, bmr, 300)
    assert bmr > 0
    assert tdee > bmr
    assert goals["calorie"] == tdee - 300
    assert goals["protein"] == 140
    assert goals["water"] == 2800
    assert goals["carb"] == 0
    assert goals["fat"] == 0


def test_calorie_deficit_options_have_expected_labels_and_default():
    assert CALORIE_DEFICIT_OPTIONS == {
        "溫和（-200 大卡）": 200,
        "標準（-300 大卡）": 300,
        "積極（-400 大卡）": 400,
    }
    assert DEFAULT_CALORIE_DEFICIT_LABEL == "標準（-300 大卡）"


@pytest.mark.parametrize(
    ("deficit", "expected"),
    [(200, 2200), (300, 2100), (400, 2000)],
)
def test_calorie_goal_supports_three_deficit_levels(deficit, expected):
    goals = calculate_goals(70, tdee=2400, bmr=1700, calorie_deficit=deficit)

    assert goals["calorie"] == expected


def test_calorie_goal_never_drops_below_bmr():
    goals = calculate_goals(60, tdee=2050, bmr=1800, calorie_deficit=400)

    assert goals["calorie"] == 1800


@pytest.mark.parametrize("invalid_deficit", [0, 100, 250, 500, "300"])
def test_calorie_goal_rejects_unsupported_deficit(invalid_deficit):
    with pytest.raises(ValueError, match="200、300 或 400"):
        calculate_goals(70, 2400, 1700, invalid_deficit)


def test_history_aggregate_includes_empty_days():
    result = aggregate_daily(
        [{"timestamp": "2026-07-17T12:00:00", "calories": 500, "water_ml": 600}],
        date(2026, 7, 17),
        date(2026, 7, 18),
    )
    assert result[date(2026, 7, 17)]["calorie"] == 500
    assert result[date(2026, 7, 18)]["calorie"] == 0
