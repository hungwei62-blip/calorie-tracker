from __future__ import annotations

import json

import pytest

from services import sheets
from tools.migrate_training_schema import LEGACY_TRAINING_HEADERS, run_migration


class TrainingWorksheet:
    def __init__(self, values):
        self.values = [list(row) for row in values]
        self.clear_calls = 0
        self.update_calls = []

    def get_all_values(self):
        return [list(row) for row in self.values]

    def clear(self):
        self.clear_calls += 1
        self.values = []

    def update(self, values, **kwargs):
        self.update_calls.append((values, kwargs))
        self.values = [list(row) for row in values]


def _legacy_values():
    return [
        LEGACY_TRAINING_HEADERS,
        ["2026-07-17", "student-1", "0", "1", "0", "0", "0"],
        ["2026-07-18", "student-2", "0", "0", "1", "1", "0"],
    ]


def test_training_migration_preview_only_backs_up(tmp_path):
    worksheet = TrainingWorksheet(_legacy_values())
    output = tmp_path / "preview"

    audit = run_migration(worksheet, output, apply=False)

    assert audit["records_before"] == 2
    assert audit["applied"] is False
    assert worksheet.clear_calls == 0
    assert worksheet.update_calls == []
    assert (output / "Training.csv").exists()
    assert json.loads((output / "report.json").read_text(encoding="utf-8"))["applied"] is False


def test_training_migration_apply_clears_rows_and_sets_new_header(monkeypatch, tmp_path):
    worksheet = TrainingWorksheet(_legacy_values())
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)
    output = tmp_path / "apply"

    audit = run_migration(worksheet, output, apply=True)

    assert audit["applied"] is True
    assert audit["deleted_records"] == 2
    assert audit["records_after"] == 0
    assert worksheet.get_all_values() == [sheets.TRAINING_HEADERS]
    assert worksheet.clear_calls == 1
    assert worksheet.update_calls == [
        ([sheets.TRAINING_HEADERS], {"range_name": "A1", "raw": True})
    ]
    assert (output / "Training.after.csv").exists()


def test_training_migration_rejects_unknown_schema_without_writes(tmp_path):
    worksheet = TrainingWorksheet([["timestamp", "unexpected"], ["x", "y"]])

    with pytest.raises(RuntimeError, match="欄位不符合"):
        run_migration(worksheet, tmp_path / "invalid", apply=True)

    assert worksheet.clear_calls == 0
    assert worksheet.update_calls == []
