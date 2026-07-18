from __future__ import annotations

import pytest

from domain.daily_completion import calculate_daily_completion
from pages.student import build_daily_completion_html


@pytest.mark.parametrize(
    ("totals", "completed_count", "percentage"),
    [
        ({}, 0, 0),
        ({"water": 250}, 1, 33),
        ({"water": 250, "protein": 20}, 2, 67),
        ({"water": 250, "protein": 20, "calories": 400}, 3, 100),
    ],
)
def test_daily_completion_counts_only_three_nutrition_records(
    totals, completed_count, percentage
):
    result = calculate_daily_completion(totals, {}, weight_logged=True)

    assert result.weight_logged is True
    assert result.completed_count == completed_count
    assert result.percentage == percentage


def test_weight_status_does_not_change_completion_percentage():
    without_weight = calculate_daily_completion(
        {"water": 300}, {}, weight_logged=False
    )
    with_weight = calculate_daily_completion(
        {"water": 300}, {}, weight_logged=True
    )

    assert without_weight.percentage == with_weight.percentage == 33
    assert without_weight.weight_logged is False
    assert with_weight.weight_logged is True


@pytest.mark.parametrize("calories", [1800, 2000, 2200])
def test_bonus_includes_calorie_range_boundaries(calories):
    result = calculate_daily_completion(
        {"protein": 120, "calories": calories},
        {"protein": 120, "calorie": 2000},
        weight_logged=False,
    )

    assert result.bonus is True


@pytest.mark.parametrize(
    ("totals", "goals"),
    [
        ({"protein": 119, "calories": 2000}, {"protein": 120, "calorie": 2000}),
        ({"protein": 120, "calories": 1799}, {"protein": 120, "calorie": 2000}),
        ({"protein": 120, "calories": 2201}, {"protein": 120, "calorie": 2000}),
        ({"protein": 120, "calories": 2000}, {"protein": 0, "calorie": 0}),
    ],
)
def test_bonus_requires_both_valid_goal_conditions(totals, goals):
    assert calculate_daily_completion(
        totals, goals, weight_logged=False
    ).bonus is False


def test_completion_html_has_four_unlabelled_icons_and_accessible_statuses():
    completion = calculate_daily_completion(
        {"water": 300, "calories": 500},
        {"protein": 100, "calorie": 500},
        weight_logged=True,
    )
    markup = build_daily_completion_html(completion)

    assert "今日完成度" in markup
    assert "飲食完成 2 / 3 項" in markup
    assert 'aria-valuenow="67"' in markup
    assert markup.count('role="listitem"') == 4
    assert 'aria-label="體重：已完成"' in markup
    assert 'aria-label="蛋白質：未完成"' in markup
    assert "daily-completion-label" not in markup
    assert " has-bonus" not in markup
