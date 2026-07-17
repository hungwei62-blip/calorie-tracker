"""備份、稽核並選擇性修復 Google Sheets。

預設只備份並輸出報告；只有傳入 --apply 才會修改 Users 工作表。
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import sys

import gspread
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import sheets  # noqa: E402
from services.user_migration import build_audit, repaired_user  # noqa: E402


SHEET_NAMES = ("Users", "Records", "Weight", "Training", "Notes")


def _write_csv(path: Path, values: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows(values)


def _rows_as_dicts(values: list[list[str]]) -> tuple[list[str], list[dict[str, str]]]:
    if not values:
        return [], []
    headers = values[0]
    rows = [
        {header: row[index] if index < len(row) else "" for index, header in enumerate(headers)}
        for row in values[1:]
    ]
    return headers, rows


def main() -> int:
    parser = argparse.ArgumentParser(description="備份並稽核 Calorie Tracker 資料")
    parser.add_argument("--apply", action="store_true", help="套用可安全判定的修復與 coach_id 指派")
    parser.add_argument("--primary-coach-id", help="覆蓋 secrets 中的 PRIMARY_COACH_ID")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "backups")
    args = parser.parse_args()

    primary_coach_id = args.primary_coach_id or str(st.secrets.get("PRIMARY_COACH_ID", "")).strip()
    if not primary_coach_id:
        raise EnvironmentError("缺少 PRIMARY_COACH_ID；稽核模式也必須明確指定主教練")
    spreadsheet = sheets._get_sheet()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = args.output_dir / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    snapshots: dict[str, list[list[str]]] = {}
    for name in SHEET_NAMES:
        worksheet = spreadsheet.worksheet(name)
        values = worksheet.get_all_values()
        snapshots[name] = values
        _write_csv(backup_dir / f"{name}.csv", values)

    headers, user_rows = _rows_as_dicts(snapshots["Users"])
    if headers != sheets.USERS_HEADERS[:len(headers)]:
        raise RuntimeError("Users 欄位順序不符合預期，已停止且未修改資料")

    audit = build_audit(user_rows, primary_coach_id)
    audit.update({"applied": False, "primary_coach_id": primary_coach_id})
    report_path = backup_dir / "audit_report.json"
    report_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.apply:
        print(f"稽核完成，未修改資料：{report_path}")
        return 0

    users_ws = spreadsheet.worksheet("Users")
    if len(headers) < len(sheets.USERS_HEADERS):
        if users_ws.col_count < len(sheets.USERS_HEADERS):
            users_ws.add_cols(len(sheets.USERS_HEADERS) - users_ws.col_count)
        for col, header in enumerate(sheets.USERS_HEADERS[len(headers):], start=len(headers) + 1):
            users_ws.update_cell(1, col, header)

    cells: list[gspread.Cell] = []
    for row_index, row in enumerate(user_rows, start=2):
        repaired, _ = repaired_user(row, primary_coach_id)
        for col_index, header in enumerate(sheets.USERS_HEADERS, start=1):
            before = row.get(header, "")
            after = repaired.get(header, "")
            if before != after:
                cells.append(gspread.Cell(row_index, col_index, after))
    if cells:
        users_ws.update_cells(cells, value_input_option="USER_ENTERED")
    sheets.clear_read_caches()

    for name in SHEET_NAMES:
        after_values = spreadsheet.worksheet(name).get_all_values()
        _write_csv(backup_dir / f"{name}.after.csv", after_values)
        if len(after_values) != len(snapshots[name]):
            raise RuntimeError(f"遷移後 {name} 筆數不一致，請使用備份復原")
    if users_ws.row_values(1) != sheets.USERS_HEADERS:
        raise RuntimeError("遷移後 Users 欄位不完整，請使用備份檢查")

    audit["applied"] = True
    audit["updated_cells"] = len(cells)
    report_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"遷移完成：{report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
