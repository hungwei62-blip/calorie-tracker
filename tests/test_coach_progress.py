from __future__ import annotations

import pytest
import inspect

from pages.coach import (
    build_coach_welcome_html,
    build_coach_nutrient_progress_html,
    build_coach_student_card_html,
    calculate_coach_nutrient_progress,
)
from ui import coach_student_card as card_component
from ui import styles


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
    assert markup.index('class="coach-nutrient-track"') < markup.index(
        'class="coach-nutrient-value"'
    )


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
    stylesheet = card_component._CARD_CSS

    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in stylesheet
    assert "@media (max-width: 480px)" in stylesheet
    assert ".capsule-track" not in stylesheet


def test_coach_welcome_uses_avatar_and_escapes_dynamic_values():
    markup = build_coach_welcome_html(
        '<教練 & "Prime">', 'data:image/jpeg;base64,a&b'
    )

    assert 'src="data:image/jpeg;base64,a&amp;b"' in markup
    assert '&lt;教練 &amp; &quot;Prime&quot;&gt;' in markup
    assert "width:56px;height:56px" in markup
    assert "object-fit:cover" in markup


def test_coach_overview_matches_student_header_and_enlarges_values():
    coach_pages = __import__("pages.coach", fromlist=["page_coach_overview"])
    source = inspect.getsource(coach_pages.page_coach_overview)
    stylesheet = card_component._CARD_CSS

    assert 'key="coach_overview_header"' in source
    assert 'st.header("本日學員狀態")' in source
    assert "section-title" not in source
    assert "coach_student_card(" in source
    assert "font-size: 14px" in stylesheet
    assert "font-size: 17px" in stylesheet
    assert "font-size: 13px" in stylesheet
    assert "font-size: 15px" in stylesheet
    assert "font-variant-numeric: tabular-nums" in stylesheet
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in stylesheet


def test_coach_card_component_uses_ccv2_toggle_and_accessible_button():
    assert 'type="button"' in card_component._CARD_HTML
    assert 'aria-expanded="false"' in card_component._CARD_HTML
    assert 'setTriggerValue("toggle"' in card_component._CARD_JS
    assert "Streamlit.setComponentValue" not in card_component._CARD_JS
    assert "window.Streamlit" not in card_component._CARD_JS
    assert ':focus-visible' in card_component._CARD_CSS


def test_coach_card_wrapper_normalizes_values_and_returns_toggle(monkeypatch):
    mounted = {}

    def fake_component(**kwargs):
        mounted.update(kwargs)
        return {"toggle": "student-1"}

    monkeypatch.setattr(card_component, "_COACH_STUDENT_CARD", fake_component)

    toggled = card_component.coach_student_card(
        student_id="student-1",
        name="小明",
        has_training=True,
        totals={"calories": 900, "water": -1, "protein": 60},
        goals={"calorie": 1800, "water": 2400, "protein": 120},
        expanded=False,
        key="student-card-1",
    )

    assert toggled is True
    assert mounted["data"]["student_id"] == "student-1"
    assert mounted["data"]["nutrients"][0]["percentage"] == 50
    assert mounted["data"]["nutrients"][1]["value_text"] == "0 / 2,400 ml"
    assert mounted["on_toggle_change"] is not None


def test_coach_goal_editor_updates_only_three_positive_goals():
    coach_pages = __import__("pages.coach", fromlist=["_render_student_goal_editor"])
    source = inspect.getsource(coach_pages._render_student_goal_editor)

    assert source.count("min_value=1.0") == 3
    assert '{"calorie": calorie, "protein": protein, "water": water}' in source
    assert '"carb"' not in source
    assert '"fat"' not in source
    assert "_clear_analysis_cache()" in source


def test_admin_health_rows_and_coach_history_top_spacing_are_scoped():
    stylesheet = "\n".join(
        value for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str)
    )
    overview_source = inspect.getsource(
        __import__("pages.coach", fromlist=["page_coach_overview"]).page_coach_overview
    )

    assert 'key="admin_health_status"' in overview_source
    assert ".st-key-admin_health_status .admin-health-row" in stylesheet
    assert "font-size: 12px !important;" in stylesheet
    assert ":has(.st-key-coach_student_history_page)" in stylesheet
