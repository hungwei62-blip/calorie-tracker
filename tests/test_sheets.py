from __future__ import annotations

import inspect

import pytest

import pages.student as student_pages
from services import sheets


def _install_fake_users(monkeypatch, worksheet, rows):
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: worksheet)
    monkeypatch.setattr(sheets, "get_users_rows", lambda: rows)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)


def test_bmr_uses_header_column(monkeypatch, student_row):
    from conftest import FakeWorksheet

    ws = FakeWorksheet()
    _install_fake_users(monkeypatch, ws, [student_row])

    assert sheets.update_user_bmr(student_row["user_id"], 1550) is True
    assert ws.updated_cells == [(2, sheets.USERS_HEADERS.index("bmr") + 1, 1550.0)]


def test_goals_update_correct_columns_in_one_batch(monkeypatch, student_row):
    from conftest import FakeWorksheet

    ws = FakeWorksheet()
    _install_fake_users(monkeypatch, ws, [student_row])
    goals = {"calorie": 1900, "protein": 130, "carb": 180, "fat": 55, "water": 2500}

    assert sheets.update_user_goals(student_row["user_id"], goals) is True
    assert {col: value for _row, col, value in ws.updated_cells} == {
        sheets.USERS_HEADERS.index("daily_calorie_goal") + 1: 1900.0,
        sheets.USERS_HEADERS.index("daily_protein_goal") + 1: 130.0,
        sheets.USERS_HEADERS.index("daily_carb_goal") + 1: 180.0,
        sheets.USERS_HEADERS.index("daily_fat_goal") + 1: 55.0,
        sheets.USERS_HEADERS.index("daily_water_goal") + 1: 2500.0,
    }


def test_negative_goal_is_rejected(monkeypatch, student_row):
    from conftest import FakeWorksheet

    _install_fake_users(monkeypatch, FakeWorksheet(), [student_row])
    with pytest.raises(ValueError, match="不可小於 0"):
        sheets.update_user_goals(student_row["user_id"], {"protein": -1})


def test_coach_only_sees_owned_students(monkeypatch, student_row):
    other = dict(student_row, user_id="student_2", coach_id="coach_2")
    unassigned = dict(student_row, user_id="student_3", coach_id="")
    monkeypatch.setattr(sheets, "get_users_rows", lambda: [student_row, other, unassigned])

    assert sheets.get_students_for_coach("coach_1") == [student_row]
    assert sheets.get_student_for_coach("student_2", "coach_1") is None


def test_admin_sees_all_students(monkeypatch, student_row):
    other = dict(student_row, user_id="student_2", coach_id="coach_2")
    admin = dict(student_row, user_id="admin_1", role="admin", coach_id="")
    rows = [student_row, other, admin]
    monkeypatch.setattr(sheets, "get_users_rows", lambda: rows)
    monkeypatch.setattr(sheets, "get_user_role", lambda user_id: "admin" if user_id == "admin_1" else "student")

    assert sheets.get_students_for_manager("admin_1") == [student_row, other]
    assert sheets.get_student_for_manager("student_2", "admin_1") == other


def test_append_user_persists_coach_id(monkeypatch):
    from conftest import FakeWorksheet

    ws = FakeWorksheet()
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: ws)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)
    sheets.append_user(
        "u1",
        "account",
        "name",
        "hash",
        "now",
        {},
        sheets.FIXED_PRIMARY_COACH_ID,
    )
    assert (
        ws.appended_rows[0][sheets.USERS_HEADERS.index("coach_id")]
        == "u_20260629165506_4b525f9c"
    )


def test_primary_coach_is_fixed_and_ignores_streamlit_secrets(monkeypatch):
    monkeypatch.setattr(
        sheets.st,
        "secrets",
        {"PRIMARY_COACH_ID": "different_coach"},
    )
    monkeypatch.setattr(
        sheets,
        "get_users_rows",
        lambda: [
            {
                "user_id": sheets.FIXED_PRIMARY_COACH_ID,
                "role": "coach",
            }
        ],
    )

    assert sheets.get_primary_coach_id() == "u_20260629165506_4b525f9c"
    assert "st.secrets" not in inspect.getsource(sheets.get_primary_coach_id)


def test_primary_coach_must_exist(monkeypatch):
    monkeypatch.setattr(sheets, "get_users_rows", lambda: [])

    with pytest.raises(EnvironmentError, match="固定主教練帳號不存在"):
        sheets.get_primary_coach_id()


@pytest.mark.parametrize("role", ["", "student", "admin"])
def test_primary_coach_must_keep_coach_role(monkeypatch, role):
    monkeypatch.setattr(
        sheets,
        "get_users_rows",
        lambda: [
            {
                "user_id": sheets.FIXED_PRIMARY_COACH_ID,
                "role": role,
            }
        ],
    )

    with pytest.raises(EnvironmentError, match="role=coach"):
        sheets.get_primary_coach_id()


def test_registration_uses_validated_fixed_primary_coach():
    source = inspect.getsource(student_pages.page_login)

    assert "primary_coach_id = sheets.get_primary_coach_id()" in source
    assert "coach_id=primary_coach_id" in source
