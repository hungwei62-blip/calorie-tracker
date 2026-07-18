from __future__ import annotations

import json

from services import sheets


class _Worksheet:
    def __init__(self, headers, sheet_id=1):
        self.headers = list(headers)
        self.id = sheet_id
        self.appended = []

    def row_values(self, _row):
        return list(self.headers)

    def append_row(self, row, **_kwargs):
        self.appended.append(list(row))


def test_runtime_schema_check_never_adds_or_extends(monkeypatch):
    class Spreadsheet:
        def __init__(self):
            self.added = []

        def worksheet(self, _title):
            raise sheets.gspread.WorksheetNotFound

        def add_worksheet(self, **kwargs):
            self.added.append(kwargs)

    spreadsheet = Spreadsheet()
    try:
        sheets._ensure_worksheet(spreadsheet, "Users", sheets.USERS_HEADERS)
    except RuntimeError as exc:
        assert "tools/init_sheets.py" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("missing schema must fail closed")
    assert spreadsheet.added == []


def test_audit_log_redacts_sensitive_metadata(monkeypatch):
    worksheet = _Worksheet(sheets.AUDIT_HEADERS)
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: worksheet)

    sheets.append_audit_log(
        timestamp="2026-07-19T12:00:00+00:00",
        request_id="request-1",
        actor_id="coach-1",
        actor_role="coach",
        action="student.goals.update",
        target_type="student",
        target_id="student-1",
        result="success",
        metadata={"fields": ["protein"], "password": "never-store"},
    )

    metadata = json.loads(worksheet.appended[0][-1])
    assert metadata == {"fields": ["protein"]}


def test_backup_script_keeps_twelve_weekly_copies():
    source = open("ops/apps_script/weekly_backup.gs", encoding="utf-8").read()
    assert "RETENTION_WEEKS = 12" in source
    assert "SOURCE_SPREADSHEET_ID" in source
    assert "BACKUP_FOLDER_ID" in source
    assert "installWeeklyTrigger" in source

