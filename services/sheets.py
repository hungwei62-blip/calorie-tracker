"""Google Sheets \u8b80\u5beb\u670d\u52d9\u3002\n\n\u4f9d\u8cf4\u300a\u4eba\u5de5\u667a\u80fd\u4eba\u54e1\u591a\u4eba\u71b1\u91cf\u8a18\u9304 Web App \u4ee5\u53ca\u8b8a\u66f4\u4e2d\u7684 Google Sheets \u4f5c\u70ba\u500b\u4eba\u4ee5\u53ca\u8a18\u9304\u4e2d\u5fc3\u3002\n\u9019\u4e9b\u5b58\u5132\u5728\u4e0a\u5c64\u4ee5 .streamlit/secrets.toml \u4f86\u8b80\u53d6\uff0c\u6c92\u6709\u8a72\u4ed6\u9ed8\u8a8d\u503c\u3002\n\u8a18\u9304\u8868\u5169\u500b\u3002\n\n\u4f7f\u7528\u8aaa\u660e\uff1a\n- get_users_rows / append_user\n- get_records / append_record\n- get_user_goals\n- update_user_goals (admin \u4ee5\u53ca\u4e2d\u5167\u7de8\u8f2f\u4f7f\u7528)\n"""

from __future__ import annotations

import json
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

USERS_HEADERS = [
    "user_id",
    "username",
    "password_hash",
    "created_at",
    "daily_calorie_goal",
    "daily_protein_goal",
    "daily_carb_goal",
    "daily_fat_goal",
    "daily_water_goal",
]

RECORDS_HEADERS = [
    "timestamp",
    "user_id",
    "meal_type",
    "food_summary",
    "calories",
    "protein",
    "carb",
    "fat",
    "water_ml",
    "image_url",
    "portion",
]


def _get_secrets() -> dict[str, Any]:
    import streamlit as st

    if "gcp" not in st.secrets or "SPREADSHEET_ID" not in st.secrets:
        raise EnvironmentError(
            "\u8acb\u5728 .streamlit/secrets.toml \u4e2d\u8a2d\u5b9a [gcp] (\u542b Service Account JSON) \u53ca SPREADSHEET_ID"
        )
    gcp = dict(st.secrets["gcp"])
    gcp["SPREADSHEET_ID"] = st.secrets["SPREADSHEET_ID"]
    return gcp


def _get_client() -> gspread.Client:
    sec = _get_secrets()
    sa_info = {k: v for k, v in sec.items() if k != "SPREADSHEET_ID"}
    creds = Credentials.from_service_account_info(
        sa_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds)


def _get_sheet() -> gspread.Spreadsheet:
    sec = _get_secrets()
    return _get_client().open_by_key(sec["SPREADSHEET_ID"])


def _ensure_worksheet(sh: gspread.Spreadsheet, title: str, headers: list[str]) -> gspread.Worksheet:
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


def _rows_to_dicts(ws: gspread.Worksheet, headers: list[str]) -> list[dict[str, Any]]:
    values = ws.get_all_values()
    if not values:
        return []
    head = values[0]
    out: list[dict[str, Any]] = []
    for row in values[1:]:
        record = {}
        for i, key in enumerate(headers):
            if i < len(row):
                record[key] = row[i]
            else:
                record[key] = ""
        out.append(record)
    return out


# ---------- Users ----------

def get_users_rows() -> list[dict[str, Any]]:
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    return _rows_to_dicts(ws, USERS_HEADERS)


def append_user(
    user_id: str,
    username: str,
    password_hash: str,
    created_at: str,
    goals: dict[str, float],
) -> None:
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    row = [
        user_id,
        username,
        password_hash,
        created_at,
        goals.get("calorie", 0),
        goals.get("protein", 0),
        goals.get("carb", 0),
        goals.get("fat", 0),
        goals.get("water", 0),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


def get_user_goals(user_id: str) -> dict[str, float]:
    """\u8b80\u53d6\u4e00\u540d\u4f7f\u7528\u8005\u7684\u65e5\u76ee\u6a19\uff0c\u4e0a\u5c64\u8a2d\u5b9a\u5f8c\u53ef\u88dc\u5165\u4e0a\u5c64\u53ef\u4ee5\u5169\u500b\u3002"""
    for row in get_users_rows():
        if row.get("user_id") == user_id:
            return {
                "calorie": _to_float(row.get("daily_calorie_goal"), 2000.0),
                "protein": _to_float(row.get("daily_protein_goal"), 60.0),
                "carb": _to_float(row.get("daily_carb_goal"), 250.0),
                "fat": _to_float(row.get("daily_fat_goal"), 65.0),
                "water": _to_float(row.get("daily_water_goal"), 2000.0),
            }
    return {"calorie": 2000.0, "protein": 60.0, "carb": 250.0, "fat": 65.0, "water": 2000.0}


def _to_float(val: Any, default: float) -> float:
    try:
        if val in (None, ""):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


# ---------- Records ----------

def append_record(
    timestamp: str,
    user_id: str,
    meal_type: str,
    food_summary: str,
    calories: float,
    protein: float,
    carb: float,
    fat: float,
    water_ml: float,
    image_url: str,
    portion: float,
) -> None:
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Records", RECORDS_HEADERS)
    row = [
        timestamp,
        user_id,
        meal_type,
        food_summary,
        round(calories, 2),
        round(protein, 2),
        round(carb, 2),
        round(fat, 2),
        round(water_ml, 2),
        image_url or "",
        round(portion, 2),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


def get_records(user_id: str | None = None) -> list[dict[str, Any]]:
    """\u8b80\u53d6\u8a18\u9304\uff0c\u53ef\u9078\u64c7\u4f9d user_id \u7be9\u9078\u3002"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Records", RECORDS_HEADERS)
    raw = _rows_to_dicts(ws, RECORDS_HEADERS)
    out: list[dict[str, Any]] = []
    for r in raw:
        if user_id is not None and r.get("user_id") != user_id:
            continue
        # \u8b6f\u8b80\u6578\u503c
        r["calories"] = _to_float(r.get("calories"), 0.0)
        r["protein"] = _to_float(r.get("protein"), 0.0)
        r["carb"] = _to_float(r.get("carb"), 0.0)
        r["fat"] = _to_float(r.get("fat"), 0.0)
        r["water_ml"] = _to_float(r.get("water_ml"), 0.0)
        r["portion"] = _to_float(r.get("portion"), 1.0)
        out.append(r)
    return out
