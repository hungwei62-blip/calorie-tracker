"""Authentication context, login throttling, and safe operational logging."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import threading
import time
import uuid
from typing import Callable, MutableMapping

from config.settings import SETTINGS


LOGGER = logging.getLogger("project_prime.security")
VALID_ROLES = frozenset({"student", "coach", "admin"})


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    role: str

    @property
    def is_manager(self) -> bool:
        return self.role in {"coach", "admin"}


class LoginRateLimiter:
    """Small in-process limiter suitable for the current single private deployment."""

    def __init__(
        self,
        max_failures: int = SETTINGS.login_max_failures,
        window_seconds: int = SETTINGS.login_window_seconds,
        lock_seconds: int = SETTINGS.login_lock_seconds,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._locked_until: dict[str, float] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _key(username: str) -> str:
        return str(username or "").strip().casefold()

    def _prune(self, key: str, now: float) -> None:
        attempts = self._failures[key]
        cutoff = now - self.window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()

    def is_blocked(self, username: str) -> bool:
        key = self._key(username)
        now = self._clock()
        with self._lock:
            locked_until = self._locked_until.get(key, 0.0)
            if locked_until > now:
                return True
            self._locked_until.pop(key, None)
            self._prune(key, now)
            return False

    def register_failure(self, username: str) -> bool:
        key = self._key(username)
        now = self._clock()
        with self._lock:
            self._prune(key, now)
            self._failures[key].append(now)
            if len(self._failures[key]) >= self.max_failures:
                self._locked_until[key] = now + self.lock_seconds
                return True
            return False

    def register_success(self, username: str) -> None:
        key = self._key(username)
        with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()
            self._locked_until.clear()


LOGIN_RATE_LIMITER = LoginRateLimiter()


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def log_event(
    action: str,
    *,
    result: str,
    request_id: str | None = None,
    actor_id: str = "",
    actor_role: str = "",
    target_type: str = "",
    target_id: str = "",
    metadata: dict[str, object] | None = None,
    duration_ms: float | None = None,
    exc: BaseException | None = None,
) -> str:
    request_id = request_id or new_request_id()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_id": request_id,
        "action": action,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "target_type": target_type,
        "target_id": target_id,
        "result": result,
        "duration_ms": round(max(duration_ms or 0.0, 0.0), 2),
    }
    if exc is None:
        LOGGER.info("security_event", extra={"event": payload})
    else:
        LOGGER.exception(
            "security_event",
            extra={"event": payload, "error_type": type(exc).__name__},
        )
    try:
        from services import sheets

        sheets.append_audit_log(
            timestamp=payload["timestamp"],
            request_id=request_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            result=result,
            metadata=metadata,
        )
    except Exception as audit_exc:
        LOGGER.warning(
            "audit_log_unavailable request_id=%s exception_type=%s",
            request_id,
            type(audit_exc).__name__,
        )
    return request_id


def safe_failure_message(action: str, exc: BaseException) -> str:
    request_id = log_event(action, result="error", exc=exc)
    return f"作業失敗，請稍後再試（錯誤代碼：{request_id}）"


def resolve_auth_context(user_id: str, rows: list[dict]) -> AuthContext | None:
    target = str(user_id or "").strip()
    if not target:
        return None
    user = next(
        (row for row in rows if str(row.get("user_id") or "").strip() == target),
        None,
    )
    if user is None:
        return None
    role = str(user.get("role") or "student").strip().lower()
    if role not in VALID_ROLES:
        return None
    return AuthContext(user_id=target, role=role)


def clear_auth_session(session_state: MutableMapping[str, object]) -> None:
    for key in list(session_state):
        del session_state[key]
    session_state["user_id"] = None
    session_state["role"] = None
    session_state["page"] = "個人"
    session_state["auth_mode"] = "login"
