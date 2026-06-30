"""帳密認證服務：使用 bcrypt 雜湊，認證以 Sheets Users 表為來源。"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from typing import Any

import bcrypt

# 台灣時區 (GMT+8)
TAIPEI_TZ = timezone(timedelta(hours=8))


def hash_password(plain: str) -> str:
    """將明碼密碼哈希為 bcrypt 字串。"""
    if not plain:
        raise ValueError("密碼不可以是空字串")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """驗證明碼與字串是否一致。變數無效（例如舊資料錯誤）主動返回 False。"""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def make_user_id() -> str:
    """產生唯一 user_id (以時間戳 + 8位隨機字元)。"""
    return f"u_{datetime.now(TAIPEI_TZ).strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"


def now_iso() -> str:
    """產生台北時區 (GMT+8) 的 ISO 格式時間戳。"""
    return datetime.now(TAIPEI_TZ).isoformat(timespec="seconds")


def find_user(rows: list[dict[str, Any]], username: str) -> dict[str, Any] | None:
    """從 Users 表的列表中尋找指定 username（仍需上層驗證密碼）。"""
    target = (username or "").strip().lower()
    for row in rows:
        if str(row.get("username", "")).strip().lower() == target:
            return row
    return None
