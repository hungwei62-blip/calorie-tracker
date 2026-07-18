"""Read-only administrator health checks."""

from __future__ import annotations

from dataclasses import dataclass

from services import gemini, sheets


@dataclass(frozen=True)
class HealthCheck:
    name: str
    status: str
    detail: str


def run_health_checks() -> list[HealthCheck]:
    checks: list[HealthCheck] = []
    try:
        spreadsheet = sheets._get_sheet()
        for title, headers in sheets.WORKSHEET_SCHEMAS.items():
            sheets._ensure_worksheet(spreadsheet, title, headers)
        checks.append(HealthCheck("Google Sheets", "ok", "六張工作表 schema 正常"))
    except Exception:
        checks.append(HealthCheck("Google Sheets", "error", "連線或 schema 異常"))

    try:
        sheets.get_primary_coach_id()
        checks.append(HealthCheck("固定主教練", "ok", "帳號存在且角色正確"))
    except Exception:
        checks.append(HealthCheck("固定主教練", "error", "帳號缺失或角色錯誤"))

    gemini_configured = gemini.is_configured()
    checks.append(
        HealthCheck(
            "Gemini",
            "ok" if gemini_configured else "error",
            "API key 已設定" if gemini_configured else "API key 尚未設定",
        )
    )

    try:
        audits = sheets.get_audit_logs(limit=500)
        backups = [row for row in audits if row.get("action") == "backup.complete"]
        detail = (
            f"最近備份：{backups[-1].get('timestamp', '')[:19]}"
            if backups
            else "尚無可驗證的 Drive 備份紀錄"
        )
        checks.append(HealthCheck("資料備份", "ok" if backups else "warning", detail))
    except Exception:
        checks.append(HealthCheck("資料備份", "warning", "AuditLog 尚不可讀取"))
    return checks
