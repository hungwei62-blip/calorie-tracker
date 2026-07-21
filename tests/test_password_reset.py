from __future__ import annotations

import inspect

import pytest

import app
from pages import coach as coach_pages
from pages import student as student_pages
from services import application, auth, sheets
from services.security import AuthContext


def test_temporary_password_is_strong_and_avoids_ambiguous_characters():
    password = auth.make_temporary_password()

    assert len(password) == 12
    assert set(password) <= set(auth.TEMPORARY_PASSWORD_ALPHABET)
    assert not set(password) & set("0O1Il")


def test_unknown_account_reset_does_not_create_request(monkeypatch):
    created = []
    monkeypatch.setattr(sheets, "get_users_rows", lambda: [])
    monkeypatch.setattr(sheets, "get_password_reset_requests", lambda _status: [])
    monkeypatch.setattr(
        sheets,
        "create_password_reset_request",
        lambda *args: created.append(args),
    )
    monkeypatch.setattr(application, "log_event", lambda *args, **kwargs: "id")

    assert application.request_password_reset("missing") is None
    assert created == []


def test_coach_cannot_approve_another_coachs_student(monkeypatch, student_row):
    other_student = dict(student_row, user_id="student_2", coach_id="coach_2")
    monkeypatch.setattr(
        sheets,
        "get_password_reset_requests",
        lambda _status: [{"request_id": "other", "user_id": "student_2"}],
    )
    monkeypatch.setattr(
        sheets, "get_student_for_manager", lambda _user_id, _manager_id: None
    )

    with pytest.raises(application.PermissionDenied, match="沒有權限"):
        application.approve_password_reset(
            AuthContext(user_id="coach_1", role="coach"), "other"
        )


def test_manager_only_sees_owned_students_reset_requests(monkeypatch, student_row):
    other_student = dict(student_row, user_id="student_2", coach_id="coach_2")
    monkeypatch.setattr(
        sheets, "get_students_for_manager", lambda _manager_id: [student_row]
    )
    monkeypatch.setattr(
        sheets,
        "get_password_reset_requests",
        lambda _status: [
            {"request_id": "owned", "user_id": student_row["user_id"]},
            {"request_id": "other", "user_id": other_student["user_id"]},
        ],
    )

    requests = application.get_password_reset_requests(
        AuthContext(user_id="coach_1", role="coach")
    )

    assert [request["request_id"] for request in requests] == ["owned"]
    assert requests[0]["student"] == student_row


def test_approval_hashes_temporary_password_and_sets_change_flag(
    monkeypatch, student_row
):
    approvals = []
    monkeypatch.setattr(
        application,
        "_managed_password_reset",
        lambda _context, _request_id: (
            {"request_id": "reset-1", "user_id": student_row["user_id"]},
            student_row,
        ),
    )
    monkeypatch.setattr(auth, "make_temporary_password", lambda: "TempPass2345")
    monkeypatch.setattr(auth, "hash_password", lambda value: f"hash:{value}")
    monkeypatch.setattr(
        sheets,
        "approve_password_reset_request",
        lambda *args, **kwargs: approvals.append((args, kwargs)) or True,
    )
    monkeypatch.setattr(application, "log_event", lambda *args, **kwargs: "id")

    temporary = application.approve_password_reset(
        AuthContext(user_id="coach_1", role="coach"), "reset-1"
    )

    assert temporary == "TempPass2345"
    assert approvals[0][0] == (
        "reset-1",
        student_row["user_id"],
        "hash:TempPass2345",
    )
    assert approvals[0][1]["resolved_by"] == "coach_1"


def test_password_update_writes_hash_and_change_flag(monkeypatch, student_row):
    from conftest import FakeWorksheet

    worksheet = FakeWorksheet()
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: worksheet)
    monkeypatch.setattr(sheets, "get_users_rows", lambda: [student_row])
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    assert sheets.update_user_password(
        student_row["user_id"], "new-hash", must_change_password=True
    )
    assert worksheet.updated_cells == [
        (2, sheets.USERS_HEADERS.index("password_hash") + 1, "new-hash"),
        (2, sheets.USERS_HEADERS.index("must_change_password") + 1, True),
    ]


def test_reset_approval_is_one_atomic_sheets_batch(monkeypatch, student_row):
    class Worksheet:
        def __init__(self, sheet_id, values):
            self.id = sheet_id
            self.values = values

        def get_all_values(self):
            return [list(row) for row in self.values]

    class Spreadsheet:
        def __init__(self):
            self.calls = []

        def batch_update(self, body):
            self.calls.append(body)

    spreadsheet = Spreadsheet()
    users = Worksheet(1, [sheets.USERS_HEADERS])
    resets = Worksheet(
        2,
        [
            sheets.PASSWORD_RESET_HEADERS,
            ["reset-1", student_row["user_id"], "2026-07-22", "pending", "", ""],
        ],
    )
    monkeypatch.setattr(sheets, "_get_sheet", lambda: spreadsheet)
    monkeypatch.setattr(
        sheets,
        "_ensure_worksheet",
        lambda _sh, title, _headers: {
            "Users": users,
            "PasswordResetRequests": resets,
        }[title],
    )
    monkeypatch.setattr(sheets, "get_users_rows", lambda: [student_row])
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    assert sheets.approve_password_reset_request(
        "reset-1",
        student_row["user_id"],
        "temporary-password-hash",
        resolved_at="2026-07-22T12:00:00+08:00",
        resolved_by="coach_1",
    )
    requests = spreadsheet.calls[0]["requests"]
    assert len(requests) == 5
    assert [
        request["updateCells"]["range"]["sheetId"] for request in requests
    ] == [1, 1, 2, 2, 2]
    assert "temporary-password-hash" in str(requests)


def test_reset_routes_are_exposed_in_ui_and_normal_navigation_is_blocked():
    login_source = inspect.getsource(student_pages.page_login)
    coach_source = inspect.getsource(coach_pages._render_password_reset_requests)
    app_source = inspect.getsource(app.main)

    assert 'st.button("忘記密碼"' in login_source
    assert "若帳號資料正確" in login_source
    assert "approve_password_reset" in coach_source
    assert "temporary_password_notice" in coach_source
    assert "user_must_change_password" in app_source
    assert "page_force_password_change()" in app_source


def test_forced_password_change_requires_eight_characters(monkeypatch):
    monkeypatch.setattr(sheets, "update_user_password", lambda *args, **kwargs: True)
    monkeypatch.setattr(application, "log_event", lambda *args, **kwargs: "id")

    with pytest.raises(ValueError, match="至少需要 8"):
        application.change_own_password(
            AuthContext(user_id="student", role="student"), "short"
        )
