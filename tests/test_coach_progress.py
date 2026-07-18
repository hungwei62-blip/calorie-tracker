from __future__ import annotations

import pytest

from pages.coach import (
    build_coach_nutrient_progress_html,
    build_coach_student_card_html,
    calculate_coach_nutrient_progress,
)


@pytest.mark.parametrize(
    ("actual", "goal", "expected"),
    [
        (50, 100, (50.0, 100.0, 50.0)),
        (100, 100, (100.0, 100.0, 100.0)),
        (140, 100, (140.0, 100.0, 100.0)),
        (-10, 100, (0.0, 100.0, 0.0)),
        (50, 0, (50.0, 0.0, 0.0)),
        ("bad", None, (0.0, 0.0, 0.0)),
    ],
)
def test_coach_nutrient_progress_is_safe_and_clamped(actual, goal, expected):
    assert calculate_coach_nutrient_progress(actual, goal) == expected


def test_coach_nutrient_html_shows_values_color_and_accessible_progress():
    markup = build_coach_nutrient_progress_html(
        "卡路里", 2300, 2000, "kcal", "#ff6068"
    )

    assert "卡路里" in markup
    assert "2300 / 2000 kcal" in markup
    assert "width:100.00%" in markup
    assert "background:#ff6068" in markup
    assert 'role="progressbar"' in markup
    assert 'aria-valuenow="100"' in markup


def test_coach_nutrient_html_uses_dash_when_goal_is_missing():
    markup = build_coach_nutrient_progress_html(
        "水", 350, None, "ml", "#90cbfb"
    )

    assert "350 / — ml" in markup
    assert "width:0.00%" in markup


def test_coach_student_card_has_three_ordered_metrics_and_escapes_name():
    markup = build_coach_student_card_html(
        "王<小明>",
        True,
        {"calories": 800, "water": 1200, "protein": 60},
        {"calorie": 2000, "water": 2400, "protein": 120},
    )

    assert "王&lt;小明&gt;" in markup
    assert markup.count('class="coach-nutrient"') == 3
    assert markup.index("卡路里") < markup.index("水") < markup.index("蛋白質")
    assert "#ff6068" in markup
    assert "#90cbfb" in markup
    assert "#bbf250" in markup
    assert "Trained" in markup
    assert "capsule-" not in markup


def test_coach_overview_css_keeps_metrics_in_one_row():
    source = __import__("inspect").getsource(
        __import__("pages.coach", fromlist=["page_coach_overview"]).page_coach_overview
    )

    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in source
    assert "@media (max-width: 480px)" in source
    assert ".capsule-track" not in source
