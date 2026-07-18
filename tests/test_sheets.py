from __future__ import annotations

from datetime import date
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


def test_latest_weight_uses_timestamp_order(monkeypatch):
    sheets.get_latest_weight.clear()
    monkeypatch.setattr(
        sheets,
        "get_weight_records",
        lambda _user_id: [
            {"timestamp": "2026-07-19T08:00:00+08:00", "weight_kg": 60},
            {"timestamp": "2026-07-17", "weight_kg": 62},
            {"timestamp": "2026-07-18", "weight_kg": 61},
        ],
    )

    assert sheets.get_latest_weight("timestamp-order-student") == 60


def test_weight_by_date_returns_latest_same_day_measurement(monkeypatch):
    monkeypatch.setattr(
        sheets,
        "get_weight_records",
        lambda _user_id: [
            {"timestamp": "2026-07-19T08:00:00+08:00", "weight_kg": 61},
            {"timestamp": "2026-07-18T20:00:00+08:00", "weight_kg": 62},
            {"timestamp": "2026-07-19T21:00:00+08:00", "weight_kg": 60.5},
        ],
    )

    assert sheets.get_weight_by_date("student", date(2026, 7, 19)) == 60.5


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
        "2026-07-19T12:00:00+08:00",
        {},
        sheets.FIXED_PRIMARY_COACH_ID,
    )
    assert (
        ws.appended_rows[0][sheets.USERS_HEADERS.index("coach_id")]
        == "u_20260629165506_4b525f9c"
    )


def test_registration_appends_user_and_weight_in_one_batch(monkeypatch):
    class Worksheet:
        def __init__(self, sheet_id):
            self.id = sheet_id

    class Spreadsheet:
        def __init__(self):
            self.calls = []

        def batch_update(self, body):
            self.calls.append(body)

    spreadsheet = Spreadsheet()
    worksheets = {"Users": Worksheet(1), "Weight": Worksheet(2)}
    monkeypatch.setattr(sheets, "_get_sheet", lambda: spreadsheet)
    monkeypatch.setattr(
        sheets,
        "_ensure_worksheet",
        lambda _sh, title, _headers: worksheets[title],
    )
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    sheets.append_user_with_initial_weight(
        "u1",
        "account",
        "name",
        "hash",
        "2026-07-19T12:00:00+08:00",
        {},
        sheets.FIXED_PRIMARY_COACH_ID,
        61.5,
    )

    requests = spreadsheet.calls[0]["requests"]
    assert [request["appendCells"]["sheetId"] for request in requests] == [1, 2]


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


def test_training_append_uses_new_categorized_schema(monkeypatch):
    from conftest import FakeWorksheet

    ws = FakeWorksheet()
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: ws)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    sheets.append_training(
        "2026-07-18",
        "student-1",
        ["有氧訓練", "重量訓練"],
        strength_detail="深蹲 4 組",
        cardio_detail="跑步 20 分鐘",
    )

    assert sheets.TRAINING_HEADERS == [
        "timestamp", "user_id", "training_types", "strength_detail",
        "cardio_detail", "other_detail",
    ]
    assert ws.appended_rows == [[
        "2026-07-18", "student-1", "重量訓練、有氧訓練",
        "深蹲 4 組", "跑步 20 分鐘", "",
    ]]


@pytest.mark.parametrize(
    ("training_types", "details", "message"),
    [
        ([], {}, "至少選擇"),
        (["重量訓練"], {}, "重量訓練內容"),
        (["未知類型"], {"other_detail": "測試"}, "不支援"),
    ],
)
def test_training_validation_rejects_invalid_values(
    monkeypatch, training_types, details, message
):
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    with pytest.raises(ValueError, match=message):
        sheets.append_training("2026-07-18", "student-1", training_types, **details)


def test_training_records_are_normalized_and_formatted(monkeypatch):
    from conftest import FakeWorksheet

    ws = FakeWorksheet([
        sheets.TRAINING_HEADERS,
        [
            "2026-07-18", "student-1", "重量訓練、有氧訓練",
            "深蹲 4 組", "跑步 20 分鐘", "",
        ],
    ])
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: ws)

    records = sheets.get_training_records.__wrapped__("student-1")

    assert records[0]["training_types"] == ["重量訓練", "有氧訓練"]
    assert sheets.format_training_record(records[0]) == (
        "重量訓練：深蹲 4 組；有氧訓練：跑步 20 分鐘"
    )


def test_training_update_overwrites_all_category_fields(monkeypatch):
    from conftest import FakeWorksheet

    ws = FakeWorksheet([
        sheets.TRAINING_HEADERS,
        ["2026-07-18", "student-1", "重量訓練", "深蹲", "", ""],
    ])
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: ws)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    assert sheets.update_training(
        "2026-07-18", "student-1", ["有氧訓練"], cardio_detail="單車 30 分鐘"
    ) is True
    assert ws.updated_cells == [
        (2, 3, "有氧訓練"), (2, 4, ""),
        (2, 5, "單車 30 分鐘"), (2, 6, ""),
    ]
