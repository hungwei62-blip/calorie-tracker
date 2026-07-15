"""

Google Sheets 存取層。

本模組專為《健身教練管理系統》設計，提供以下工作表的 CRUD：
- Users        ：教練與學員帳號資訊
- Records      ：學員每日飲食記錄
- Weight       ：學員體重記錄
- Training     ：學員訓練記錄（背/胸/腿/核心/有氧）

這些存取全走 .streamlit/secrets.toml 簡寫，沒有其他設定。
學員工作表在本系統中由 sheets._ensure_worksheet 自動建立。

使用範例：
- get_users_rows / append_user / set_user_role
- get_records / append_record
- get_user_goals / update_user_goals
- get_weight_records / append_weight
- get_training_records / append_training
"""

from __future__ import annotations

from datetime import date
from typing import Any

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

CACHE_TTL = 60  # 快取 TTL（秒）

# ---------- Headers ----------

USERS_HEADERS = [
    "user_id",
    "username",
    "name",           # 學員真實姓名
    "password_hash",
    "created_at",
    "bmr",
    "daily_calorie_goal",
    "daily_protein_goal",
    "daily_carb_goal",
    "daily_fat_goal",
    "daily_water_goal",
    "role",
    "weekly_training_goal",
    "record_mode",          # "simple" 或 "full"，學員的飲食記錄模式
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

# 體重記錄工作表
WEIGHT_HEADERS = [
    "timestamp",
    "user_id",
    "weight_kg",
]

# 訓練記錄工作表
TRAINING_HEADERS = [
    "timestamp",
    "user_id",
    "training_back",     # 背：1 或 0
    "training_chest",   # 胸：1 或 0
    "training_legs",    # 腿：1 或 0
    "training_core",    # 核心：1 或 0
    "training_cardio",  # 有氧：1 或 0
]

# 教練備註工作表
NOTES_HEADERS = [
    "timestamp",       # 備註時間
    "user_id",       # 學員 ID
    "coach_id",      # 教練 ID
    "note",          # 備註內容
]


# ---------- 內部工具 ----------

def _get_secrets() -> dict[str, Any]:

    if "gcp" not in st.secrets or "SPREADSHEET_ID" not in st.secrets:
        raise EnvironmentError(
            "請先在 .streamlit/secrets.toml 中設定 [gcp] (含 Service Account JSON) 與 SPREADSHEET_ID"
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
    """確保工作表存在，若不存在則自動建立並寫入 header。"""
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


def _rows_to_dicts(ws: gspread.Worksheet, headers: list[str]) -> list[dict[str, Any]]:
    """將工作表列（第一列為 header）轉為 dict 列表。"""
    values = ws.get_all_values()
    if not values:
        return []
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


def _to_float(val: Any, default: float) -> float:
    """安全轉為 float，失敗時回傳預設值。"""
    try:
        if val in (None, ""):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _to_int(val: Any, default: int) -> int:
    """安全轉為 int，失敗時回傳預設值。"""
    try:
        if val in (None, ""):
            return default
        return int(float(val))
    except (TypeError, ValueError):
        return default


# =============================================================================
# Users
# =============================================================================

@st.cache_data(ttl=CACHE_TTL)
def get_users_rows() -> list[dict[str, Any]]:
    """取得所有使用者列（教練與學員）。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    return _rows_to_dicts(ws, USERS_HEADERS)


def append_user(
    user_id: str,
    username: str,
    name: str,
    password_hash: str,
    created_at: str,
    goals: dict[str, float],
    record_mode: str = "simple",
    weekly_training: int = 4,
) -> None:
    """新增學員到 Users 工作表。

    Args:
        user_id: 學員唯一 ID
        username: 帳號名稱
        password_hash: bcrypt 密碼雜湊
        created_at: 創建時間（ISO 字串）
        goals: 營養目標字典，含 calorie/protein/carb/fat/water
        record_mode: "simple" 或 "full"，飲食記錄模式
        weekly_training: 每週訓練目標次數，預設 4
    """
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    row = [
        user_id,
        username,
        name,
        password_hash,
        created_at,
        "",  # BMR 留空，後續由 update_user_bmr 更新
        goals.get("calorie", 0),
        goals.get("protein", 0),
        goals.get("carb", 0),
        goals.get("fat", 0),
        goals.get("water", 0),
        "student",
        weekly_training,
        record_mode,
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


def get_user_role(user_id: str) -> str:
    """查詢使用者的 role，回傳 "coach" 或 "student"（預設）。"""
    for row in get_users_rows():
        if row.get("user_id") == user_id:
            val = str(row.get("role", "student") or "student")
            return val.strip().lower()
    return "student"


def set_user_role(user_id: str, role: str) -> None:
    """將指定 user_id 的 role 設為 "coach" 或 "student"。"""
    role = (role or "student").strip().lower()
    if role not in ("student", "coach"):
        raise ValueError("role 只能是 student 或 coach")
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    cell = ws.find(user_id)
    if cell is None:
        raise LookupError("找不到此 user_id")
    role_col = USERS_HEADERS.index("role") + 1
    ws.update_cell(cell.row, role_col, role)


def get_user_record_mode(user_id: str) -> str:
    """取得使用者的飲食記錄模式，回傳 "simple" 或 "full"。"""
    for row in get_users_rows():
        if row.get("user_id") == user_id:
            mode = str(row.get("record_mode", "simple") or "simple")
            return mode.strip().lower()
    return "simple"


def set_user_record_mode(user_id: str, mode: str) -> None:
    """設定使用者的飲食記錄模式。mode 只能是 "simple" 或 "full"。"""
    mode = (mode or "simple").strip().lower()
    if mode not in ("simple", "full"):
        raise ValueError("record_mode 只能是 simple 或 full")
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    cell = ws.find(user_id)
    if cell is None:
        raise LookupError("找不到此 user_id")
    col = USERS_HEADERS.index("record_mode") + 1
    ws.update_cell(cell.row, col, mode)


def get_user_goals(user_id: str) -> dict[str, float]:
    """取得使用者的每日營養目標。"""
    for row in get_users_rows():
        if row.get("user_id") == user_id:
            return {
                "bmr": _to_float(row.get("bmr"), 0.0),
                "calorie": _to_float(row.get("daily_calorie_goal"), 2000.0),
                "protein": _to_float(row.get("daily_protein_goal"), 60.0),
                "carb": _to_float(row.get("daily_carb_goal"), 250.0),
                "fat": _to_float(row.get("daily_fat_goal"), 65.0),
                "water": _to_float(row.get("daily_water_goal"), 2000.0),
                "weekly_training": float(row.get("weekly_training_goal", 4)),
            }
    return {"bmr": 0.0, "calorie": 2000.0, "protein": 60.0, "carb": 250.0, "fat": 65.0, "water": 2000.0, "weekly_training": 4.0}


def update_user_bmr(user_id: str, bmr: float) -> bool:
    """更新使用者的 BMR 值。成功回傳 True。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    rows = get_users_rows()
    for idx, row in enumerate(rows, start=2):
        if row.get("user_id") == user_id:
            ws.update_cell(idx, 5, round(bmr, 2))  # BMR 在第 5 欄
            return True
    return False


def update_user_goals(user_id: str, goals: dict[str, float]) -> bool:
    """更新使用者的營養目標（不含 BMR）。成功回傳 True。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Users", USERS_HEADERS)
    rows = get_users_rows()

    # 欄位對應 (1-based)：calorie=6, protein=7, carb=8, fat=9, water=10
    field_map = {
        "calorie": 6,
        "protein": 7,
        "carb": 8,
        "fat": 9,
        "water": 10,
    }

    found = False
    for idx, row in enumerate(rows, start=2):
        if row.get("user_id") == user_id:
            found = True
            for key, col in field_map.items():
                if key in goals:
                    val = goals[key]
                    if isinstance(val, float):
                        val = round(val, 2)
                    ws.update_cell(idx, col, val)
            break

    return found


def get_all_students() -> list[dict[str, Any]]:
    """取得所有學員（role=student）的資料。"""
    return [row for row in get_users_rows() if row.get("role", "").strip().lower() == "student"]


def get_student_by_id(user_id: str) -> dict[str, Any] | None:
    """依 user_id 取得學員資料，找不到回傳 None。"""
    for row in get_users_rows():
        if row.get("user_id") == user_id:
            return row
    return None


# =============================================================================
# Records（飲食記錄）
# =============================================================================

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
    """新增一筆飲食記錄到 Records 工作表。"""
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


@st.cache_data(ttl=CACHE_TTL)
def get_records(user_id: str | None = None) -> list[dict[str, Any]]:
    """取得飲食記錄，可依 user_id 篩選。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Records", RECORDS_HEADERS)
    raw = _rows_to_dicts(ws, RECORDS_HEADERS)
    out: list[dict[str, Any]] = []
    for r in raw:
        if user_id is not None and r.get("user_id") != user_id:
            continue
        r["calories"] = _to_float(r.get("calories"), 0.0)
        r["protein"] = _to_float(r.get("protein"), 0.0)
        r["carb"] = _to_float(r.get("carb"), 0.0)
        r["fat"] = _to_float(r.get("fat"), 0.0)
        r["water_ml"] = _to_float(r.get("water_ml"), 0.0)
        r["portion"] = _to_float(r.get("portion"), 1.0)
        out.append(r)
    return out


def get_records_by_date(user_id: str, target_date: date) -> list[dict[str, Any]]:
    """取得指定日期的飲食記錄。target_date 會比對 timestamp 的日期部分（前 10 字）。"""
    date_str = target_date.isoformat()[:10]
    all_records = get_records(user_id)
    return [r for r in all_records if r.get("timestamp", "")[:10] == date_str]


def update_record(record_timestamp: str, user_id: str, updates: dict[str, Any]) -> bool:
    """更新指定飲食記錄的欄位。成功回傳 True。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Records", RECORDS_HEADERS)
    raw_records = ws.get_all_values()

    field_map = {
        "food_summary": 4,
        "calories": 5,
        "protein": 6,
        "carb": 7,
        "fat": 8,
        "water_ml": 9,
        "portion": 11,
    }

    for row_idx, raw_row in enumerate(raw_records[1:], start=2):
        if raw_row and raw_row[0] == record_timestamp and raw_row[1] == user_id:
            for key, col in field_map.items():
                if key in updates:
                    val = updates[key]
                    if isinstance(val, float):
                        val = round(val, 2)
                    ws.update_cell(row_idx, col, val)
            return True
    return False


def delete_record(record_timestamp: str, user_id: str) -> bool:
    """刪除指定飲食記錄。成功回傳 True。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Records", RECORDS_HEADERS)
    raw_records = ws.get_all_values()

    for row_idx, raw_row in enumerate(raw_records[1:], start=2):
        if raw_row and raw_row[0] == record_timestamp and raw_row[1] == user_id:
            ws.delete_rows(row_idx)
            return True
    return False


# =============================================================================
# Weight（體重記錄）
# =============================================================================

def append_weight(timestamp: str, user_id: str, weight_kg: float) -> None:
    """新增一筆體重記錄到 Weight 工作表。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Weight", WEIGHT_HEADERS)
    row = [
        timestamp,
        user_id,
        round(weight_kg, 1),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


@st.cache_data(ttl=CACHE_TTL)
def get_weight_records(user_id: str | None = None) -> list[dict[str, Any]]:
    """取得體重記錄，可依 user_id 篩選。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Weight", WEIGHT_HEADERS)
    raw = _rows_to_dicts(ws, WEIGHT_HEADERS)
    out: list[dict[str, Any]] = []
    for r in raw:
        if user_id is not None and r.get("user_id") != user_id:
            continue
        r["weight_kg"] = _to_float(r.get("weight_kg"), 0.0)
        out.append(r)
    return out


@st.cache_data(ttl=CACHE_TTL)
def get_latest_weight(user_id: str) -> float | None:
    """取得學員最新一筆體重記錄，回傳 kg 值，無記錄時回傳 None。"""
    records = get_weight_records(user_id)
    if not records:
        return None
    return records[-1].get("weight_kg")


def get_weight_by_date(user_id: str, target_date: date) -> float | None:
    """取得指定日期的體重記錄，無記錄時回傳 None。"""
    date_str = target_date.isoformat()[:10]
    for r in get_weight_records(user_id):
        if r.get("timestamp", "")[:10] == date_str:
            return r.get("weight_kg")
    return None


# =============================================================================
# Training（訓練記錄）
# =============================================================================

def append_training(
    timestamp: str,
    user_id: str,
    training_back: int = 0,
    training_chest: int = 0,
    training_legs: int = 0,
    training_core: int = 0,
    training_cardio: int = 0,
) -> None:
    """新增一筆訓練記錄到 Training 工作表。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Training", TRAINING_HEADERS)
    row = [
        timestamp,
        user_id,
        training_back,
        training_chest,
        training_legs,
        training_core,
        training_cardio,
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


@st.cache_data(ttl=CACHE_TTL)
def get_training_records(user_id: str | None = None) -> list[dict[str, Any]]:
    """取得訓練記錄，可依 user_id 篩選。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Training", TRAINING_HEADERS)
    raw = _rows_to_dicts(ws, TRAINING_HEADERS)
    out: list[dict[str, Any]] = []
    for r in raw:
        if user_id is not None and r.get("user_id") != user_id:
            continue
        r["training_back"] = _to_int(r.get("training_back"), 0)
        r["training_chest"] = _to_int(r.get("training_chest"), 0)
        r["training_legs"] = _to_int(r.get("training_legs"), 0)
        r["training_core"] = _to_int(r.get("training_core"), 0)
        r["training_cardio"] = _to_int(r.get("training_cardio"), 0)
        out.append(r)
    return out


def get_training_by_date(user_id: str, target_date: date) -> dict[str, int] | None:
    """取得指定日期的訓練記錄，回傳 dict（無記錄回傳 None）。"""
    date_str = target_date.isoformat()[:10]
    for r in get_training_records(user_id):
        if r.get("timestamp", "")[:10] == date_str:
            return {
                "back": r.get("training_back", 0),
                "chest": r.get("training_chest", 0),
                "legs": r.get("training_legs", 0),
                "core": r.get("training_core", 0),
                "cardio": r.get("training_cardio", 0),
            }
    return None


def has_training_today(user_id: str, target_date: date) -> bool:
    """檢查指定日期是否有任何訓練記錄。"""
    record = get_training_by_date(user_id, target_date)
    if record is None:
        return False
    return any(v == 1 for v in record.values())


def update_training(
    timestamp: str,
    user_id: str,
    training_back: int = 0,
    training_chest: int = 0,
    training_legs: int = 0,
    training_core: int = 0,
    training_cardio: int = 0,
) -> bool:
    """更新指定日期的訓練記錄，若該日記錄不存在則新增。成功回傳 True。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Training", TRAINING_HEADERS)
    raw_records = ws.get_all_values()

    # 先找看看有沒有該日期的記錄
    for row_idx, raw_row in enumerate(raw_records[1:], start=2):
        if raw_row and raw_row[0] == timestamp and raw_row[1] == user_id:
            # 更新現有列
            for col, val in enumerate([training_back, training_chest, training_legs, training_core, training_cardio], start=3):
                ws.update_cell(row_idx, col, val)
            return True

    # 沒找到就新增
    append_training(timestamp, user_id, training_back, training_chest, training_legs, training_core, training_cardio)
    return True


# =============================================================================
# Notes（教練備註）
# =============================================================================

def append_note(timestamp: str, user_id: str, coach_id: str, note: str) -> None:
    """新增一筆教練備註到 Notes 工作表。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Notes", NOTES_HEADERS)
    row = [
        timestamp,
        user_id,
        coach_id,
        note,
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


@st.cache_data(ttl=CACHE_TTL)
def get_notes(user_id: str | None = None) -> list[dict[str, Any]]:
    """取得教練備註，可依 user_id 篩選。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Notes", NOTES_HEADERS)
    raw = _rows_to_dicts(ws, NOTES_HEADERS)
    out: list[dict[str, Any]] = []
    for r in raw:
        if user_id is not None and r.get("user_id") != user_id:
            continue
        out.append(r)
    return out


def get_latest_note(user_id: str) -> dict[str, Any] | None:
    """取得指定學員的最新一筆備註。"""
    notes = get_notes(user_id)
    if not notes:
        return None
    return notes[-1]  # 因為是時間排序，最後一筆是最新的
def update_note(timestamp: str, user_id: str, coach_id: str, new_note: str) -> bool:
    """更新指定教練備註的內容。成功回傳 True。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Notes", NOTES_HEADERS)
    raw_records = ws.get_all_values()
    for row_idx, raw_row in enumerate(raw_records[1:], start=2):
        if raw_row and raw_row[0] == timestamp and raw_row[1] == user_id and raw_row[2] == coach_id:
            ws.update_cell(row_idx, 4, new_note)  # note 在第 4 欄
            return True
    return False


def delete_note(timestamp: str, user_id: str, coach_id: str) -> bool:
    """刪除指定教練備註。成功回傳 True。"""
    sh = _get_sheet()
    ws = _ensure_worksheet(sh, "Notes", NOTES_HEADERS)
    raw_records = ws.get_all_values()
    for row_idx, raw_row in enumerate(raw_records[1:], start=2):
        if raw_row and raw_row[0] == timestamp and raw_row[1] == user_id and raw_row[2] == coach_id:
            ws.delete_rows(row_idx)
            return True
    return False


def import_records_from_excel(excel_file_bytes: bytes, user_id: str, overwrite_duplicates: bool = False) -> dict[str, Any]:
    """從 Excel 檔案匯入飲食記錄。
    
    自動識別欄位：日期、蛋白質(g)、總熱量(kcal)、喝水(ml)
    
    參數：
    - excel_file_bytes: Excel 檔案位元組
    - user_id: 學員 ID
    - overwrite_duplicates: 是否覆寫已存在的日期記錄（預設 False，表示跳過）
    
    回傳：{
        "imported": 新增數量, 
        "overwritten": 覆寫數量, 
        "skipped": 跳過數量,
        "duplicates": [{"date": 日期, "existing": 現有資料}]（僅當 overwrite_duplicates=False 時）,
        "errors": [錯誤訊息]
    }
    """
    import openpyxl
    from io import BytesIO
    from datetime import datetime
    
    result = {
        "imported": 0,
        "overwritten": 0,
        "skipped": 0,
        "duplicates": [],
        "errors": []
    }
    
    try:
        wb = openpyxl.load_workbook(BytesIO(excel_file_bytes))
        
        existing_records = get_records(user_id)
        existing_dates = {}
        for r in existing_records:
            ts = r.get("timestamp", "")
            if ts:
                existing_dates[ts[:10]] = r
        
        column_keywords = {
            "date": ["日期", "date", "日期欄"],
            "protein": ["蛋白質", "蛋白質(g)", "蛋白", "protein", "蛋白 (g)", "蛋白(g)"],
            "calories": ["熱量", "總熱量", "總熱量(kcal)", "calories", "calorie", "kcal", "能量", "總熱量(kcal)"],
            "water": ["喝水", "喝水(ml)", "飲水量", "水量", "water", "ml", "水"],
        }
        
        def find_column(headers, target_key):
            for col_idx, header in enumerate(headers):
                header_str = str(header).strip().lower() if header else ""
                keywords = column_keywords.get(target_key, [])
                for keyword in keywords:
                    if keyword.lower() in header_str or header_str in keyword.lower():
                        return col_idx
            return -1
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            # 掃描前 10 列找出包含關鍵字的標題列
            headers = None
            header_row = 1
            for row_idx in range(1, min(11, ws.max_row + 1)):
                row_values = [cell.value for cell in ws[row_idx]]
                row_str = " ".join([str(v).lower() if v else "" for v in row_values])
                # 檢查這列是否包含必要的關鍵字
                has_date = any(kw in row_str for kw in ["日期", "date"])
                has_nutrient = any(kw in row_str for kw in ["熱量", "蛋白質", "calorie", "protein", "kcal", "能量"])
                if has_date and has_nutrient:
                    headers = row_values
                    header_row = row_idx
                    break
            
            if headers is None:
                result["errors"].append(f"工作表「{sheet_name}」找不到包含日期和營養素的標題列，跳過")
                continue
            
            date_col = find_column(headers, "date")
            protein_col = find_column(headers, "protein")
            calories_col = find_column(headers, "calories")
            water_col = find_column(headers, "water")
            
            if date_col == -1 or (calories_col == -1 and protein_col == -1):
                result["errors"].append(f"工作表「{sheet_name}」找不到必要欄位，跳過（headers={headers}）")
                continue
            
            for row_idx, row in enumerate(ws.iter_rows(min_row=header_row + 1, values_only=True), start=header_row + 1):
                try:
                    date_val = row[date_col] if date_col < len(row) else None
                    if date_val is None:
                        continue
                    
                    if isinstance(date_val, datetime):
                        date_str = date_val.strftime("%Y-%m-%d")
                    elif isinstance(date_val, str):
                        for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                date_str = datetime.strptime(date_val, fmt).strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                        else:
                            result["errors"].append(f"工作表「{sheet_name}」第{row_idx}列：日期格式無法解析")
                            continue
                    else:
                        continue
                    
                    protein = 0.0
                    calories = 0.0
                    water = 0.0
                    
                    if protein_col != -1 and protein_col < len(row):
                        val = row[protein_col]
                        if val is not None:
                            try:
                                protein = float(val)
                            except (ValueError, TypeError):
                                pass
                    
                    if calories_col != -1 and calories_col < len(row):
                        val = row[calories_col]
                        if val is not None:
                            try:
                                calories = float(val)
                            except (ValueError, TypeError):
                                pass
                    
                    if water_col != -1 and water_col < len(row):
                        val = row[water_col]
                        if val is not None:
                            try:
                                water = float(val)
                            except (ValueError, TypeError):
                                pass
                    
                    timestamp = f"{date_str}T12:00:00"
                    
                    if date_str in existing_dates:
                        if overwrite_duplicates:
                            delete_record(timestamp, user_id)
                            append_record(
                                timestamp=timestamp,
                                user_id=user_id,
                                meal_type="午餐",
                                food_summary="從 Excel 匯入（覆寫）",
                                calories=calories,
                                protein=protein,
                                carb=0,
                                fat=0,
                                water_ml=water,
                                image_url="",
                                portion=1.0,
                            )
                            result["overwritten"] += 1
                        else:
                            result["duplicates"].append({
                                "date": date_str,
                                "existing": existing_dates[date_str]
                            })
                            result["skipped"] += 1
                    else:
                        append_record(
                            timestamp=timestamp,
                            user_id=user_id,
                            meal_type="午餐",
                            food_summary="從 Excel 匯入",
                            calories=calories,
                            protein=protein,
                            carb=0,
                            fat=0,
                            water_ml=water,
                            image_url="",
                            portion=1.0,
                        )
                        existing_dates[date_str] = True
                        result["imported"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"工作表「{sheet_name}」第{row_idx}列：{str(e)}")
        
    except Exception as e:
        result["errors"].append(f"開啟 Excel 檔案失敗：{str(e)}")
    
    return result


def overwrite_record_by_date(user_id: str, date_str: str, calories: float, protein: float, water: float) -> bool:
    """根據日期覆寫飲食記錄（用於匯入時覆蓋）。"""
    timestamp = f"{date_str}T12:00:00"
    # 先刪除現有記錄
    delete_record(timestamp, user_id)
    # 重新寫入
    append_record(
        timestamp=timestamp,
        user_id=user_id,
        meal_type="午餐",
        food_summary="從 Excel 匯入（覆寫）",
        calories=calories,
        protein=protein,
        carb=0,
        fat=0,
        water_ml=water,
        image_url="",
        portion=1.0,
    )
    return True
