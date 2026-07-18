"""Back up Training and optionally replace its legacy schema and rows."""

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


LEGACY_TRAINING_HEADERS = [
    "timestamp",
    "user_id",
    "training_back",
    "training_chest",
    "training_legs",
    "training_core",
    "training_cardio",
]


def _write_csv(path: Path, values: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows(values)


def run_migration(worksheet: Any, output_dir: Path, *, apply: bool) -> dict[str, Any]:
    """Back up and audit Training; clear legacy rows only when apply is true."""
    output_dir.mkdir(parents=True, exist_ok=False)
    before = worksheet.get_all_values()
    headers = before[0] if before else []
    if headers not in (LEGACY_TRAINING_HEADERS, sheets.TRAINING_HEADERS):
        raise RuntimeError("Training 欄位不符合舊版或新版定義，已停止且未修改資料")

    _write_csv(output_dir / "Training.csv", before)
    already_migrated = headers == sheets.TRAINING_HEADERS
    audit: dict[str, Any] = {
        "sheet": "Training",
        "current_headers": headers,
        "target_headers": sheets.TRAINING_HEADERS,
        "records_before": max(len(before) - 1, 0),
        "already_migrated": already_migrated,
        "applied": False,
    }
    report_path = output_dir / "report.json"
    report_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not apply or already_migrated:
        return audit

    worksheet.clear()
    worksheet.update([sheets.TRAINING_HEADERS], range_name="A1", raw=True)
    after = worksheet.get_all_values()
    expected = [sheets.TRAINING_HEADERS]
    if after != expected:
        raise RuntimeError("Training 遷移後比對失敗，請使用 Training.csv 備份復原")

    _write_csv(output_dir / "Training.after.csv", after)
    sheets.clear_read_caches()
    audit.update({
        "applied": True,
        "deleted_records": max(len(before) - 1, 0),
        "records_after": 0,
        "headers_verified": True,
    })
    report_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description="備份並重設 Training 工作表結構")
    parser.add_argument("--apply", action="store_true", help="套用清除與改版；預設只預覽")
    parser.add_argument(
        "--output-dir", type=Path, default=PROJECT_ROOT / "backups"
    )
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = args.output_dir / f"migrate_training_{stamp}"
    worksheet = sheets._get_sheet().worksheet("Training")
    audit = run_migration(worksheet, destination, apply=args.apply)
    action = "已套用" if audit["applied"] else "僅預覽"
    if audit["already_migrated"]:
        action = "已是新版結構"
    print(f"{action}：{destination / 'report.json'}")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
