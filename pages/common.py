"""AI 健身教練管理系統 Web App

健身教練管理學員的飲食、訓練、體重記錄系統。

使用 Streamlit + Gemini 2.5 Flash + Google Sheets。

"""

from __future__ import annotations

from datetime import date
import streamlit as st
from services import metrics, sheets

# ---------- 常數 ----------

NUTRIENT_KEYS = ("calorie", "protein", "carb", "fat")

CACHE_TTL = 60

DEFAULT_GOALS = {"calorie": 2000.0, "protein": 60.0, "carb": 250.0, "fat": 65.0, "water": 2000.0}

# 訓練項目

TRAINING_TYPES = ["背", "胸", "腿", "核心", "有氧"]

# ---------- Session 初始化 ----------

def init_session() -> None:

    defaults = {

        "user_id": None,

        "username": None,

        "role": None,

        "page": "個人",

        "pending_analysis": None,

        "pending_student_id": None,
        "needs_tdee_setup": False,
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

# =============================================================================

# 教練端頁面

# =============================================================================

def do_logout() -> None:
    """清除 session 並重新整理頁面（用於登出按鈕）"""
    for k in list(st.session_state.keys()):
        if k != "page":
            del st.session_state[k]
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()
