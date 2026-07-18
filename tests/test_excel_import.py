from __future__ import annotations

import pytest

from services import sheets


class _Worksheet:
    id = 42

    def __init__(self, rows=None):
        self.rows = rows or [sheets.RECORDS_HEADERS]

    def get_all_values(self):
        return self.rows


class _Spreadsheet:
    def __init__(self):
        self.requests = []

    def batch_update(self, body):
        self.requests.append(body)


def _data(token: str, *, existing: bool) -> dict:
    return {
        "records": [
            {
                "date": "2026-07-17",
                "timestamp": "2026-07-17T12:00:00",
                "calories": 500,
                "protein": 30,
                "water": 600,
            }
        ],
        "existing_dates": (
            {"2026-07-17": {"timestamp": "2026-07-17T08:00:00"}}
            if existing
            else {}
        ),
        "user_id": "u1",
        "operation_token": token,
    }


def _install(monkeypatch, rows=None):
    spreadsheet = _Spreadsheet()
    worksheet = _Worksheet(rows)
    monkeypatch.setattr(sheets, "_get_sheet", lambda: spreadsheet)
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: worksheet)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)
    return spreadsheet


def test_excel_precomputed_duplicates_can_be_skipped(monkeypatch):
    spreadsheet = _install(monkeypatch)
    data = _data("skip-token", existing=True)
    result = sheets.import_records_from_excel(
        user_id="u1",
        precomputed_data=data,
        operation_token="skip-token",
        overwrite_duplicates=False,
    )
    assert result["skipped"] == 1
    assert spreadsheet.requests == []


def test_excel_precomputed_new_record_is_batched(monkeypatch):
    spreadsheet = _install(monkeypatch)
    data = _data("append-token", existing=False)
    result = sheets.import_records_from_excel(
        user_id="u1", precomputed_data=data, operation_token="append-token"
    )
    assert result["imported"] == 1
    request = spreadsheet.requests[0]["requests"][0]["appendCells"]
    assert request["sheetId"] == 42


def test_excel_duplicate_is_updated_without_delete(monkeypatch):
    rows = [
        sheets.RECORDS_HEADERS,
        ["2026-07-17T08:00:00", "u1", "食物", "舊資料"],
    ]
    spreadsheet = _install(monkeypatch, rows)
    data = _data("overwrite-token", existing=True)
    result = sheets.import_records_from_excel(
        user_id="u1",
        precomputed_data=data,
        operation_token="overwrite-token",
        overwrite_duplicates=True,
    )
    assert result["overwritten"] == 1
    request = spreadsheet.requests[0]["requests"][0]["updateCells"]
    assert request["range"]["startRowIndex"] == 1


def test_excel_token_cannot_be_replayed_or_change_target(monkeypatch):
    _install(monkeypatch)
    data = _data("single-use-token", existing=False)
    sheets.import_records_from_excel(
        user_id="u1", precomputed_data=data, operation_token="single-use-token"
    )
    replay = sheets.import_records_from_excel(
        user_id="u1", precomputed_data=data, operation_token="single-use-token"
    )
    assert replay["errors"] and "已執行" in replay["errors"][0]

    changed = _data("target-token", existing=False)
    result = sheets.import_records_from_excel(
        user_id="u2", precomputed_data=changed, operation_token="target-token"
    )
    assert result["errors"] and "目標學員不一致" in result["errors"][0]
