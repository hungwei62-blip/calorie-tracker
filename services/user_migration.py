"""Users 工作表稽核與舊版欄位錯位修復的純函式。"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any


TAIPEI_TZ = timezone(timedelta(hours=8))
GOAL_FIELDS = (
    "bmr",
    "daily_calorie_goal",
    "daily_protein_goal",
    "daily_carb_goal",
    "daily_fat_goal",
    "daily_water_goal",
)


def _as_number(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def created_at_from_user_id(user_id: str) -> str:
    """從 u_YYYYMMDDHHMMSS_* 還原台北時區建立時間。"""
    parts = str(user_id).split("_")
    if len(parts) < 3 or parts[0] != "u":
        return ""
    try:
        parsed = datetime.strptime(parts[1], "%Y%m%d%H%M%S").replace(tzinfo=TAIPEI_TZ)
    except ValueError:
        return ""
    return parsed.isoformat(timespec="seconds")


def has_shifted_goals(row: dict[str, Any]) -> bool:
    """舊錯誤會把 BMR（數字）寫入 created_at，可用此訊號安全辨識。"""
    return row.get("role", "").strip().lower() == "student" and _as_number(row.get("created_at")) is not None


def repaired_user(row: dict[str, Any], primary_coach_id: str) -> tuple[dict[str, Any], list[str]]:
    """回傳修復後資料與警告；不修改傳入的 row。"""
    repaired = dict(row)
    warnings: list[str] = []

    if has_shifted_goals(row):
        restored_created_at = created_at_from_user_id(str(row.get("user_id", "")))
        if not restored_created_at:
            warnings.append("created_at 無法從 user_id 還原，已留空")
        repaired.update({
            "created_at": restored_created_at,
            "bmr": row.get("created_at", ""),
            "daily_calorie_goal": row.get("bmr", ""),
        })

    role = str(repaired.get("role", "")).strip().lower()
    if role == "student" and not str(repaired.get("coach_id", "")).strip():
        repaired["coach_id"] = primary_coach_id
    elif role in ("coach", "admin"):
        repaired["coach_id"] = ""

    for field in GOAL_FIELDS:
        number = _as_number(repaired.get(field))
        if number is not None and number < 0:
            warnings.append(f"{field} 是負數，未自動修正")
    return repaired, warnings


def build_audit(rows: list[dict[str, Any]], primary_coach_id: str) -> dict[str, Any]:
    """產生可序列化稽核結果及每列預計變更。"""
    coach_ids = {
        str(row.get("user_id", ""))
        for row in rows
        if str(row.get("role", "")).strip().lower() == "coach"
    }
    if primary_coach_id not in coach_ids:
        raise ValueError("PRIMARY_COACH_ID 必須指向 role=coach 的既有帳號")

    changes = []
    unassigned = []
    for index, row in enumerate(rows, start=2):
        repaired, warnings = repaired_user(row, primary_coach_id)
        changed_fields = {
            key: {"before": row.get(key, ""), "after": repaired.get(key, "")}
            for key in repaired
            if row.get(key, "") != repaired.get(key, "")
        }
        if changed_fields or warnings:
            changes.append({
                "row": index,
                "user_id": row.get("user_id", ""),
                "changes": changed_fields,
                "warnings": warnings,
            })
        if str(repaired.get("role", "")).strip().lower() == "student" and not str(repaired.get("coach_id", "")).strip():
            unassigned.append(repaired.get("user_id", ""))

    return {
        "row_count": len(rows),
        "shifted_goal_rows": sum(1 for row in rows if has_shifted_goals(row)),
        "changed_rows": len(changes),
        "initially_unassigned_students": [
            row.get("user_id", "")
            for row in rows
            if str(row.get("role", "")).strip().lower() == "student"
            and not str(row.get("coach_id", "")).strip()
        ],
        "unassigned_students": unassigned,
        "changes": changes,
    }
