from __future__ import annotations

from services import health


def test_health_checks_do_not_expose_secret_values(monkeypatch):
    monkeypatch.setattr(health.sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(health.sheets, "_ensure_worksheet", lambda *_args: object())
    monkeypatch.setattr(health.sheets, "get_primary_coach_id", lambda: "coach-secret-id")
    monkeypatch.setattr(health.gemini, "is_configured", lambda: True)
    monkeypatch.setattr(
        health.sheets,
        "get_audit_logs",
        lambda limit=500: [
            {"action": "backup.complete", "timestamp": "2026-07-19T03:00:00+08:00"}
        ],
    )

    checks = health.run_health_checks()
    rendered = " ".join(check.detail for check in checks)
    assert all(check.status == "ok" for check in checks)
    assert "coach-secret-id" not in rendered
