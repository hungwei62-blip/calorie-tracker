from __future__ import annotations

import pytest

from domain.daily_completion import calculate_daily_completion
from pages.student import build_daily_completion_html


@pytest.mark.parametrize(
    ("totals", "goals", "completed_count", "percentage"),
    [
        ({}, {"water": 2000, "protein": 100, "calorie": 2000}, 0, 0),
        (
            {"water": 2000},
            {"water": 2000, "protein": 100, "calorie": 2000},
            1,
            33,
        ),
        (
            {"water": 2000, "protein": 100},
            {"water": 2000, "protein": 100, "calorie": 2000},
            2,
            67,
        ),
        (
            {"water": 2000, "protein": 100, "calories": 2000},
            {"water": 2000, "protein": 100, "calorie": 2000},
            3,
            100,
        ),
    ],
)
def test_daily_completion_counts_only_goals_that_are_reached(
    totals, goals, completed_count, percentage
):
    result = calculate_daily_completion(totals, goals, weight_logged=True)

    assert result.weight_logged is True
    assert result.completed_count == completed_count
    assert result.percentage == percentage


def test_weight_status_does_not_change_completion_percentage():
    without_weight = calculate_daily_completion(
        {"water": 300}, {"water": 300}, weight_logged=False
    )
    with_weight = calculate_daily_completion(
        {"water": 300}, {"water": 300}, weight_logged=True
    )

    assert without_weight.percentage == with_weight.percentage == 33
    assert without_weight.weight_logged is False
    assert with_weight.weight_logged is True


@pytest.mark.parametrize("calories", [1800, 2000, 2200])
def test_calorie_goal_includes_ten_percent_boundaries(calories):
    result = calculate_daily_completion(
        {"calories": calories},
        {"calorie": 2000},
        weight_logged=False,
    )

    assert result.calories_logged is True
    assert result.percentage == 33


@pytest.mark.parametrize(
    ("totals", "goals", "field"),
    [
        ({"water": 1999}, {"water": 2000}, "water_logged"),
        ({"protein": 119}, {"protein": 120}, "protein_logged"),
        ({"calories": 1799}, {"calorie": 2000}, "calories_logged"),
        ({"calories": 2201}, {"calorie": 2000}, "calories_logged"),
        ({"water": 2000}, {"water": 0}, "water_logged"),
        ({"protein": 120}, {"protein": float("nan")}, "protein_logged"),
        ({"calories": 2000}, {"calorie": "invalid"}, "calories_logged"),
    ],
)
def test_below_range_or_invalid_goals_do_not_complete(totals, goals, field):
    result = calculate_daily_completion(totals, goals, weight_logged=False)

    assert getattr(result, field) is False
    assert result.percentage == 0


@pytest.mark.parametrize(
    ("field", "actual", "goal"),
    [
        ("water", 2000, 2000),
        ("water", 2500, 2000),
        ("protein", 120, 120),
        ("protein", 140, 120),
    ],
)
def test_water_and_protein_complete_at_or_above_goal(field, actual, goal):
    result = calculate_daily_completion(
        {field: actual}, {field: goal}, weight_logged=False
    )

    assert getattr(result, f"{field}_logged") is True
    assert result.percentage == 33


def test_bonus_requires_all_three_goals():
    goals = {"water": 2000, "protein": 120, "calorie": 2000}
    partial = calculate_daily_completion(
        {"protein": 120, "calories": 2000}, goals, weight_logged=False
    )
    complete = calculate_daily_completion(
        {"water": 2000, "protein": 120, "calories": 2000},
        goals,
        weight_logged=False,
    )

    assert partial.bonus is False
    assert complete.bonus is True


def test_completion_html_has_four_unlabelled_icons_and_accessible_statuses():
    completion = calculate_daily_completion(
        {"water": 300, "calories": 500},
        {"water": 300, "protein": 100, "calorie": 500},
        weight_logged=True,
    )
    markup = build_daily_completion_html(
        completion,
        {"calories": 1234.4, "protein": 78.6, "water": 2000},
    )

    assert "今日記錄完成度" in markup
    assert '<details class="daily-completion-details">' in markup
    assert '<summary class="daily-completion-card' in markup
    assert 'aria-label="今日記錄完成度，點擊查看今日輸入數值"' in markup
    assert 'aria-label="今日輸入數值"' in markup
    assert "熱量</span><strong>1,234 kcal" in markup
    assert "蛋白質</span><strong>79 g" in markup
    assert "飲水</span><strong>2,000 ml" in markup
    assert "今日完成度" not in markup
    assert "目標達成 2 / 3 項" in markup
    assert 'aria-valuenow="67"' in markup
    assert markup.count('role="listitem"') == 4
    assert 'aria-label="體重：已完成"' in markup
    assert 'aria-label="蛋白質：未完成"' in markup
    assert "daily-completion-label" not in markup
    assert " has-bonus" not in markup


@pytest.mark.parametrize(
    ("totals", "expected_values"),
    [
        ({}, ("0 kcal", "0 g", "0 ml")),
        (
            {"calories": -10, "protein": float("nan"), "water": "invalid"},
            ("0 kcal", "0 g", "0 ml"),
        ),
    ],
)
def test_completion_html_safely_formats_missing_or_invalid_totals(
    totals, expected_values
):
    completion = calculate_daily_completion({}, {}, weight_logged=False)

    markup = build_daily_completion_html(completion, totals)

    for expected in expected_values:
        assert f"<strong>{expected}</strong>" in markup
