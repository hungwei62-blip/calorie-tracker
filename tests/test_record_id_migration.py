from __future__ import annotations

from pathlib import Path

import pytest

from services import sheets
from tools.migrate_record_ids import run_migration


class Worksheet:
    def __init__(self, values):
        self.values = [list(row) for row in values]
        self.col_count = len(self.values[0])
        self.writes = 0

    def get_all_values(self):
        return [list(row) for row in self.values]

    def add_cols(self, count):
        self.col_count += count

    def update_cell(self, row, col, value):
        while len(self.values[row - 1]) < col:
            self.values[row - 1].append("")
        self.values[row - 1][col - 1] = value
        self.writes += 1

    def update_cells(self, cells, **_kwargs):
        for cell in cells:
            self.update_cell(cell.row, cell.col, cell.value)


def _worksheets():
    return {
        "Records": Worksheet([
            sheets.LEGACY_RECORDS_HEADERS,
            ["2026-07-20T08:00:00+08:00", "u1", "食物", "早餐", 500, 30, 0, 0, 0, "", 1],
        ]),
        "Weight": Worksheet([
            sheets.LEGACY_WEIGHT_HEADERS,
            ["2026-07-20T08:00:00+08:00", "u1", 66.5],
        ]),
        "Training": Worksheet([
            sheets.LEGACY_TRAINING_HEADERS,
            ["2026-07-20", "u1", "有氧訓練", "", "跑步", ""],
        ]),
    }


def test_record_id_migration_preview_never_writes(tmp_path: Path):
    worksheets = _worksheets()
    report = run_migration(worksheets, tmp_path / "preview", apply=False)

    assert not (tmp_path / "preview").exists()
    assert all(item["missing_ids"] == 1 for item in report["worksheets"].values())
    assert all(worksheet.writes == 0 for worksheet in worksheets.values())


def test_record_id_migration_backs_up_backfills_and_is_idempotent(tmp_path: Path):
    worksheets = _worksheets()
    run_migration(worksheets, tmp_path / "first", apply=True)

    first_ids = {}
    for name, worksheet in worksheets.items():
        assert worksheet.values[0][-1] == "record_id"
        first_ids[name] = worksheet.values[1][-1]
        assert first_ids[name]
        assert (tmp_path / "first" / f"{name}.before.csv").is_file()

    run_migration(worksheets, tmp_path / "second", apply=True)
    assert {name: ws.values[1][-1] for name, ws in worksheets.items()} == first_ids


def test_record_id_migration_rejects_duplicates_before_any_write(tmp_path: Path):
    worksheets = _worksheets()
    worksheets["Records"] = Worksheet([
        sheets.RECORDS_HEADERS,
        ["2026-07-20", "u1", "食物", "a", 1, 1, 0, 0, 0, "", 1, "rec_same"],
        ["2026-07-21", "u1", "食物", "b", 1, 1, 0, 0, 0, "", 1, "rec_same"],
    ])

    with pytest.raises(ValueError, match="重複 record_id"):
        run_migration(worksheets, tmp_path / "blocked", apply=True)

    assert not (tmp_path / "blocked").exists()
    assert all(worksheet.writes == 0 for worksheet in worksheets.values())


def test_record_id_migration_preview_reports_duplicates(tmp_path: Path):
    worksheets = _worksheets()
    worksheets["Records"] = Worksheet([
        sheets.RECORDS_HEADERS,
        ["2026-07-20", "u1", "食物", "a", 1, 1, 0, 0, 0, "", 1, "rec_same"],
        ["2026-07-21", "u1", "食物", "b", 1, 1, 0, 0, 0, "", 1, "rec_same"],
    ])

    report = run_migration(worksheets, tmp_path / "preview", apply=False)

    assert report["worksheets"]["Records"]["duplicate_ids"] == ["rec_same"]
    assert not (tmp_path / "preview").exists()


def test_record_id_migration_rejects_unknown_schema(tmp_path: Path):
    worksheets = _worksheets()
    worksheets["Weight"] = Worksheet([["unexpected"], ["value"]])

    with pytest.raises(ValueError, match="不是可辨識"):
        run_migration(worksheets, tmp_path / "unknown", apply=True)

    assert not (tmp_path / "unknown").exists()
