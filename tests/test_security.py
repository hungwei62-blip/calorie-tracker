from __future__ import annotations

from services.security import (
    LoginRateLimiter,
    clear_auth_session,
    resolve_auth_context,
)


def test_login_rate_limiter_blocks_fifth_failure_and_expires():
    now = [100.0]
    limiter = LoginRateLimiter(clock=lambda: now[0])

    for _ in range(4):
        assert limiter.register_failure(" Student ") is False
    assert limiter.register_failure("student") is True
    assert limiter.is_blocked("STUDENT") is True

    now[0] += 901
    assert limiter.is_blocked("student") is False


def test_success_clears_login_failures():
    limiter = LoginRateLimiter()
    limiter.register_failure("student")
    limiter.register_success("student")
    assert limiter.is_blocked("student") is False


def test_auth_context_rejects_missing_and_invalid_roles():
    rows = [
        {"user_id": "student-1", "role": "student"},
        {"user_id": "broken", "role": "owner"},
    ]
    assert resolve_auth_context("student-1", rows).role == "student"
    assert resolve_auth_context("missing", rows) is None
    assert resolve_auth_context("broken", rows) is None


def test_clear_auth_session_removes_sensitive_state():
    session = {"user_id": "u1", "role": "admin", "pending_analysis": {"x": 1}}
    clear_auth_session(session)
    assert session == {
        "user_id": None,
        "role": None,
        "page": "個人",
        "auth_mode": "login",
    }

