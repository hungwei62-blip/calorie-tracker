"""Back up Records and optionally remove breakfast/lunch/dinner/late-night rows."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import sheets  # noqa: E402
from services.record_migration import build_legacy_record_audit  # noqa: E402


def _write_csv(path: Path, values: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows(values)


def _rows_as_dicts(values: list[list[str]]) -> list[dict[str, str]]:
    headers = values[0] if values else []
    return [
        {
            header: row[index] if index < len(row) else ""
            for index, header in enumerate(headers)
        }
        for row in values[1:]
    ]


def _contiguous_ranges(row_numbers: list[int]) -> list[tuple[int, int]]:
    if not row_numbers:
        return []
    ranges: list[tuple[int, int]] = []
    start = previous = row_numbers[0]
    for row_number in row_numbers[1:]:
        if row_number == previous + 1:
            previous = row_number
            continue
        ranges.append((start, previous))
        start = previous = row_number
    ranges.append((start, previous))
    return ranges


def run_migration(worksheet: Any, output_dir: Path, *, apply: bool) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=False)
    before = worksheet.get_all_values()
    if not before or before[0] != sheets.RECORDS_HEADERS:
        raise RuntimeError("Records 欄位順序不符合預期，已停止且未修改資料")

    _write_csv(output_dir / "Records.csv", before)
    audit = build_legacy_record_audit(_rows_as_dicts(before))
    audit["applied"] = False
    report_path = output_dir / "report.json"
    report_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not apply:
        return audit

    targets = audit["worksheet_row_numbers"]
    for start, end in reversed(_contiguous_ranges(targets)):
        worksheet.delete_rows(start, end)

    after = worksheet.get_all_values()
    target_set = set(targets)
    expected = [
        row for index, row in enumerate(before, start=1)
        if index not in target_set
    ]
    if after != expected:
        raise RuntimeError("刪除後資料比對失敗，請使用 Records.csv 備份復原")
    _write_csv(output_dir / "Records.after.csv", after)
    sheets.clear_read_caches()
    audit["applied"] = True
    audit["deleted_records"] = len(targets)
    report_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description="備份並移除舊用餐時段紀錄")
    parser.add_argument("--apply", action="store_true", help="套用刪除；預設只預覽")
    parser.add_argument(
        "--output-dir", type=Path, default=PROJECT_ROOT / "backups"
    )
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = args.output_dir / f"remove_legacy_meals_{stamp}"
    worksheet = sheets._get_sheet().worksheet("Records")
    audit = run_migration(worksheet, destination, apply=args.apply)
    action = "已套用" if args.apply else "僅預覽"
    print(f"{action}：{destination / 'report.json'}")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
