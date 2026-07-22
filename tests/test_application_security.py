from __future__ import annotations

from datetime import date
import csv
from io import StringIO

import pytest

from domain.validation import bounded_text, finite_non_negative, safe_csv_cell, valid_timestamp
from pages import coach as coach_pages
from services import application
from services.security import AuthContext


def test_student_can_only_write_own_records(monkeypatch):
    calls = []
    monkeypatch.setattr(application.sheets, "append_record", lambda **kwargs: calls.append(kwargs))
    context = AuthContext("student-1", "student")

    application.append_student_record(
        context,
        "student-1",
        timestamp="2026-07-19T10:00:00+08:00",
        meal_type="食物",
        food_summary="午餐",
        calories=500,
        protein=30,
        carb=0,
        fat=0,
        water_ml=0,
        image_url="",
        portion=1,
    )
    assert calls[0]["user_id"] == "student-1"

    with pytest.raises(application.PermissionDenied):
        application.append_student_record(context, "student-2")


def test_manager_target_is_revalidated(monkeypatch):
    monkeypatch.setattr(
        application.sheets,
        "get_student_for_manager",
        lambda user_id, manager_id: {"user_id": user_id} if (user_id, manager_id) == ("s1", "c1") else None,
    )
    coach = AuthContext("c1", "coach")
    assert application.require_managed_student(coach, "s1")["user_id"] == "s1"
    with pytest.raises(application.PermissionDenied):
        application.require_managed_student(coach, "s2")


def test_manager_cannot_update_goals_for_unmanaged_student(monkeypatch):
    monkeypatch.setattr(
        application.sheets,
        "get_student_for_manager",
        lambda _user_id, _manager_id: None,
    )
    monkeypatch.setattr(
        application.sheets,
        "update_user_goals",
        lambda *_args, **_kwargs: pytest.fail("repository must not be called"),
    )

    with pytest.raises(application.PermissionDenied):
        application.update_student_goals(
            AuthContext("coach-1", "coach"),
            "student-2",
            {"calorie": 1800, "protein": 120, "water": 2400},
        )


def test_common_validators_reject_invalid_values():
    with pytest.raises(ValueError):
        finite_non_negative(float("nan"), "calories")
    with pytest.raises(ValueError):
        valid_timestamp("not-a-date")
    with pytest.raises(ValueError):
        bounded_text("x" * 6, "field", limit=5)


@pytest.mark.parametrize("value", ["=SUM(A1:A2)", "+1+1", "-2+3", "@cmd"])
def test_csv_formula_cells_are_neutralized(value):
    assert safe_csv_cell(value).startswith("'")


def test_history_csv_neutralizes_dynamic_note_content():
    csv_bytes = coach_pages._build_history_csv(
        {"name": "=HYPERLINK(\"bad\")"},
        {},
        [],
        [],
        [{"timestamp": "2026-07-19", "coach_id": "c1", "note": "=1+1"}],
        date(2026, 7, 19),
        date(2026, 7, 19),
    )
    rows = list(csv.reader(StringIO(csv_bytes.decode("utf-8-sig"))))
    assert rows[-1][-1].startswith("'")
