"""AI 健身教練管理系統 Web App

健身教練管理學員的飲食、訓練、體重記錄系統。

使用 Streamlit + Gemini 2.5 Flash + Google Sheets。

"""

from __future__ import annotations

import base64
from datetime import date
from pathlib import Path
import streamlit as st
from services import metrics, sheets
from services.security import AuthContext, clear_auth_session

# ---------- 常數 ----------

NUTRIENT_KEYS = ("calorie", "protein", "carb", "fat")

CACHE_TTL = 60

DEFAULT_GOALS = {"calorie": 2000.0, "protein": 60.0, "carb": 250.0, "fat": 65.0, "water": 2000.0}

DEFAULT_AVATAR_PATH = Path(__file__).resolve().parents[1] / "static" / "avatar.jpg"
DEFAULT_AVATAR_FALLBACK = (
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb"
    "?auto=format&fit=crop&q=80&w=200&h=200"
)

# 訓練項目

TRAINING_TYPES = ("重量訓練", "有氧訓練", "其他")


@st.cache_data(show_spinner=False)
def get_default_avatar_source(avatar_path: str | None = None) -> str:
    """Return the shared student/coach avatar as a JPEG data URI."""
    path = Path(avatar_path) if avatar_path else DEFAULT_AVATAR_PATH
    if not path.is_file():
        return DEFAULT_AVATAR_FALLBACK
    encoded_avatar = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded_avatar}"

# ---------- Session 初始化 ----------

def init_session() -> None:

    defaults = {

        "user_id": None,

        "username": None,

        "name": None,

        "role": None,

        "page": "個人",

        "pending_analysis": None,

        "pending_student_id": None,
        "needs_tdee_setup": False,
        "initial_weight_save_warning": None,
        "auth_mode": "login",

    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value

@st.cache_data(ttl=CACHE_TTL)

def _fetch_records_cached(user_id: str) -> list:

    return sheets.get_records(user_id=user_id)

@st.cache_data(ttl=CACHE_TTL)

def _fetch_goals_cached(user_id: str) -> dict:

    return sheets.get_user_goals(user_id)

def _clear_analysis_cache() -> None:
    # 清掉 app.py 的快取，，避免殘留
    try:
        _fetch_records_cached.clear()
    except Exception:
        pass
    try:
        _fetch_goals_cached.clear()
    except Exception:
        pass
    # 清掉 services/sheets.py 的快取函式，包括所有查詢函式
    for fn_name in ("get_records", "get_weight_records", "get_training_records", "get_notes", "get_latest_weight", "get_users_rows", "get_user_goals"):
        fn = getattr(sheets, fn_name, None)
        if fn is None:
            continue
        try:
            fn.clear()
        except Exception:
            pass


def _today_range() -> tuple:

    today = date.today()

    return today, today

def _week_range() -> tuple:

    today = date.today()

    start = metrics.week_start(today)

    return start, today


def current_auth_context() -> AuthContext:
    """Return the server-validated identity stored by the top-level router."""
    user_id = str(st.session_state.get("user_id") or "").strip()
    role = str(st.session_state.get("role") or "").strip().lower()
    if not user_id or role not in {"student", "coach", "admin"}:
        raise PermissionError("登入狀態無效")
    return AuthContext(user_id=user_id, role=role)

# =============================================================================

# 教練端頁面

# =============================================================================

def do_logout() -> None:
    """清除 session 並重新整理頁面（用於登出按鈕）"""
    clear_auth_session(st.session_state)
    st.rerun()
