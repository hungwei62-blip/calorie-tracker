from __future__ import annotations

import csv
from pathlib import Path

from services import sheets
from services.record_migration import (
    build_legacy_record_audit,
    legacy_record_row_numbers,
)
from tools.remove_legacy_meal_records import run_migration


def _record(meal_type: str, summary: str) -> list[str]:
    return [
        "2026-07-18T12:00:00",
        "student-1",
        meal_type,
        summary,
        "100",
        "10",
        "0",
        "0",
        "0",
        "",
        "1",
    ]


class _Worksheet:
    def __init__(self, values: list[list[str]]):
        self.values = [row[:] for row in values]
        self.deleted = []

    def get_all_values(self):
        return [row[:] for row in self.values]

    def delete_rows(self, start: int, end: int | None = None):
        end = end or start
        self.deleted.append(start if start == end else (start, end))
        del self.values[start - 1:end]


def test_legacy_record_audit_targets_only_meal_period_categories():
    rows = [
        {"meal_type": "早餐"},
        {"meal_type": "食物"},
        {"meal_type": "午餐"},
        {"meal_type": "晚餐"},
        {"meal_type": "宵夜"},
        {"meal_type": "喝水"},
        {"meal_type": "飲水"},
    ]
    assert legacy_record_row_numbers(rows) == [2, 4, 5, 6]
    audit = build_legacy_record_audit(rows)
    assert audit["legacy_records"] == 4
    assert audit["remaining_records"] == 3


def test_preview_creates_backup_without_deleting(tmp_path: Path):
    values = [sheets.RECORDS_HEADERS, _record("早餐", "早餐"), _record("食物", "食物")]
    worksheet = _Worksheet(values)
    output = tmp_path / "preview"

    audit = run_migration(worksheet, output, apply=False)

    assert audit["applied"] is False
    assert worksheet.deleted == []
    assert worksheet.values == values
    assert (output / "Records.csv").exists()
    assert (output / "report.json").exists()


def test_apply_deletes_legacy_rows_in_reverse_and_preserves_others(
    tmp_path: Path, monkeypatch
):
    values = [
        sheets.RECORDS_HEADERS,
        _record("早餐", "delete-1"),
        _record("喝水", "keep-water"),
        _record("宵夜", "delete-2"),
        _record("食物", "keep-food"),
    ]
    worksheet = _Worksheet(values)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    audit = run_migration(worksheet, tmp_path / "apply", apply=True)

    assert worksheet.deleted == [4, 2]
    assert audit["deleted_records"] == 2
    assert [row[3] for row in worksheet.values[1:]] == ["keep-water", "keep-food"]
    with (tmp_path / "apply" / "Records.after.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        assert list(csv.reader(handle)) == worksheet.values
