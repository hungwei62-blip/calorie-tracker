"""Preview or apply stable record IDs for Records, Weight, and Training."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
import uuid
from typing import Any

import gspread


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import sheets  # noqa: E402
from services.record_id_migration import audit_record_ids  # noqa: E402


MIGRATION_SCHEMAS = {
    "Records": (sheets.LEGACY_RECORDS_HEADERS, sheets.RECORDS_HEADERS, "rec"),
    "Weight": (sheets.LEGACY_WEIGHT_HEADERS, sheets.WEIGHT_HEADERS, "wgt"),
    "Training": (sheets.LEGACY_TRAINING_HEADERS, sheets.TRAINING_HEADERS, "trn"),
}


def _write_csv(path: Path, values: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows(values)


def run_migration(
    worksheets: dict[str, Any], output_dir: Path, *, apply: bool
) -> dict[str, Any]:
    snapshots = {name: worksheet.get_all_values() for name, worksheet in worksheets.items()}
    report: dict[str, Any] = {"applied": apply, "worksheets": {}}

    for name, (legacy, target, _prefix) in MIGRATION_SCHEMAS.items():
        audit = audit_record_ids(
            snapshots[name], legacy_headers=legacy, target_headers=target
        )
        if apply and audit["duplicate_ids"]:
            raise ValueError(f"{name} 含有重複 record_id，已停止遷移")
        report["worksheets"][name] = audit

    if not apply:
        return report

    output_dir.mkdir(parents=True, exist_ok=False)
    for name, values in snapshots.items():
        _write_csv(output_dir / f"{name}.before.csv", values)

    for name, (legacy, target, prefix) in MIGRATION_SCHEMAS.items():
        worksheet = worksheets[name]
        values = snapshots[name]
        if values[0] == legacy:
            if worksheet.col_count < len(target):
                worksheet.add_cols(len(target) - worksheet.col_count)
            worksheet.update_cell(1, len(target), "record_id")

        id_col = target.index("record_id") + 1
        cells = []
        for row_index, row in enumerate(values[1:], start=2):
            existing = str(row[id_col - 1]).strip() if len(row) >= id_col else ""
            if not existing:
                cells.append(gspread.Cell(row_index, id_col, f"{prefix}_{uuid.uuid4().hex}"))
        if cells:
            worksheet.update_cells(cells, value_input_option="RAW")

    sheets._VERIFIED_WORKSHEET_SCHEMAS.clear()
    report["backup_dir"] = str(output_dir)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="檢查三張紀錄表的 record_id；只有 --apply 才會備份並套用"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "backups")
    args = parser.parse_args()

    spreadsheet = sheets._get_sheet()
    worksheets = {
        name: spreadsheet.worksheet(name) for name in MIGRATION_SCHEMAS
    }
    stamp = datetime.now().strftime("record_ids_%Y%m%d_%H%M%S")
    destination = args.output_dir / stamp
    report = run_migration(worksheets, destination, apply=args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any(
        item["duplicate_ids"] for item in report["worksheets"].values()
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
