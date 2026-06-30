"""\u5e33\u5bc6\u8a8d\u8b49\u670d\u52d9\uff1a\u4f7f\u7528 bcrypt \u96dc\u6e96\uff0c\u8a8d\u8b49\u4ee5 Sheets Users \u8868\u70ba\u4f86\u6e90\u3002"""

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
    """\u5f9e Users \u8868\u7684\u5217\u8868\u4e2d\u5c0b\u627e\u6307\u5b9a username\uff08\u4ecd\u9700\u4e0a\u5c64\u9a57\u8b49\u5bc6\u78bc\uff09\u3002"""
    target = (username or "").strip().lower()
    for row in rows:
        if str(row.get("username", "")).strip().lower() == target:
            return row
    return None
