from __future__ import annotations

from services.user_migration import build_audit, has_shifted_goals, repaired_user


def test_shifted_user_is_repaired_and_assigned():
    row = {
        "user_id": "u_20260717123045_deadbeef",
        "created_at": "1450",
        "bmr": "1900",
        "daily_calorie_goal": "120",
        "daily_protein_goal": "200",
        "daily_carb_goal": "55",
        "daily_fat_goal": "2400",
        "daily_water_goal": "2000",
        "role": "student",
        "coach_id": "",
    }
    repaired, warnings = repaired_user(row, "coach_1")
    assert has_shifted_goals(row)
    assert repaired["created_at"] == "2026-07-17T12:30:45+08:00"
    assert [repaired[key] for key in (
        "bmr", "daily_calorie_goal", "daily_protein_goal", "daily_carb_goal",
        "daily_fat_goal", "daily_water_goal",
    )] == ["1450", "1900", "200", "55", "2400", "2000"]
    assert repaired["coach_id"] == "coach_1"
    assert warnings == []


def test_normal_user_values_are_not_shifted(student_row):
    repaired, _ = repaired_user(student_row, "coach_1")
    assert repaired == student_row


def test_audit_rejects_non_coach_primary(student_row):
    try:
        build_audit([student_row], "missing")
    except ValueError as exc:
        assert "role=coach" in str(exc)
    else:
        raise AssertionError("expected ValueError")
