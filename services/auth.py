"""\u5e33\u5bc6\u8a8d\u8b49\u670d\u52d9\uff1a\u4f7f\u7528 bcrypt \u96dc\u6e96\uff0c\u8a8d\u8b49\u4ee5 Sheets Users \u8868\u70ba\u4f86\u6e90\u3002"""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any

import bcrypt


def hash_password(plain: str) -> str:
    """\u5c07\u660e\u78bc\u78bc\u6e96\u70ba bcrypt \u5b57\u4e32\u3002"""
    if not plain:
        raise ValueError("\u5bc6\u78bc\u4e0d\u53ef\u4ee5\u662f\u7a7a\u5b57\u4e32")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """\u9a57\u8b49\u660e\u78bc\u8207\u5b57\u4e32\u662f\u5426\u4e00\u81f4\u3002\u8b8a\u6578\u7121\u6548 (\u4f8b\u5982\u820a\u8cc7\u6599\u9055\u5f02) \u4e3b\u52d5\u8fd4\u56de False\u3002"""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def make_user_id() -> str:
    """\u7522\u751f\u552f\u4e00 user_id (\u4ee5\u6642\u9593\u6233 + 8 \u4f4d\u96a8\u6a5f\u78bc)\u3002"""
    return f"u_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def find_user(rows: list[dict[str, Any]], username: str) -> dict[str, Any] | None:
    """\u5f9e Users \u8868\u7684\u5217\u8868\u4e2d\u5c0b\u627e\u6307\u5b9a username\uff08\u4ecd\u9700\u4e0a\u5c64\u9a57\u8b49\u5bc6\u78bc\uff09\u3002"""
    target = (username or "").strip().lower()
    for row in rows:
        if str(row.get("username", "")).strip().lower() == target:
            return row
    return None
