"""Central, non-secret application settings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    cache_ttl_seconds: int = 60
    primary_coach_id: str = "u_20260629165506_4b525f9c"
    login_max_failures: int = 5
    login_window_seconds: int = 15 * 60
    login_lock_seconds: int = 15 * 60
    max_upload_mb: int = 10


SETTINGS = AppSettings()

