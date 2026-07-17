"""AI 健身教練管理系統 Web App

健身教練管理學員的飲食、訓練、體重記錄系統。

使用 Streamlit + Gemini 2.5 Flash + Google Sheets + Firebase Storage。

"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import os
from io import BytesIO
import io as _io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as _plt
import plotly.graph_objects as go
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages as _PdfPages

import time
import streamlit as st

from PIL import Image

from services import auth, firebase, gemini, metrics, sheets

# ---------- 常數 ----------

MEAL_TYPES = ["早餐", "午餐", "晚餐", "宵夜", "喝水"]

MEAL_EMOJI = {"早餐": "🌅", "午餐": "☀️", "晚餐": "🌙", "宵夜": "🌛", "喝水": "💧"}

NUTRIENT_KEYS = ("calorie", "protein", "carb", "fat")

CACHE_TTL = 60

DEFAULT_GOALS = {"calorie": 2000.0, "protein": 60.0, "carb": 250.0, "fat": 65.0, "water": 2000.0}

# TDEE 活動係數

TDEE_MULTIPLIERS = {

    "幾乎不動": 1.2,

    "每週運動 1-3 天": 1.375,

    "每週運動 3-5 天": 1.55,

    "每週運動 6-7 天": 1.72,

    "每天激烈運動": 1.9,

}
EXERCISE_LEVELS = list(TDEE_MULTIPLIERS.keys())

# 訓練項目

TRAINING_TYPES = ["背", "胸", "腿", "核心", "有氧"]

TRAINING_EMOJI = {"背": "🏋️", "胸": "🏋️", "腿": "🦵", "核心": "🎯", "有氧": "🏃"}

# ---------- TDEE 計算 ----------

def _calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:

    if gender == "男":

        return 66 + (13.7 * weight) + (5.0 * height) - (6.8 * age)

    else:

        return 655 + (9.6 * weight) + (1.8 * height) - (4.7 * age)

def _calculate_tdee(bmr: float, exercise_level: str) -> float:

    multiplier = TDEE_MULTIPLIERS.get(exercise_level, 1.2)

    return bmr * multiplier

def _calculate_goals(weight: float, tdee: float, goal_type: str = "維持") -> dict[str, float]:

    protein = weight * 2

    fat = weight * 0.8

    carb = ((tdee - 100) - (protein * 4) - (fat * 9)) / 4

    water = weight * 40

    if goal_type == "減脂":

        calorie = tdee - 300

    elif goal_type == "增肌":

        calorie = tdee + 300

    else:

        calorie = tdee

    return {

        "bmr": 0,

        "calorie": max(0, calorie),

        "protein": protein,

        "carb": max(0, carb),

        "fat": fat,

        "water": water,

    }

# ---------- Session 初始化 ----------

def init_session() -> None:

    defaults = {

        "user_id": None,

        "username": None,

        "role": None,

        "page": "個人",

        "pending_meal_type": None,

        "input_mode": None,

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
    for fn_name in ("get_records", "get_weight_records", "get_training_records", "get_notes", "get_latest_weight", "get_users_rows", "get_student_by_id", "get_user_goals", "get_all_students"):
        fn = getattr(sheets, fn_name, None)
        if fn is None:
            continue
        try:
            fn.clear()
        except Exception:
            pass


def _run_analysis(image_bytes, content_type, text):

    if image_bytes is not None:

        image = Image.open(BytesIO(image_bytes))

        if image.mode != "RGB":

            image = image.convert("RGB")

        return gemini.analyze_image(image)

    return gemini.analyze_text(text)

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



def page_coach_overview() -> None:
    st.markdown("""<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
    .coach-header { display: flex; align-items: center; margin-bottom: 24px; }
    .coach-avatar { width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, #BBE8EE 0%, #8B5CF6 100%); display: flex; align-items: center; justify-content: center; font-size: 24px; margin-right: 16px; }
    .coach-greeting { font-size: 24px; font-weight: 400; color: #1F2937; }
    .member-card { display: flex; flex-direction: column; gap: 16px; padding: 16px; background: #fff; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; }
    .member-top-row { display: flex; align-items: center; gap: 12px; }
    .member-avatar { width: 48px; height: 48px; border-radius: 50%; background: #BBE8EE; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
    .member-name { font-size: 18px; font-weight: 500; color: #1F2937; }
    .member-avatar { width: 56px; height: 56px; border-radius: 50%; background: #BBE8EE; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-right: 20px; flex-shrink: 0; }
            .member-name { font-size: 18px; font-weight: 400; color: #1F2937; }
    .training-badge { background: #DCFCE7; color: #16A34A; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 4px; }
    .training-badge.not-done { background: #F3F4F6; color: #9CA3AF; }
    .capsule-container { display: flex; flex-direction: column; align-items: center; gap: 6px; width: 80px; }
    .capsule-track { position: relative; overflow: hidden; width: 64px; height: 200px; border-radius: 50px; background-color: #f0f4f1; }
    .capsule-fill { position: absolute; bottom: 0; left: 0; width: 100%; }
    .capsule-fill.cal { background: linear-gradient(180deg, #d4f0f5 0%, #bbe8ee 100%); }
    .capsule-fill.pro { background: linear-gradient(180deg, #e2f5dd 0%, #d1ebbe 100%); }
    .capsule-fill.water { background: linear-gradient(180deg, #ffe0a3 0%, #ffc766 100%); }
    .capsule-badge { position: absolute; left: 50%; transform: translateX(-50%); width: 52px; height: 52px; background-color: #ffffff; border-radius: 50%; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 400; color: #3c3c3c; z-index: 10; }
    .capsule-label { font-size: 12px; font-weight: 600; color: #6B7280; text-transform: uppercase; }
    .capsule-value { font-size: 10px; color: #9CA3AF; }
    .capsule-row { display: flex; gap: 24px; justify-content: center; padding: 16px 0; }
    .section-title { font-size: 18px; font-weight: 600; color: #1F2937; margin-bottom: 12px; }
    </style>""", unsafe_allow_html=True)
    
    coach_name = str(st.session_state.username or "Coach")
    st.markdown("<div class=\"coach-header\"><div class=\"coach-avatar\"></div><div class=\"coach-greeting\">Hello ! " + coach_name + "</div></div>", unsafe_allow_html=True)

    try:
        students = sheets.get_all_students()
    except Exception as exc:
        st.error("Failed to get students: " + str(exc))
        return
    
    if not students:
        st.info("No students yet.")
        return
    
    today = date.today()
    st.markdown("<p class=\"section-title\">本日學員狀態</p>", unsafe_allow_html=True)
    
    for student in students:
        uid = student.get("user_id", "")
        name = student.get("name", student.get("username", "Unknown"))
        goals = sheets.get_user_goals(uid)
        today_records = sheets.get_records_by_date(uid, today)
        totals = metrics.sum_totals(today_records).as_dict()
        training_today = sheets.get_training_by_date(uid, today)
        has_training = training_today is not None and any(v == 1 for v in training_today.values()) if training_today else False
        
        calorie_goal = goals.get("calorie", 0)
        protein_goal = goals.get("protein", 0)
        water_goal = goals.get("water", 0)
        calorie_actual = int(totals.get("calories", 0))
        protein_actual = int(totals.get("protein", 0))
        water_actual = int(totals.get("water", 0))
        
        cal_pct = min((calorie_actual / calorie_goal) * 100, 100) if calorie_goal > 0 else 0
        pro_pct = min((protein_actual / protein_goal) * 100, 100) if protein_goal > 0 else 0
        water_pct = min((water_actual / water_goal) * 100, 100) if water_goal > 0 else 0
        
        cal_top = 100 - cal_pct
        pro_top = 100 - pro_pct
        water_top = 100 - water_pct
        
        if has_training:
            training_html = "<i class=\"fas fa-check\"></i> Trained"
            training_class = ""
        else:
            training_html = "<i class=\"fas fa-times\"></i> Not trained"
            training_class = "not-done"
        
        surname = name[0] if name else "?"
        
        card_html = "<div class=\"member-card\"><div class=\"member-top-row\"><div class=\"member-avatar\">" + surname + "</div><div class=\"member-name\">" + name + "</div><div class=\"training-badge " + training_class + "\">" + training_html + "</div></div><div class=\"capsule-row\"><div class=\"capsule-container\"><div class=\"capsule-track\"><div class=\"capsule-fill cal\" style=\"height: " + str(cal_pct) + "%\"></div><div class=\"capsule-badge\" style=\"top: " + str(cal_top) + "%\">" + str(calorie_actual) + "</div></div><div class=\"capsule-label\">CAL</div><div class=\"capsule-value\">" + str(calorie_actual) + "/" + str(int(calorie_goal)) + "</div></div><div class=\"capsule-container\"><div class=\"capsule-track\"><div class=\"capsule-fill pro\" style=\"height: " + str(pro_pct) + "%\"></div><div class=\"capsule-badge\" style=\"top: " + str(pro_top) + "%\">" + str(protein_actual) + "</div></div><div class=\"capsule-label\">PROT</div><div class=\"capsule-value\">" + str(protein_actual) + "/" + str(int(protein_goal)) + "g</div></div><div class=\"capsule-container\"><div class=\"capsule-track\"><div class=\"capsule-fill water\" style=\"height: " + str(water_pct) + "%\"></div><div class=\"capsule-badge\" style=\"top: " + str(water_top) + "%\">" + str(water_actual) + "</div></div><div class=\"capsule-label\">WATER</div><div class=\"capsule-value\">" + str(water_actual) + "/" + str(int(water_goal)) + "</div></div></div></div>"
        st.markdown(card_html, unsafe_allow_html=True)
def page_coach_student_detail() -> None:

    uid = st.session_state.get("view_student_id")

    if not uid:

        st.error("未指定學員")

        return

    student = sheets.get_student_by_id(uid)

    if not student:

        st.error("找不到學員")

        return

    st.header(f"📋 學員：{student.get('username', '未知')}")

    if st.button("← 返回總覽"):

        st.session_state.page = "學員狀態"

        st.session_state.pop("view_student_id", None)

        st.rerun()

    st.divider()


    # ============================================================
    # Excel 匯入功能
    # ============================================================
    st.subheader("今日完成率")

    uploaded_file = st.file_uploader(
        "選擇 Excel 檔案（每個工作表代表一個月份）",
        type=["xlsx", "xls"],
        key="excel_import_file"
    )

    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.getvalue()
            
            # 第一次分析（不回寫）
            with st.spinner("分析 Excel 檔案中..."):
                analysis_result = sheets.import_records_from_excel(file_bytes, uid, overwrite_duplicates=False)

            # 顯示分析結果
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("可新增", f"{analysis_result['imported']} 筆")
            with col2:
                st.metric("將覆寫", f"{analysis_result['overwritten']} 筆")
            with col3:
                st.metric("將跳過", f"{analysis_result['skipped']} 筆")

            # 如果有錯誤，顯示警告
            if analysis_result["errors"]:
                with st.expander("⚠️ 匯入時的錯誤（點擊查看）"):
                    for err in analysis_result["errors"]:
                        st.warning(err)

            # 如果有重複，顯示並讓使用者選擇
            if analysis_result["duplicates"]:
                with st.expander(f"⚠️ 發現 {len(analysis_result['duplicates'])} 筆重複資料（點擊查看）"):
                    for dup in analysis_result["duplicates"][:20]:
                        st.write(f"📅 {dup['date']}｜現有熱量：{dup['existing'].get('calories', 0)} kcal")

            # 選擇匯入模式
            if analysis_result["imported"] > 0 or analysis_result["skipped"] > 0:
                overwrite_mode = st.radio(
                    "遇到重複日期怎麼辦？",
                    ["跳過（保留現有資料）", "覆寫（用新資料取代）"],
                    index=0,
                    horizontal=True,
                )
                do_overwrite = (overwrite_mode == "覆寫（用新資料取代）")

                if st.button("確認匯入", type="primary", use_container_width=True):
                    with st.spinner("匯入資料中..."):
                        # 第二次呼叫，實際寫入
                        final_result = sheets.import_records_from_excel(
                            precomputed_data=analysis_result['parsed_data'],
                            user_id=uid,
                            overwrite_duplicates=do_overwrite
                        )
                        _clear_analysis_cache()
                        
                        msg = f"匯入完成！新增 {final_result['imported']} 筆"
                        if final_result["overwritten"] > 0:
                            msg += f"，覆寫 {final_result['overwritten']} 筆"
                        if final_result["skipped"] > 0:
                            msg += f"，跳過 {final_result['skipped']} 筆"
                        st.success(msg)
                        
                        st.session_state.excel_import_file = None
                        st.info("請手動刷新頁面以查看最新資料")
            else:
                st.info("沒有找到可匯入的資料")

        except Exception as exc:
            st.error(f"讀取 Excel 失敗：{str(exc)}")

    st.divider()


    goals = sheets.get_user_goals(uid)

    today = date.today()

    today_records = sheets.get_records_by_date(uid, today)

    totals = metrics.sum_totals(today_records).as_dict()

    st.subheader("今日完成率")

    col1, col2 = st.columns(2)

    with col1:

        cal = totals.get("calories", 0)

        st.metric("熱量", f"{cal:.0f}", f"{goals.get('calorie', 0) - cal:.0f}")

    with col2:

        weight = sheets.get_latest_weight(uid)

        st.metric("體重", f"{weight:.1f}kg" if weight else "-", delta=None)

    st.divider()

    st.subheader("今日完成率")

    col1, col2 = st.columns(2)

    with col1:

        new_calorie = st.number_input("每日熱量目標 (kcal)", value=float(goals.get("calorie", 2000)), step=50.0)

        new_protein = st.number_input("每日蛋白質目標 (g)", value=float(goals.get("protein", 60)), step=5.0)

    with col2:

        new_carb = st.number_input("每日碳水目標 (g)", value=float(goals.get("carb", 250)), step=10.0)

        new_fat = st.number_input("每日脂肪目標 (g)", value=float(goals.get("fat", 65)), step=5.0)

        new_water = st.number_input("每日水量目標 (ml)", value=float(goals.get("water", 2000)), step=100.0)

    if st.button("儲存目標修改"):

        try:

            sheets.update_user_goals(uid, {

                "calorie": new_calorie,

                "protein": new_protein,

                "carb": new_carb,

                "fat": new_fat,

                "water": new_water,

            })

            _clear_analysis_cache()

            st.success("目標已更新！")

            st.rerun()

        except Exception as exc:

            st.error("更新失敗: " + str(exc))

    st.divider()

    st.subheader("今日完成率")

    weight_records = sheets.get_weight_records(uid)

    if weight_records:

        weight_data = {"日期": [], "體重 (kg)": []}

        for r in weight_records[-14:]:

            weight_data["日期"].append(r.get("timestamp", "")[:10])

            weight_data["體重 (kg)"].append(r.get("weight_kg", 0))

        st.line_chart(weight_data, x="日期", y="體重 (kg)")

    else:

        st.info("尚無體重記錄")

# =============================================================================
# 教練端：學員歷史頁面（圖表 / 教練備註 / 匯出 PDF + CSV）

# =============================================================================
# 教練端：學員歷史頁面（圖表 / 教練備註 / 匯出 PDF + CSV）
# =============================================================================

def _parse_record_date(ts):
    from datetime import date as _date
    try:
        return _date.fromisoformat(str(ts)[:10])
    except Exception:
        return _date.min


def _history_aggregate_daily(records, start_date, end_date):
    days = {}
    cur = start_date
    while cur <= end_date:
        days[cur] = {"calorie": 0.0, "protein": 0.0, "carb": 0.0, "fat": 0.0, "water": 0.0}
        cur = cur + timedelta(days=1)
    for r in records:
        d = _parse_record_date(r.get("timestamp", ""))
        if d in days:
            t = days[d]
            t["calorie"] += float(r.get("calories", 0) or 0)
            t["protein"] += float(r.get("protein", 0) or 0)
            t["carb"]    += float(r.get("carb", 0) or 0)
            t["fat"]     += float(r.get("fat", 0) or 0)
            t["water"]   += float(r.get("water_ml", r.get("water", 0)) or 0)
    return days


def _build_history_csv(student, daily, weights, trainings, notes, start_date, end_date):
    import csv
    buf = _io.StringIO()
    w = csv.writer(buf)
    name = student.get("name", student.get("username", "未知"))
    w.writerow(["學員：" + str(name)])
    w.writerow(["區間：" + str(start_date.isoformat()) + " ~ " + str(end_date.isoformat())])
    w.writerow([])
    w.writerow(["日期", "熱量 (kcal)", "蛋白質 (g)", "醣類 (g)", "脂質 (g)", "水量 (ml)", "體重 (kg)", "訓練項目"])
    weight_by_day = {}
    for r in weights:
        d = _parse_record_date(r.get("timestamp", ""))
        if d >= start_date:
            weight_by_day[d] = r.get("weight_kg", "")
    training_by_day = {}
    for r in trainings:
        d = _parse_record_date(r.get("timestamp", ""))
        if start_date <= d <= end_date:
            items = []
            if r.get("training_back"):   items.append("背")
            if r.get("training_chest"):  items.append("胸")
            if r.get("training_legs"):   items.append("腿")
            if r.get("training_core"):   items.append("核心")
            if r.get("training_cardio"): items.append("有氧")
            training_by_day[d] = "、".join(items) if items else ""
    for d in sorted(daily.keys()):
        v = daily[d]
        wd = weight_by_day.get(d, "")
        wd_str = (("%.1f" % wd) if isinstance(wd, (int, float)) else (wd if wd else ""))
        w.writerow([
            d.isoformat(),
            "%.0f" % v["calorie"],
            "%.0f" % v["protein"],
            "%.0f" % v["carb"],
            "%.0f" % v["fat"],
            "%.0f" % v["water"],
            wd_str,
            training_by_day.get(d, ""),
        ])
    if notes:
        w.writerow([])
        w.writerow(["教練備註"])
        w.writerow(["時間", "教練", "內容"])
        for n in notes:
            w.writerow([
                n.get("timestamp", "")[:19],
                n.get("coach_id", ""),
                n.get("note", "").replace("\n", " "),
            ])
    return ("\ufeff" + buf.getvalue()).encode("utf-8")

def _build_history_pdf(student, daily, weights, trainings, notes, start_date, end_date):
    # 中文字型設定
    # 中文字型設定
    import matplotlib.font_manager as fm
    # 嘗試使用系統中文字型
    # 內嵌中文字型（放在 assets/fonts/ 目錄）
    # 嘗試載入內嵌中文字型
    font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansTC-Regular.otf")

    if os.path.exists(font_path):
        # 使用 addfont 註冊字型
        try:
            fm.fontManager.addfont(font_path)
            _plt.rcParams["font.family"] = "sans-serif"
            _plt.rcParams["font.sans-serif"] = ["Noto Sans TC", "DejaVu Sans"]
        except Exception:
            prop = fm.FontProperties(fname=font_path)
            _plt.rcParams["font.family"] = prop.get_family()
            _plt.rcParams["font.sans-serif"] = [font_path]
    else:
        # Fallback 到系統字型
        font_paths = [
            "C:/Windows/Fonts/msjh.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    fm.fontManager.addfont(fp)
                    _plt.rcParams["font.family"] = "sans-serif"
                    _plt.rcParams["font.sans-serif"] = ["Noto Sans CJK TC", "DejaVu Sans"]
                except Exception:
                    prop = fm.FontProperties(fname=fp)
                    _plt.rcParams["font.family"] = prop.get_family()
                    _plt.rcParams["font.sans-serif"] = [fp]
                break
        else:
            _plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
            _plt.rcParams["font.family"] = "sans-serif"

    _plt.rcParams["axes.unicode_minus"] = False
    name = student.get("name", student.get("username", "未知"))
    buf = _io.BytesIO()
    with _PdfPages(buf) as pdf:
        # Page 1: 摘要
        fig = _plt.figure(figsize=(8.27, 11.69))
        fig.suptitle(str(name) + " 歷史紀錄", fontsize=18, fontweight="bold")
        ax = fig.add_subplot(111)
        ax.axis("off")
        days_count = (end_date - start_date).days + 1
        total_cal = sum(v["calorie"] for v in daily.values())
        total_pro = sum(v["protein"] for v in daily.values())
        total_water = sum(v["water"] for v in daily.values())
        avg_cal = total_cal / max(days_count, 1)
        avg_pro = total_pro / max(days_count, 1)
        sorted_weights = sorted(
            [r for r in weights if start_date <= _parse_record_date(r.get("timestamp", "")) <= end_date],
            key=lambda r: r.get("timestamp", ""),
        )
        first_w = sorted_weights[0].get("weight_kg") if sorted_weights else None
        last_w  = sorted_weights[-1].get("weight_kg") if sorted_weights else None
        weight_delta = (last_w - first_w) if (first_w is not None and last_w is not None) else None
        first_s = ("%.1f kg" % first_w) if first_w is not None else "-"
        last_s  = ("%.1f kg" % last_w)  if last_w  is not None else "-"
        delta_s = ""
        if weight_delta is not None:
            delta_s = "（%+.1f kg）" % weight_delta
        lines = [
            "區間：" + start_date.isoformat() + " ~ " + end_date.isoformat() + "（" + str(days_count) + " 天）",
            "",
            "平均熱量：%.0f kcal / 天" % avg_cal,
            "平均蛋白質：%.0f g / 天" % avg_pro,
            "總飲水量：%.0f ml" % total_water,
            "體重：" + first_s + " -> " + last_s + delta_s,
            "備註數：" + str(len(notes)) + " 筆",
        ]
        ax.text(0.05, 0.95, "\n".join(lines), va="top", ha="left", fontsize=12)
        pdf.savefig(fig, bbox_inches="tight")
        _plt.close(fig)

        # Page 2: 飲食組成圓餅
        total_pro2 = sum(v["protein"] for v in daily.values())
        total_carb = sum(v["carb"] for v in daily.values())
        total_fat = sum(v["fat"] for v in daily.values())
        if total_pro2 + total_carb + total_fat > 0:
            fig, ax = _plt.subplots(figsize=(8.27, 11.69))
            fig.suptitle("飲食組成（區間總和）", fontsize=16, fontweight="bold")
            ax.pie(
                [total_carb, total_pro2, total_fat],
                labels=[
                    "醣類\n%.0fg" % total_carb,
                    "蛋白質\n%.0fg" % total_pro2,
                    "脂質\n%.0fg" % total_fat,
                ],
                autopct="%1.1f%%",
                startangle=90,
                colors=["#FFD166", "#06D6A0", "#EF476F"],
            )
            ax.axis("equal")
            pdf.savefig(fig, bbox_inches="tight")
            _plt.close(fig)

        # Page 3: 熱量 / 蛋白質 / 水量
        if daily:
            xs = [d.strftime("%m/%d") for d in sorted(daily.keys())]
            cals = [daily[d]["calorie"] for d in sorted(daily.keys())]
            pros = [daily[d]["protein"] for d in sorted(daily.keys())]
            wats = [daily[d]["water"] for d in sorted(daily.keys())]
            fig, axes = _plt.subplots(3, 1, figsize=(8.27, 11.69))
            fig.suptitle("每日攝取趨勢", fontsize=16, fontweight="bold")
            axes[0].plot(xs, cals, marker="o", color="#118AB2")
            axes[0].set_title("熱量 (kcal)")
            axes[0].grid(True, alpha=0.3)
            axes[1].plot(xs, pros, marker="o", color="#06D6A0")
            axes[1].set_title("蛋白質 (g)")
            axes[1].grid(True, alpha=0.3)
            axes[2].bar(xs, wats, color="#073B4C")
            axes[2].set_title("水量 (ml)")
            axes[2].grid(True, alpha=0.3, axis="y")
            for a in axes:
                a.tick_params(axis="x", rotation=45)
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig, bbox_inches="tight")
            _plt.close(fig)

        # Page 4: 體重
        if sorted_weights:
            fig, ax = _plt.subplots(figsize=(8.27, 11.69))
            fig.suptitle("體重變化", fontsize=16, fontweight="bold")
            xs = [r.get("timestamp", "")[:10] for r in sorted_weights]
            ys = [r.get("weight_kg", 0) for r in sorted_weights]
            ax.plot(xs, ys, marker="o", color="#EF476F")
            ax.set_ylabel("kg")
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig, bbox_inches="tight")
            _plt.close(fig)

        # Page 5: 訓練 + 備註
        fig, ax = _plt.subplots(figsize=(8.27, 11.69))
        ax.axis("off")
        fig.suptitle("訓練記錄與教練備註", fontsize=16, fontweight="bold")
        text_lines = ["【訓練記錄】"]
        if trainings:
            for r in sorted(trainings, key=lambda x: x.get("timestamp", ""))[-20:]:
                items = []
                if r.get("training_back"):   items.append("背")
                if r.get("training_chest"):  items.append("胸")
                if r.get("training_legs"):   items.append("腿")
                if r.get("training_core"):   items.append("核心")
                if r.get("training_cardio"): items.append("有氧")
                text_lines.append("  " + r.get("timestamp", "")[:10] + "  " + ("、".join(items) if items else "-"))
        else:
            text_lines.append("  （無）")
        text_lines += ["", "【教練備註】"]
        if notes:
            for n in notes[-20:]:
                text_lines.append("  " + n.get("timestamp", "")[:19] + "  " + str(n.get("coach_id", "")) + "：" + str(n.get("note", "")))
        else:
            text_lines.append("  （無）")
        ax.text(0.05, 0.95, "\n".join(text_lines), va="top", ha="left", fontsize=10)
        pdf.savefig(fig, bbox_inches="tight")
        _plt.close(fig)
    return buf.getvalue()

def page_coach_student_history():
    """教練端：檢視單一學員的歷史記錄（圖表 / 備註 / 匯出）。"""
    uid = st.session_state.get("view_student_id")

    if not uid:
        try:
            students = sheets.get_all_students()
        except Exception as exc:
            st.error("取得學員列表失敗：" + str(exc))
            return
        st.header("學員歷史")
        if not students:
            st.info("目前沒有學員。")
            return
        st.caption("從總覽點選學員，或在此手動選擇：")
        labels = {}
        for s in students:
            labels[s.get("user_id", "")] = s.get("name", s.get("username", "未知"))
        picked = st.selectbox(
            "選擇學員",
            options=list(labels.keys()),
            format_func=lambda x: labels.get(x, x),
            key="hist_picker",
        )
        if st.button("查看歷史", type="primary", key="hist_picker_btn"):
            st.session_state.view_student_id = picked
            st.rerun()
        return

    student = sheets.get_student_by_id(uid)
    if not student:
        st.error("找不到學員，請返回總覽重新選擇。")
        if st.button("← 返回學員狀態", key="back_err"):
            st.session_state.page = "學員狀態"
            st.session_state.pop("view_student_id", None)
            st.rerun()
        return

    name = student.get("name", student.get("username", "未知"))
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← 返回總覽", key="back_top"):
            st.session_state.page = "學員狀態"
            st.session_state.pop("view_student_id", None)
            st.rerun()
    with col_title:
        st.header("📚 " + str(name) + " 的歷史記錄")
    st.divider()
    st.subheader("今日完成率")

    # ============================================================
    # Excel 匯入功能
    # ============================================================
    with st.expander("📥 匯入 Excel 資料"):
        uploaded_file = st.file_uploader(
            "選擇 Excel 檔案（每個工作表代表一個月份）",
            type=["xlsx", "xls"],
            key="excel_import_file_hist"
        )

        if uploaded_file is not None:
            try:
                file_bytes = uploaded_file.getvalue()
                
                with st.spinner("分析 Excel 檔案中..."):
                    analysis_result = sheets.import_records_from_excel(file_bytes, uid, overwrite_duplicates=False)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("可新增", f"{analysis_result['imported']} 筆")
                with col2:
                    st.metric("將覆寫", f"{analysis_result['overwritten']} 筆")
                with col3:
                    st.metric("將跳過", f"{analysis_result['skipped']} 筆")

                if analysis_result["errors"]:
                    with st.expander("⚠️ 匯入時的錯誤"):
                        for err in analysis_result["errors"]:
                            st.warning(err)

                if analysis_result["duplicates"]:
                    with st.expander(f"⚠️ 發現 {len(analysis_result['duplicates'])} 筆重複"):
                        for dup in analysis_result["duplicates"][:10]:
                            st.write(f"📅 {dup['date']}")

                if analysis_result["imported"] > 0 or analysis_result["skipped"] > 0:
                    overwrite_mode = st.radio(
                        "遇到重複日期：",
                        ["跳過", "覆寫"],
                        horizontal=True,
                    )
                    do_overwrite = (overwrite_mode == "覆寫")

                    if st.button("確認匯入", type="primary", use_container_width=True):
                        with st.spinner("匯入資料中..."):
                            final_result = sheets.import_records_from_excel(
                                precomputed_data=analysis_result['parsed_data'],
                                user_id=uid,
                                overwrite_duplicates=do_overwrite
                            )
                            _clear_analysis_cache()
                            
                            msg = f"匯入完成！新增 {final_result['imported']} 筆"
                            if final_result["overwritten"] > 0:
                                msg += f"，覆寫 {final_result['overwritten']} 筆"
                            if final_result["skipped"] > 0:
                                msg += f"，跳過 {final_result['skipped']} 筆"
                            st.success(msg)
                            
                            st.info("請手動刷新頁面以查看最新資料")
                else:
                    st.info("沒有找到可匯入的資料")

            except Exception as exc:
                st.error(f"讀取 Excel 失敗：{str(exc)}")

    st.divider()

    range_mode = st.radio(
        "範圍",
        ["7 天", "30 天", "自訂日期"],
        horizontal=True,
        index=0,
        label_visibility="collapsed",
        key="hist_range_mode",
    )
    today = date.today()
    if range_mode == "7 天":
        start_date = today - timedelta(days=6)
        end_date = today
    elif range_mode == "30 天":
        start_date = today - timedelta(days=29)
        end_date = today
    else:
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input(
                "開始日期",
                today - timedelta(days=6),
                max_value=today,
                key="hist_start",
            )
        with c2:
            end_date = st.date_input(
                "結束日期",
                today,
                max_value=today,
                key="hist_end",
            )
        if start_date > end_date:
            st.warning("開始日期不能晚於結束日期，已自動交換。")
            start_date, end_date = end_date, start_date
    days_count = (end_date - start_date).days + 1
    st.caption(
        "顯示區間："
        + start_date.strftime("%Y/%m/%d")
        + " ~ "
        + end_date.strftime("%Y/%m/%d")
        + "（共 "
        + str(days_count)
        + " 天）"
    )

    try:
        all_records = sheets.get_records(uid)
        all_weights = sheets.get_weight_records(uid)
        all_trainings = sheets.get_training_records(uid)
        all_notes = sheets.get_notes(uid)
        goals = sheets.get_user_goals(uid)
    except Exception as exc:
        st.error("取得資料失敗：" + str(exc))
        return

    daily = _history_aggregate_daily(all_records, start_date, end_date)
    weights = []
    for r in all_weights:
        d = _parse_record_date(r.get("timestamp", ""))
        if start_date <= d <= end_date:
            weights.append(r)
    trainings = []
    for r in all_trainings:
        d = _parse_record_date(r.get("timestamp", ""))
        if start_date <= d <= end_date:
            trainings.append(r)
    notes = []
    for r in all_notes:
        d = _parse_record_date(r.get("timestamp", ""))
        if start_date <= d <= end_date:
            notes.append(r)
    st.subheader("今日完成率")
    avg_cal = sum(v["calorie"] for v in daily.values()) / max(days_count, 1)
    avg_pro = sum(v["protein"] for v in daily.values()) / max(days_count, 1)
    avg_water = sum(v["water"] for v in daily.values()) / max(days_count, 1)
    sorted_w = sorted(weights, key=lambda r: r.get("timestamp", ""))
    first_w = None
    last_w = None
    weight_delta = None
    if sorted_w:
        first_w = sorted_w[0].get("weight_kg")
        last_w = sorted_w[-1].get("weight_kg")
        if first_w is not None and last_w is not None:
            weight_delta = last_w - first_w
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("平均熱量", "%.0f kcal" % avg_cal, "目標 %.0f" % goals.get("calorie", 0))
    with mc2:
        st.metric("平均蛋白質", "%.0f g" % avg_pro, "目標 %.0f" % goals.get("protein", 0))
    with mc3:
        st.metric("平均水量", "%.0f ml" % avg_water, "目標 %.0f" % goals.get("water", 0))
    with mc4:
        if last_w is not None:
            d_str = ("%+.1f kg" % weight_delta) if weight_delta is not None else None
            st.metric("目前體重", "%.1f kg" % last_w, d_str)
        else:
            st.metric("目前體重", "-")
    # 統一的高質感深夜底色
    CARD_BG = '#2a2850'
    # 統一強制套用系統原生高質感字型
    FONT_SETTING = dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif")

    # ==========================================
    # 體重趨勢圖
    # ==========================================
    if weights:
        # 準備體重數據
        def parse_weight_date(ts):
            ts_str = str(ts)
            # 嘗試解析 ISO 格式: 2026-07-15T10:30:00
            if "T" in ts_str:
                try:
                    dt = datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")
                    return dt.strftime("%m/%d")
                except:
                    pass
            # 回退：直接取日期部分
            if "-" in ts_str:
                parts = ts_str.split(" ")[0].split("-")
                if len(parts) >= 3:
                    return f"{int(parts[1]):02d}/{int(parts[2]):02d}"
            return ts_str[:10]
        
        weight_xs = [parse_weight_date(r.get("timestamp", "")) for r in sorted_w]
        weight_ys = [r.get("weight_kg", 0) for r in sorted_w]
        # 自適應 Y軸範圍
        min_w = min(weight_ys) if weight_ys else 0
        max_w = max(weight_ys) if weight_ys else 100
        weight_range = max_w - min_w
        
        # 根據範圍選擇刻度間隔
        if weight_range < 5:
            step = 1
        elif weight_range < 10:
            step = 2
        elif weight_range < 20:
            step = 5
        else:
            step = 10
        
        # 計算 Y軸範圍（加入緩衝）
        y_min = int(min_w) - step
        y_max = int(max_w) + step
        # 確保不為負數
        y_min = max(0, y_min)
        
        # 生成刻度列表
        weight_ticks = list(range(y_min, y_max + 1, step))

        last_weight = weight_ys[-1] if weight_ys else 0
        first_weight = weight_ys[0] if weight_ys else 0
        weight_change = last_weight - first_weight
        
        fig_weight = go.Figure()
        
        fig_weight.add_trace(go.Scatter(
            x=weight_xs,
            y=weight_ys,
            mode='lines+markers',
            line=dict(color='#ffffff', width=3, shape='spline'),
            marker=dict(size=6, color='#16152b', line=dict(color='#ffffff', width=2)),
            fill='tozeroy',
            fillcolor='rgba(255, 255, 255, 0.04)',
            hovertemplate='日期: %{x}<br>體重: %{y:.1f} kg<extra></extra>'
        ))
        
        change_str = f"{weight_change:+.1f}" if weight_change != 0 else "0.0"
        
        fig_weight.update_layout(
            paper_bgcolor=CARD_BG,
            plot_bgcolor=CARD_BG,
            margin=dict(l=40, r=25, t=90, b=25),
            height=260,
            font=FONT_SETTING,
            annotations=[
                dict(x=0.01, y=1.40, xref="paper", yref="paper",
                    text=f"<b style='font-size:32px; color:#ffffff;'>{last_weight:.1f}</b> <span style='font-size:14px; color:#a0a0a0; font-weight:normal;'>kg</span>",
                    showarrow=False, align="left"),
                dict(x=0.01, y=1.12, xref="paper", yref="paper",
                    text=f"<span style='font-size:12px; color:#a0a0a0; font-weight:normal;'>體重 {change_str} kg</span>",
                    showarrow=False, align="left")
            ],
            xaxis=dict(showgrid=False, tickfont=dict(color='#888888', size=12), showline=False, ticks=""),
            yaxis=dict(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", tickfont=dict(color="#888888", size=11), zeroline=False, showline=False, ticks="", tickvals=weight_ticks, range=[y_min, y_max]),
            showlegend=False
        )
        
        st.plotly_chart(fig_weight, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("此區間沒有體重記錄。")



    # 統一的高質感深夜底色
    st.subheader("今日完成率")

    # 深色卡片趨勢圖 CSS
    st.markdown("""<style>
        .chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 20px 20px 5px 20px !important; margin: 15px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; box-sizing: border-box !important; }
        .chart-value { font-size: 28px !important; font-weight: 700 !important; color: #ffffff !important; }
        .chart-unit { font-size: 14px !important; color: #a0a0a0 !important; }
        .chart-emoji { font-size: 32px !important; }
        .chart-header { display: flex !important; justify-content: space-between !important; align-items: center !important; margin-bottom: 16px !important; }
    </style>""", unsafe_allow_html=True)

    
    if daily:
        sorted_days = sorted(daily.keys())
        xs = [d.strftime("%m/%d") for d in sorted_days]

        # ----- 1. 準備數據 -----
        cals = [daily[d]["calorie"] for d in sorted_days]
        pros = [daily[d]["protein"] for d in sorted_days]

        total_cal = sum(cals)
        avg_cal = total_cal / len(sorted_days) if sorted_days else 0

        total_pro = sum(pros)
        avg_pro = total_pro / len(sorted_days) if sorted_days else 0


        # ==========================================
        # CSS：Plotly 容器圓角與陰影
        # ==========================================
        st.markdown("""
        <style>
            div[data-testid="stPlotlyChart"] {
                border-radius: 24px !important;
                overflow: hidden !important;
                box-shadow: 0 12px 40px rgba(0,0,0,0.3) !important;
                margin: 15px 0 !important;
                background-color: #16152b !important;
            }
        </style>
        """, unsafe_allow_html=True)


        # ==========================================
        # 1. 一體化熱量趨勢圖
        # ==========================================
        max_cal = max(cals) if cals else 0
        cal_ticks = []
        if max_cal > 0:
            cal_ticks = [v for v in [1000, 1500, 2000, 2500, 3000, 3500, 4000] if v <= max_cal * 1.2]
            if not cal_ticks or cal_ticks[-1] < max_cal:
                cal_ticks.append(((max_cal // 500) + 1) * 500)

        fig_cal = go.Figure()

        fig_cal.add_trace(go.Scatter(
            x=xs,
            y=cals,
            mode='lines+markers',
            line=dict(color='#ffffff', width=3, shape='spline'),
            marker=dict(size=6, color='#16152b', line=dict(color='#ffffff', width=2)),
            fill='tozeroy',
            fillcolor='rgba(255, 255, 255, 0.04)',
            hovertemplate='日期: %{x}<br>熱量: %{y:.0f} kcal<extra></extra>'
        ))

        fig_cal.update_layout(
            paper_bgcolor=CARD_BG,
            plot_bgcolor=CARD_BG,
            margin=dict(l=40, r=25, t=90, b=25),
            height=260,
            font=FONT_SETTING,
            annotations=[
                dict(x=0.01, y=1.40, xref="paper", yref="paper",
                    text=f"<b style='font-size:32px; color:#ffffff;'>" + f"{avg_cal:.1f}" + "</b> <span style='font-size:14px; color:#a0a0a0; font-weight:normal;'>kcal</span>",
                    showarrow=False, align="left"),
                dict(x=0.01, y=1.12, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#a0a0a0; font-weight:normal;'>平均每日熱量</span>",
                    showarrow=False, align="left")
            ],
            xaxis=dict(showgrid=False, tickfont=dict(color='#888888', size=12), showline=False, ticks=""),
            yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)', tickfont=dict(color='#888888', size=11), zeroline=False, showline=False, ticks="", tickvals=cal_ticks if cal_ticks else None),
            showlegend=False
        )

        st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})

        # ==========================================
        # 2. 一體化蛋白質趨勢圖
        # ==========================================
        max_pro = max(pros) if pros else 0
        pro_ticks = []
        if max_pro > 0:
            pro_ticks = [v for v in [50, 100, 150, 200, 250] if v <= max_pro * 1.2]
            if not pro_ticks or pro_ticks[-1] < max_pro:
                pro_ticks.append(((max_pro // 25) + 1) * 25)

        fig_pro = go.Figure()

        fig_pro.add_trace(go.Scatter(
            x=xs,
            y=pros,
            mode='lines+markers',
            line=dict(color='#ffffff', width=3, shape='spline'),
            marker=dict(size=6, color='#16152b', line=dict(color='#ffffff', width=2)),
            fill='tozeroy',
            fillcolor='rgba(255, 255, 255, 0.04)',
            hovertemplate='日期: %{x}<br>蛋白質: %{y:.0f} g<extra></extra>'
        ))

        fig_pro.update_layout(
            paper_bgcolor=CARD_BG,
            plot_bgcolor=CARD_BG,
            margin=dict(l=40, r=25, t=90, b=25),
            height=260,
            font=FONT_SETTING,
            annotations=[
                dict(x=0.01, y=1.40, xref="paper", yref="paper",
                    text=f"<b style='font-size:32px; color:#ffffff;'>" + f"{avg_pro:.1f}" + "</b> <span style='font-size:14px; color:#a0a0a0; font-weight:normal;'>g</span>",
                    showarrow=False, align="left"),
                dict(x=0.01, y=1.12, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#a0a0a0; font-weight:normal;'>平均每日蛋白質</span>",
                    showarrow=False, align="left")
            ],
            xaxis=dict(showgrid=False, tickfont=dict(color='#888888', size=12), showline=False, ticks=""),
            yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)', tickfont=dict(color='#888888', size=11), zeroline=False, showline=False, ticks="", tickvals=pro_ticks if pro_ticks else None),
            showlegend=False
        )

        st.plotly_chart(fig_pro, use_container_width=True, config={'displayModeBar': False})

        # ----- 4. 水量趨勢圖 -----

        # ==========================================
        # 3. 一體化水量趨勢圖
        # ==========================================
        waters = [daily[d]["water"] for d in sorted_days]
        max_water = max(waters) if waters else 0
        water_ticks = []
        if max_water > 0:
            water_ticks = [v for v in [1000, 1500, 2000, 2500, 3000, 3500, 4000] if v <= max_water * 1.2]
            if not water_ticks or water_ticks[-1] < max_water:
                water_ticks.append(((max_water // 500) + 1) * 500)

        fig_water = go.Figure()

        fig_water.add_trace(go.Scatter(
            x=xs,
            y=waters,
            mode='lines+markers',
            line=dict(color='#ffffff', width=3, shape='spline'),
            marker=dict(size=6, color='#16152b', line=dict(color='#ffffff', width=2)),
            fill='tozeroy',
            fillcolor='rgba(255, 255, 255, 0.04)',
            hovertemplate='日期: %{x}<br>水量: %{y:.0f} ml<extra></extra>'
        ))

        fig_water.update_layout(
            paper_bgcolor=CARD_BG,
            plot_bgcolor=CARD_BG,
            margin=dict(l=40, r=25, t=90, b=25),
            height=260,
            font=FONT_SETTING,
            annotations=[
                dict(x=0.01, y=1.40, xref="paper", yref="paper",
                    text=f"<b style='font-size:32px; color:#ffffff;'>{(sum(waters)/len(waters) if waters else 0):.1f}</b> <span style='font-size:14px; color:#a0a0a0; font-weight:normal;'>ml</span>",
                    showarrow=False, align="left"),
                dict(x=0.01, y=1.12, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#a0a0a0; font-weight:normal;'>平均每日水量</span>",
                    showarrow=False, align="left")
            ],
            xaxis=dict(showgrid=False, tickfont=dict(color='#888888', size=12), showline=False, ticks=""),
            yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)', tickfont=dict(color='#888888', size=11), zeroline=False, showline=False, ticks="", tickvals=water_ticks if water_ticks else None),
            showlegend=False
        )

        st.plotly_chart(fig_water, use_container_width=True, config={'displayModeBar': False})


    else:
        st.info("此區間沒有飲食記錄。")


    st.subheader("今日完成率")
    if trainings:
        rows = []
        for r in sorted(trainings, key=lambda x: x.get("timestamp", "")):
            items = []
            if r.get("training_back"):   items.append("背")
            if r.get("training_chest"):  items.append("胸")
            if r.get("training_legs"):   items.append("腿")
            if r.get("training_core"):   items.append("核心")
            if r.get("training_cardio"): items.append("有氧")
            rows.append({
                "日期": r.get("timestamp", "")[:10],
                "訓練項目": "、".join(items) if items else "無",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("此區間沒有訓練記錄。")


    st.subheader("今日完成率")
    csv_bytes = _build_history_csv(student, daily, weights, trainings, notes, start_date, end_date)
    pdf_bytes = _build_history_pdf(student, daily, weights, trainings, notes, start_date, end_date)
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "下載 CSV",
            data=csv_bytes,
            file_name=str(name) + "_歷史_" + start_date.isoformat() + "_" + end_date.isoformat() + ".csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv",
        )
    with ec2:
        st.download_button(
            "下載 PDF",
            data=pdf_bytes,
            file_name=str(name) + "_歷史_" + start_date.isoformat() + "_" + end_date.isoformat() + ".pdf",
            mime="application/pdf",
            use_container_width=True,
            key="dl_pdf",
        )


# =============================================================================

# END_HISTORY_BLOCK

# =============================================================================

def page_tdee_questionnaire() -> None:

    st.header("📋 設定你的營養目標")

    st.caption("回答以下問題，讓系統為你計算個人化的營養目標")

    with st.form("tdee_form"):

        st.subheader("今日完成率")

        col1, col2 = st.columns(2)

        with col1:

            weight = st.number_input("體重 (kg)", value=60.0, step=0.1, min_value=30.0, max_value=200.0)

            height = st.number_input("身高 (cm)", value=165.0, step=0.1, min_value=100.0, max_value=250.0)

        with col2:

            age = st.number_input("年齡", value=25, step=1, min_value=10, max_value=100)

            gender = st.radio("性別", ["男", "女"], horizontal=True)

        st.subheader("今日完成率")

        exercise_level = st.selectbox("每週運動頻率", EXERCISE_LEVELS, index=1)

        st.subheader("今日完成率")

        goal_type = st.radio("你的目標是？", ["減脂", "維持", "增肌"], horizontal=True, index=1)

        st.subheader("今日完成率")

        record_mode = st.radio(

            "選擇飲食記錄模式",

            ["簡易模式（蛋白質/熱量/水量）", "完整模式（蛋白質/碳水/脂肪/熱量/水量）"],

            horizontal=False,

        )

        mode = "simple" if "簡易" in record_mode else "full"

        submitted = st.form_submit_button("計算並儲存目標", use_container_width=True)

    if submitted:

        bmr = _calculate_bmr(weight, height, age, gender)

        tdee = _calculate_tdee(bmr, exercise_level)

        goals = _calculate_goals(weight, tdee, goal_type)

        goals["bmr"] = bmr

        try:

            uid = st.session_state.user_id

            sheets.update_user_bmr(uid, bmr)

            sheets.update_user_goals(uid, goals)

            sheets.set_user_record_mode(uid, mode)

            if mode == "simple":

                sheets.update_user_goals(uid, {"carb": 0.0, "fat": 0.0})

            _clear_analysis_cache()

            st.success("目標設定完成！")

            st.balloons()

            st.session_state.page = "個人"

            st.rerun()

        except Exception as exc:

            st.error("儲存失敗: " + str(exc))

# =============================================================================

# 登入頁面

# =============================================================================


def page_login() -> None:
    st.title("飲食控制管理系統")
    st.caption("輕鬆記錄飲食，追蹤你的營養目標")

    # 確保 auth_mode 存在
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    if st.session_state.auth_mode == "login":
        # ==================== 登入表單 ====================
        with st.form("login_form"):
            username = st.text_input("帳號", key="login_user")
            password = st.text_input("密碼", type="password", key="login_pwd")
            submit = st.form_submit_button("登入", use_container_width=True)

        if submit:
            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error("取得使用者失敗: " + str(exc))
                return
            user = auth.find_user(rows, username)
            if not user:
                st.error("找不到此帳號")
                return
            if not auth.verify_password(password, user.get("password_hash", "")):
                st.error("密碼錯誤")
                return

            st.session_state.user_id = user.get("user_id")
            st.session_state.username = user.get("username")
            st.session_state.role = sheets.get_user_role(str(user.get("user_id") or ""))

            if st.session_state.role == "coach":
                st.session_state.page = "學員狀態"
            else:
                st.session_state.page = "個人"
            st.success("登入成功！")
            st.rerun()

        # 切換到註冊
        if st.button("還沒有帳號？立即註冊", key="nav_to_register"):
            st.session_state.auth_mode = "register"
            st.rerun()

    else:
        # ==================== 註冊表單 ====================
        st.subheader("今日完成率")
        st.info("填寫以下資料即可建立帳號")

        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_user = st.text_input("帳號", placeholder="輸入帳號")
                new_name = st.text_input("姓名", placeholder="輸入真實姓名")
                new_pwd = st.text_input("密碼", type="password")
                new_pwd2 = st.text_input("確認密碼", type="password")
            with col2:
                initial_weight = st.number_input("目前體重 (kg)", value=60.0, step=0.1, min_value=30.0, max_value=200.0)
                goal_type = st.selectbox("目標", ["減脂", "維持", "增肌"], index=1)
                record_mode = st.radio("記錄模式", ["簡易模式", "完整模式"], horizontal=True, index=0)

            submitted = st.form_submit_button("註冊並登入", use_container_width=True)

        if submitted:
            if not new_user or not new_name or not new_pwd:
                st.error("帳號、姓名和密碼都不能為空")
                return
            if new_pwd != new_pwd2:
                st.error("兩次密碼不一致")
                return
            if len(new_pwd) < 4:
                st.warning("密碼建議至少 4 個字元")

            try:
                rows = sheets.get_users_rows()
            except Exception as exc:
                st.error("取得使用者失敗: " + str(exc))
                return

            if auth.find_user(rows, new_user):
                st.error("此帳號已被使用")
                return

            try:
                uid = auth.make_user_id()
                pwd_hash = auth.hash_password(new_pwd)

                estimated_tdee = initial_weight * 30
                if goal_type == "減脂":
                    calorie = estimated_tdee - 300
                elif goal_type == "增肌":
                    calorie = estimated_tdee + 300
                else:
                    calorie = estimated_tdee

                protein = initial_weight * 2
                water = initial_weight * 40

                goals = {
                    "calorie": calorie,
                    "protein": protein,
                    "carb": 0,
                    "fat": 0,
                    "water": water,
                }

                sheets.append_user(
                    uid, new_user, new_name, pwd_hash, auth.now_iso(),
                    goals=goals,
                    record_mode="simple" if "簡易" in record_mode else "full",
                    weekly_training=4,
                )

                st.session_state.user_id = uid
                st.session_state.username = new_user
                st.session_state.role = "student"
                st.session_state.needs_tdee_setup = True
                st.success("註冊成功！請先填寫 TDEE 問卷完成設定")
                st.rerun()

            except Exception as exc:
                st.error("註冊失敗: " + str(exc))

        # 切換回登入
        if st.button("已經有帳號了？立即登入", key="nav_to_login"):
            st.session_state.auth_mode = "login"
            st.rerun()



def page_personal() -> None:

    st.header("📊 今日摘要")

    uid = st.session_state.user_id

    try:

        records = _fetch_records_cached(uid)

        goals = _fetch_goals_cached(uid)

    except Exception as exc:

        st.error("取得資料失敗: " + str(exc))

        return

    bmr = goals.get("bmr", 0)

    calorie_goal = goals.get("calorie", 0)

    if bmr <= 0 or calorie_goal <= 0:

        st.warning("你尚未設定營養目標")

        st.info("請先回答 TDEE 問卷，系統會為你計算個人化的營養目標")

        if st.button("前往 TDEE 問卷", use_container_width=True):

            st.session_state.page = "TDEE 問卷"

            st.rerun()

        return

    ws, we = _today_range()

    today_records = metrics.filter_records(records, ws, we)

    totals = metrics.sum_totals(today_records).as_dict()

    st.subheader("今日完成率")

    col1, col2 = st.columns(2)

    with col1:

        st.metric("基礎代謝率 (BMR)", f"{bmr:.0f} 大卡")

    with col2:

        st.metric("建議熱量攝取", f"{calorie_goal:.0f} 大卡")


    st.divider()

    st.subheader("今日完成率")

    record_mode = sheets.get_user_record_mode(uid)

    if record_mode == "full":

        col1, col2, col3 = st.columns(3)

        with col1:
            # CSS for calories chart
            st.markdown("""
<style>
    .cal-chart-full div[data-testid="stPlotlyChart"] {
        border-radius: 24px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04) !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

            # Calculate calorie percentage
            cal_pct = min(totals.get("calories", 0) / calorie_goal * 100, 100) if calorie_goal > 0 else 0
            
            FONT_SETTING = dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
            CAL_CARD_BG = "#ffffff"
            
            fig_cal = go.Figure()
            fig_cal.add_trace(go.Pie(
                values=[cal_pct, 100 - cal_pct],
                hole=0.76,
                domain=dict(x=[0, 1], y=[0, 1]),
                marker=dict(colors=['#ffbfa3', '#f0f0f0']),
                sort=False,
                direction='clockwise',
                showlegend=False,
                hoverinfo='none',
                textinfo='none'
            ))
            fig_cal.update_layout(
                paper_bgcolor=CAL_CARD_BG,
                plot_bgcolor=CAL_CARD_BG,
                margin=dict(l=10, r=10, t=50, b=10),
                height=180,
                font=FONT_SETTING,
                annotations=[
                    dict(
                        x=0.02, y=1.22, xref="paper", yref="paper",
                        text="<span style='font-size:15px; color:#1a1a1a; font-weight:600; font-family: sans-serif;'>Calories</span>",
                        showarrow=False, align="left"
                    ),
                    dict(
                        x=0.5, y=0.5, xref="paper", yref="paper",
                        text=f"<b style='font-size:28px; color:#1a1a1a;'>{totals.get('calories', 0):.0f}</b>",
                        showarrow=False, align="center"
                    ),
                    dict(
                        x=0.5, y=0.22, xref="paper", yref="paper",
                        text="<span style='font-size:12px; color:#666666; font-weight:500;'>Kcal</span>",
                        showarrow=False, align="center"
                    )
                ]
            )
            st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})

        with col2:

            carb = totals.get("carb", 0)

            st.metric("碳水", f"{carb:.0f}g", f"{goals.get('carb', 0) - carb:.0f}g")

        with col3:

            fat = totals.get("fat", 0)

            st.metric("脂肪", f"{fat:.0f}g", f"{goals.get('fat', 0) - fat:.0f}g")

    else:

        col1, col2, col3 = st.columns(3)

        with col1:
            # CSS for calories chart
            st.markdown("""
<style>
    .cal-chart-simple div[data-testid="stPlotlyChart"] {
        border-radius: 24px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04) !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

            # Calculate calorie percentage
            cal_pct = min(totals.get("calories", 0) / calorie_goal * 100, 100) if calorie_goal > 0 else 0
            
            FONT_SETTING = dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
            CAL_CARD_BG = "#ffffff"
            
            fig_cal = go.Figure()
            fig_cal.add_trace(go.Pie(
                values=[cal_pct, 100 - cal_pct],
                hole=0.76,
                domain=dict(x=[0, 1], y=[0, 1]),
                marker=dict(colors=['#ffbfa3', '#f0f0f0']),
                sort=False,
                direction='clockwise',
                showlegend=False,
                hoverinfo='none',
                textinfo='none'
            ))
            fig_cal.update_layout(
                paper_bgcolor=CAL_CARD_BG,
                plot_bgcolor=CAL_CARD_BG,
                margin=dict(l=10, r=10, t=50, b=10),
                height=180,
                font=FONT_SETTING,
                annotations=[
                    dict(
                        x=0.02, y=1.22, xref="paper", yref="paper",
                        text="<span style='font-size:15px; color:#1a1a1a; font-weight:600; font-family: sans-serif;'>Calories</span>",
                        showarrow=False, align="left"
                    ),
                    dict(
                        x=0.5, y=0.5, xref="paper", yref="paper",
                        text=f"<b style='font-size:28px; color:#1a1a1a;'>{totals.get('calories', 0):.0f}</b>",
                        showarrow=False, align="center"
                    ),
                    dict(
                        x=0.5, y=0.22, xref="paper", yref="paper",
                        text="<span style='font-size:12px; color:#666666; font-weight:500;'>Kcal</span>",
                        showarrow=False, align="center"
                    )
                ]
            )
            st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})

        with col2:

            pro = totals.get("protein", 0)

            st.metric("蛋白質", f"{pro:.0f}g", f"{goals.get('protein', 0) - pro:.0f}g")

        with col3:

            water = totals.get("water", 0)

            st.metric("水量", f"{water:.0f}ml", f"{goals.get('water', 0) - water:.0f}ml")

    st.divider()

    # CSS for pie charts
    st.markdown("""
<style>
    div[data-testid="stPlotlyChart"] {
        border-radius: 24px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 24px rgba(199, 237, 246, 0.3) !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

    st.subheader("今日完成率")

    # 定義比由變参
    cal_ratio = min(totals.get("calories", 0) / calorie_goal, 1.5) if calorie_goal > 0 else 0
    pro_ratio = min(totals.get("protein", 0) / goals.get("protein", 1), 1.5) if goals.get("protein", 0) > 0 else 0
    water_ratio = min(totals.get("water", 0) / goals.get("water", 1), 1.5) if goals.get("water", 0) > 0 else 0

    # 建立三欄，將 食飼、水量、蛋質膜質 橫向並排
    cal_pct = min(cal_ratio * 100, 100)
    water_pct = min(water_ratio * 100, 100)
    pro_pct = min(pro_ratio * 100, 100)
    
    # 取得今日日期字串
    today_str = date.today().strftime("%d %B")

    # 定義统一的卡粉色胊背景背能
    CARD_BG_COLOR = "#c7edf6"

    # ?????? ????????? ????
    col1, col2, col3 = st.columns(3)

    # ?????? ????????? ????
    with col1:
        fig_cal = go.Figure()
        fig_cal.add_trace(go.Pie(
            values=[cal_pct, 100 - cal_pct],
            hole=0.75,
            marker=dict(colors=['#ffffff', 'rgba(255, 255, 255, 0.3)']),
            sort=False,
            direction='clockwise',
            showlegend=False,
            hoverinfo='none',
            textinfo='none'
        ))
        fig_cal.update_layout(
            paper_bgcolor=CARD_BG_COLOR,
            plot_bgcolor=CARD_BG_COLOR,
            margin=dict(l=20, r=20, t=20, b=20),
            height=160,
            annotations=[
                dict(
                    x=0.75, y=0.5, xref="paper", yref="paper",
                    text=f"<b style='font-size:20px; color:#1a2530;'>{totals.get('calories', 0):.0f}</b><br><span style='font-size:10px; color:#5a6e7f;'>kcal</span>",
                    showarrow=False, align="center"
                ),
                dict(
                    x=0.05, y=0.90, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#5a6e7f; font-weight:600;'>飲食進度</span>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.50, xref="paper", yref="paper",
                    text=f"<b style='font-size:36px; color:#1a2530;'>{cal_pct:.0f}%</b>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.10, xref="paper", yref="paper",
                    text=f"<span style='font-size:11px; color:#5a6e7f;'>{today_str}</span>",
                    showarrow=False, align="left"
                )
            ]
        )
        st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})

    # 
    with col2:
        fig_water = go.Figure()
        fig_water.add_trace(go.Pie(
            values=[water_pct, 100 - water_pct],
            hole=0.75,
            marker=dict(colors=['#ffffff', 'rgba(255, 255, 255, 0.3)']),
            sort=False,
            direction='clockwise',
            showlegend=False,
            hoverinfo='none',
            textinfo='none'
        ))
        fig_water.update_layout(
            paper_bgcolor=CARD_BG_COLOR,
            plot_bgcolor=CARD_BG_COLOR,
            margin=dict(l=20, r=20, t=20, b=20),
            height=160,
            annotations=[
                dict(
                    x=0.75, y=0.5, xref="paper", yref="paper",
                    text=f"<b style='font-size:18px; color:#1a2530;'>{totals.get('water', 0):.0f}</b><br><span style='font-size:10px; color:#5a6e7f;'>ml</span>",
                    showarrow=False, align="center"
                ),
                dict(
                    x=0.05, y=0.90, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#5a6e7f; font-weight:600;'>水量進度</span>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.50, xref="paper", yref="paper",
                    text=f"<b style='font-size:36px; color:#1a2530;'>{water_pct:.0f}%</b>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.10, xref="paper", yref="paper",
                    text=f"<span style='font-size:11px; color:#5a6e7f;'>{today_str}</span>",
                    showarrow=False, align="left"
                )
            ]
        )
        st.plotly_chart(fig_water, use_container_width=True, config={'displayModeBar': False})

    # 水量圓環卡區
    with col3:
        fig_pro = go.Figure()
        fig_pro.add_trace(go.Pie(
            values=[pro_pct, 100 - pro_pct],
            hole=0.75,
            marker=dict(colors=['#ffffff', 'rgba(255, 255, 255, 0.3)']),
            sort=False,
            direction='clockwise',
            showlegend=False,
            hoverinfo='none',
            textinfo='none'
        ))
        fig_pro.update_layout(
            paper_bgcolor=CARD_BG_COLOR,
            plot_bgcolor=CARD_BG_COLOR,
            margin=dict(l=20, r=20, t=20, b=20),
            height=160,
            annotations=[
                dict(
                    x=0.75, y=0.5, xref="paper", yref="paper",
                    text=f"<b style='font-size:20px; color:#1a2530;'>{totals.get('protein', 0):.0f}</b><br><span style='font-size:10px; color:#5a6e7f;'>g</span>",
                    showarrow=False, align="center"
                ),
                dict(
                    x=0.05, y=0.90, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#5a6e7f; font-weight:600;'>蛋白質進度</span>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.50, xref="paper", yref="paper",
                    text=f"<b style='font-size:36px; color:#1a2530;'>{pro_pct:.0f}%</b>",
                    showarrow=False, align="left"
                ),
                dict(
                    x=0.05, y=0.10, xref="paper", yref="paper",
                    text=f"<span style='font-size:11px; color:#5a6e7f;'>{today_str}</span>",
                    showarrow=False, align="left"
                )
            ]
        )
        st.plotly_chart(fig_pro, use_container_width=True, config={'displayModeBar': False})

    st.divider()

    # ============================================================
    st.subheader("⚖️ 體重")

    # 注入精確定位與排版的 CSS
    st.markdown("""
    <style>
        .weight-card-container {
            position: relative !important;
            width: 100% !important;
            margin-bottom: 20px !important;
        }

        .weight-card {
            background-color: #f8f8f8 !important;
            border-radius: 24px !important;
            padding: 24px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03) !important;
            box-sizing: border-box !important;
        }
        
        .weight-title {
            font-size: 16px !important;
            font-weight: 500 !important;
            color: #1a1a1a !important;
            margin-bottom: 12px !important;
            font-family: system-ui, -apple-system, sans-serif !important;
        }
        
        .weight-value {
            font-size: 36px !important;
            font-weight: 700 !important;
            color: #1a1a1a !important;
            font-family: system-ui, -apple-system, sans-serif !important;
            line-height: 1 !important;
        }
        
        .weight-unit {
            font-size: 18px !important;
            font-weight: normal !important;
            color: #a0a0a0 !important;
            margin-left: 6px !important;
        }

        .weight-trend {
            font-size: 14px !important;
            color: #1a1a1a !important;
            font-weight: 500 !important;
            margin-top: 12px !important;
            display: flex !important;
            align-items: center !important;
            font-family: system-ui, -apple-system, sans-serif !important;
        }

        .stApp div[data-testid="element-container"]:has(button[key="weight_lightning_btn"]) {
            position: absolute !important;
            top: 24px !important;
            right: 24px !important;
            width: 44px !important;
            height: 44px !important;
            z-index: 999 !important;
        }

        .stApp button[key="weight_lightning_btn"] {
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            border-radius: 50% !important;
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
            font-size: 18px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }

        .stApp button[key="weight_lightning_btn"]:hover {
            transform: scale(1.08) !important;
            background-color: #f3f3f3 !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.1) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    latest_weight = sheets.get_latest_weight(uid)
    weight_display_str = f"{latest_weight:.1f}" if latest_weight else "--.-"
    
    # 歷史紀錄與變動計算
    weight_history = []
    if "records" in dir() and records:
        for r in records:
            w = r.get("weight") if isinstance(r, dict) else getattr(r, "weight", None)
            if w is not None:
                try:
                    w_val = float(w)
                    if w_val > 0:
                        weight_history.append(w_val)
                except (ValueError, TypeError):
                    continue

    # 計算趨勢
    trend_content = ""
    if latest_weight and len(weight_history) >= 2:
        prev_weight = weight_history[-2]
        diff = latest_weight - prev_weight
        diff_pct = (diff / prev_weight) * 100
        
        if diff < 0:
            trend_content = f"⇩ {abs(diff):.1f} Kg ({diff_pct:.1f}%)"
        elif diff > 0:
            trend_content = f"⇧ {abs(diff):.1f} Kg (+{diff_pct:.1f}%)"
        else:
            trend_content = "⬌ 體重維持持平"
    else:
        trend_content = ""

    st.markdown('<div class="weight-card-container">', unsafe_allow_html=True)

    card_html = f"""
    <div class="weight-card">
        <div class="weight-title">Current Weight</div>
        <div class="weight-value">
            {weight_display_str}<span class="weight-unit">Kg</span>
        </div>"""
    
    if trend_content:
        card_html += f"""
        <div class="weight-trend">
            {trend_content}
        </div>"""
    
    card_html += """
    </div>"""
    
    st.markdown(card_html, unsafe_allow_html=True)

    if st.button("⚡", key="weight_lightning_btn"):
        st.session_state.page = "體重記錄"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.write("<div style='height: 40px;'></div>", unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)




# =============================================================================

# 學員端：體重記錄

# =============================================================================

def page_weight() -> None:

    st.header("⚖️ 體重記錄")

    uid = st.session_state.user_id

    with st.form("weight_form"):

        col1, col2 = st.columns([2, 1])

        with col1:

            weight = st.number_input("今日體重 (kg)", value=60.0, step=0.1, min_value=30.0, max_value=300.0)

        with col2:

            st.write("")

            submitted = st.form_submit_button("儲存", use_container_width=True)

        if submitted:

            try:

                sheets.append_weight(timestamp=datetime.now().strftime("%Y-%m-%d"), user_id=uid, weight_kg=weight)

                st.success("體重已記錄！")

                st.rerun()

            except Exception as exc:

                st.error("儲存失敗: " + str(exc))

    st.divider()

    st.subheader("今日完成率")

    weight_records = sheets.get_weight_records(uid)

    if weight_records:

        weight_data = {"日期": [], "體重 (kg)": []}

        for r in weight_records[-30:]:

            weight_data["日期"].append(r.get("timestamp", "")[:10])

            weight_data["體重 (kg)"].append(r.get("weight_kg", 0))

        st.line_chart(weight_data, x="日期", y="體重 (kg)")

        if len(weight_data["體重 (kg)"]) >= 2:

            weights = weight_data["體重 (kg)"]

            change = weights[-1] - weights[0]

            st.caption(f"起始：{weights[0]:.1f}kg → 目前：{weights[-1]:.1f}kg（{change:+.1f}kg）")

    else:

        st.info("尚無體重記錄")

# =============================================================================

# 學員端：訓練記錄

# =============================================================================

def page_training() -> None:

    st.header("🏋️ 訓練記錄")

    uid = st.session_state.user_id

    today = date.today()

    today_str = today.isoformat()

    today_training = sheets.get_training_by_date(uid, today)

    with st.form("training_form"):

        st.subheader(f"📅 {today.strftime('%Y/%m/%d')} 訓練項目")

        cols = st.columns(len(TRAINING_TYPES))

        training_values = {}

        for idx, t_type in enumerate(TRAINING_TYPES):

            with cols[idx]:

                emoji = TRAINING_EMOJI.get(t_type, "")

                default = today_training.get(t_type.lower(), 0) if today_training else 0

                checked = st.checkbox(f"{emoji} {t_type}", value=bool(default))

                training_values[t_type.lower()] = 1 if checked else 0

        submitted = st.form_submit_button("儲存訓練記錄", use_container_width=True)

    if submitted:

        try:

            sheets.update_training(

                timestamp=today_str, user_id=uid,

                training_back=training_values.get("背", 0),

                training_chest=training_values.get("胸", 0),

                training_legs=training_values.get("腿", 0),

                training_core=training_values.get("核心", 0),

                training_cardio=training_values.get("有氧", 0),

            )

            st.success("訓練記錄已儲存！")

            st.rerun()

        except Exception as exc:

            st.error("儲存失敗: " + str(exc))

    st.divider()

    st.subheader("今日完成率")

    ws, we = _week_range()

    training_data = []

    for i in range((we - ws).days + 1):

        d = ws + timedelta(days=i)

        training = sheets.get_training_by_date(uid, d)

        if training and any(v == 1 for v in training.values()):

            items = [TRAINING_EMOJI.get(t, "") + t for t, v in training.items() if v == 1]

            training_data.append({"日期": d.strftime("%m/%d"), "訓練項目": " ".join(items)})

    if training_data:

        st.dataframe(training_data, use_container_width=True, hide_index=True)

    else:

        st.info("本週尚無訓練記錄")

# =============================================================================

# 學員端：記錄飲食

# =============================================================================

def page_log_meal() -> None:

    st.header("🍽️ 記錄飲食")

    uid = st.session_state.user_id

    record_mode = sheets.get_user_record_mode(uid)

    meal_type = st.selectbox("餐點類型", MEAL_TYPES)

    st.subheader("今日完成率")

    input_mode = st.radio(

        "輸入模式",

        ["📝 文字輸入", "📷 拍照上傳", "📁 圖片上傳"],

        horizontal=True,

        label_visibility="collapsed",

    )

    analysis_result = None

    if input_mode == "📝 文字輸入":

        with st.form("text_input_form"):

            food_text = st.text_area("輸入食物內容", placeholder="例如：雞腿便當 + 滷蛋 + 無糖豆漿", height=100)

            submitted = st.form_submit_button("分析食物", use_container_width=True)

        if submitted and food_text:

            with st.spinner("AI 分析中..."):

                try:

                    analysis_result = gemini.analyze_text(food_text)

                except Exception as exc:

                    st.error("分析失敗: " + str(exc))

    elif input_mode == "📷 拍照上傳":

        camera_file = st.camera_input("拍攝食物照片")

        if camera_file:

            with st.spinner("AI 分析中..."):

                try:

                    analysis_result = gemini.analyze_image(Image.open(camera_file))

                except Exception as exc:

                    st.error("分析失敗: " + str(exc))

    else:

        uploaded_file = st.file_uploader("上傳食物照片", type=["jpg", "jpeg", "png"])

        if uploaded_file:

            with st.spinner("AI 分析中..."):

                try:

                    analysis_result = gemini.analyze_image(Image.open(uploaded_file))

                except Exception as exc:

                    st.error("分析失敗: " + str(exc))

    # 將 analysis_result 存入 session_state，確保按鈕點擊後還能取用
    if analysis_result:
        st.session_state.pending_analysis = analysis_result

    if st.session_state.get("pending_analysis"):
        analysis_result = st.session_state.pending_analysis

        st.divider()

        st.subheader("今日完成率")

        cal = analysis_result.get("calories", 0)

        pro = analysis_result.get("protein", 0)

        carb = analysis_result.get("carb", 0)

        fat = analysis_result.get("fat", 0)

        if record_mode == "full":

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric("熱量", f"{cal:.0f} kcal")

            with col2:

                st.metric("蛋白質", f"{pro:.0f} g")

            with col3:

                st.metric("碳水", f"{carb:.0f} g")

            with col4:

                st.metric("脂肪", f"{fat:.0f} g")

        else:

            col1, col2 = st.columns(2)

            with col1:

                st.metric("熱量", f"{cal:.0f} kcal")

            with col2:

                st.metric("蛋白質", f"{pro:.0f} g")

        portion = st.slider("份量", 0.5, 3.0, 1.0, 0.1)

        if portion != 1.0:

            st.caption(f"× {portion} 份")

        water_ml = st.number_input("飲水量 (ml)", value=0, step=50, min_value=0)

        if st.button("✅ 存入今日記錄", use_container_width=True):


            try:
                sheets.append_record(

                    timestamp=datetime.now().isoformat(),

                    user_id=uid,

                    meal_type=meal_type,

                    food_summary=analysis_result.get("food_summary", ""),

                    calories=cal * portion,

                    protein=pro * portion,

                    carb=carb * portion if record_mode == "full" else 0,

                    fat=fat * portion if record_mode == "full" else 0,

                    water_ml=water_ml,

                    image_url="",

                    portion=portion,

                )

                _clear_analysis_cache()

                # 清除 pending_analysis，讓錊單回到初始狀態
                st.session_state.pending_analysis = None

                # 顯示短暫的成功標記
                st.success("已存入！")

                st.rerun()

            except Exception as exc:

                st.error("儲存失敗: " + str(exc))

# =============================================================================

# 學員端：歷史記錄

# =============================================================================

def page_history() -> None:

    st.header("📜 歷史記錄")

    uid = st.session_state.user_id

    try:

        records = _fetch_records_cached(uid)

        goals = _fetch_goals_cached(uid)

    except Exception as exc:

        st.error("取得記錄失敗: " + str(exc))

        return

    bmr = goals.get("bmr", 0)

    calorie_goal = goals.get("calorie", 0)

    if bmr <= 0 or calorie_goal <= 0:

        st.warning("你尚未設定營養目標")

        return

    ws, we = _week_range()

    days = (we - ws).days + 1

    st.subheader("今日完成率")

    daily_data = []

    for i in range(days):

        d = ws + timedelta(days=i)

        day_recs = metrics.filter_records(records, d, d)

        day_totals = metrics.sum_totals(day_recs).as_dict()

        day_cal = float(day_totals.get("calories", 0.0))

        day_pro = float(day_totals.get("protein", 0.0))

        cal_ratio = (day_cal / calorie_goal) if calorie_goal > 0 else 0.0

        pro_ratio = (day_pro / goals.get("protein", 1)) if goals.get("protein", 0) > 0 else 0.0

        date_str = d.strftime("%m/%d")

        weekday = ["一", "二", "三", "四", "五", "六", "日"][d.weekday()]

        daily_data.append({

            "日期": f"{date_str}({weekday})",

            "熱量": f"{day_cal:.0f}",

            "熱量目標": f"{calorie_goal:.0f}",

            "熱量%": f"{cal_ratio:.0%}",

            "蛋白質": f"{day_pro:.0f}g",

            "蛋白質%": f"{pro_ratio:.0%}",

        })

    st.dataframe(daily_data, use_container_width=True, hide_index=True)

    st.subheader("今日完成率")

    calorie_chart = {"日期": [], "達成率(%)": []}

    for i in range(days):

        d = ws + timedelta(days=i)

        day_recs = metrics.filter_records(records, d, d)

        day_totals = metrics.sum_totals(day_recs).as_dict()

        day_cal = float(day_totals.get("calories", 0.0))

        cal_ratio = (day_cal / calorie_goal * 100) if calorie_goal > 0 else 0.0

        calorie_chart["日期"].append(d.strftime("%m/%d"))

        calorie_chart["達成率(%)"].append(min(cal_ratio, 100))

    st.bar_chart(calorie_chart, x="日期", y="達成率(%)")

# =============================================================================

# 學員端：TDEE 頁面

# =============================================================================

def page_tdee() -> None:

    st.header("🧮 TDEE 計算機")

    uid = st.session_state.user_id

    goals = sheets.get_user_goals(uid)

    bmr = goals.get("bmr", 0)

    calorie_goal = goals.get("calorie", 0)

    if bmr > 0:

        col1, col2 = st.columns(2)

        with col1:

            st.metric("基礎代謝率 (BMR)", f"{bmr:.0f} 大卡")

        with col2:

            st.metric("每日建議攝取", f"{calorie_goal:.0f} 大卡")

        st.info("以上為你目前設定的目標，可由教練調整")

    else:

        st.warning("你尚未設定營養目標")

        if st.button("前往 TDEE 問卷"):

            st.session_state.page = "TDEE 問卷"

            st.rerun()

# =============================================================================

# 主程式

# =============================================================================

def main() -> None:

    st.set_page_config(page_title="飲食控制管理系統", layout="wide")

    st.markdown("""

    <style>

        @import url('https://fonts.googleapis.com/css2?family=Line+Seed+JP:wght@400&display=swap');

        .stApp {

            background-color: #FFFFFF !important;

            color: #2F3E46 !important;

            font-family: 'Line Seed JP', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;

        }

        h1, h2, h3, h4, h5, h6 {

            color: #2F3E46 !important;

            font-weight: 400 !important;

        }

        div[data-testid="stMetric"] {

            background-color: #FFFFFF !important;

            padding: 20px 24px !important;

            border-radius: 16px !important;

            box-shadow: 0 8px 24px rgba(149, 157, 165, 0.06) !important;

        }

        div[data-testid="stMetric"] label {

            color: #666 !important;

        }

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {

            color: #2F3E46 !important;

        }

        div[data-testid="stSidebar"] {

            background-color: #F8F9FA !important;

        }

        div.stButton > button {

            background-color: #4A7C59 !important;

            color: #FFFFFF !important;

            border-radius: 12px !important;

            border: none !important;

            padding: 0.5rem 1rem !important;

        }

        div.stButton > button:hover {

            background-color: #385E43 !important;

        }

        div[data-testid="stFormSubmitButton"] button {

            background-color: #4A7C59 !important;

            color: #FFFFFF !important;

            border-radius: 12px !important;

            border: none !important;

            padding: 0.6rem 2rem !important;

        }

        div[data-testid="stFormSubmitButton"] button:hover {

            background-color: #385E43 !important;

        }

        div[data-testid="stTabs"] button[aria-selected="true"] {

            background-color: #4A7C59 !important;

            color: #FFFFFF !important;

        }

        body, .stApp, .stApp > div, .main, .main > div,

        .block-container, section.main > div,

        [data-testid="stSidebar"], [data-testid="stSidebarContent"],

        div[data-testid="stVerticalBlock"], div[data-testid="stHorizontalBlock"],

        .stTabs, div[data-testid="stTabContent"],

        .stForm, [data-testid="stFormSubmitButton"] {

            background-color: #FFFFFF !important;

        }

        [data-testid="stTabsContent"] {

            background-color: #FFFFFF !important;

        }

        .stTabs * {

            background-color: #FFFFFF !important;

        }

        div[data-testid="stProgressBar"] > div > div {

            background-color: #4A7C59 !important;

        }

        /* ===== Mobile Responsive (手機響應式) ===== */
        @media (max-width: 768px) {
            /* 調整區塊標題大小 */
            h1 { font-size: 1.4rem !important; }
            h2 { font-size: 1.2rem !important; }
            h3 { font-size: 1rem !important; }

            /* Metric 卡片在手機上更好看 */
            div[data-testid="stMetric"] {
                margin-bottom: 8px !important;
                padding: 12px !important;
                border-radius: 12px !important;
            }

            /* 側邊欄調整 */
            [data-testid="stSidebar"] {
                width: 200px !important;
                min-width: 200px !important;
            }

            /* 讓所有 columns 在手機上自動換行 */
            .stColumns > div {
                flex-wrap: wrap !important;
            }

            /* 4欄 -> 2x2 在手機上 */
            div.stHorizontalBlock:has(> div:nth-child(4)) {
                flex-wrap: wrap !important;
            }
            div.stHorizontalBlock:has(> div:nth-child(4)) > div {
                min-width: 48% !important;
                flex: 0 0 48% !important;
            }

            /* 5欄 -> 3+2 或全部堆疊 */
            div.stHorizontalBlock:has(> div:nth-child(5)) {
                flex-wrap: wrap !important;
            }
            div.stHorizontalBlock:has(> div:nth-child(5)) > div {
                min-width: 48% !important;
                flex: 0 0 48% !important;
            }

            /* 按鈕全寬 */
            div.stButton > button,
            div[data-testid="stFormSubmitButton"] button {
                width: 100% !important;
                padding: 0.5rem 1rem !important;
                font-size: 0.9rem !important;
            }

            /* 表單輸入框全寬 */
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                width: 100% !important;
            }

            /* 資料表可橫向滾動 */
            .dataframe {
                overflow-x: auto !important;
                display: block !important;
            }

            /* Tabs 在手機上可橫向滾動 */
            div[data-testid="stTabs"] {
                overflow-x: auto !important;
                white-space: nowrap !important;
            }

            /* 進度條調整 */
            div[data-testid="stProgressBar"] {
                height: 8px !important;
            }

            /* 下載按鈕在手機上全寬 */
            .stDownloadButton > button {
                width: 100% !important;
            }

            /* Expander 在手機上全寬 */
            .streamlit-expanderHeader {
                font-size: 0.9rem !important;
            }
        }

        /* 超小手機 (320px - 400px) */
        @media (max-width: 400px) {
            h1 { font-size: 1.2rem !important; }
            h2 { font-size: 1.1rem !important; }
            h3 { font-size: 0.95rem !important; }

            div[data-testid="stMetric"] {
                padding: 10px !important;
            }

            /* 4欄直接變成2欄 */
            div.stHorizontalBlock:has(> div:nth-child(4)) > div {
                min-width: 100% !important;
                flex: 0 0 100% !important;
            }

            /* 5欄也變成2欄 */
            div.stHorizontalBlock:has(> div:nth-child(5)) > div {
                min-width: 100% !important;
                flex: 0 0 100% !important;
            }
        }


        /* ===== Dashboard Styles (教練端) ===== */
        
        /* 狀態指示燈 */
        .status-green { color: #22C55E; }
        .status-yellow { color: #EAB308; }
        .status-red { color: #DC2626; }
        
        /* 學員卡片容器 */
        .student-card {
            background: #FFFFFF;
            border-radius: 16px;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid #E5E7EB;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        
        /* 進度條優化 */
        div[data-testid="stProgressBar"] {
            height: 12px !important;
            border-radius: 6px !important;
            background-color: #E5E7EB !important;
        }
        
        div[data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #22C55E, #10B981) !important;
            border-radius: 6px !important;
        }
        
        /* 警示進度條 */
        .progress-warning > div > div {
            background: linear-gradient(90deg, #EAB308, #F59E0B) !important;
        }
        
        .progress-danger > div > div {
            background: linear-gradient(90deg, #DC2626, #EF4444) !important;
        }
        
        /* 數據卡片 */
        .metric-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #E5E7EB;
            text-align: center;
        }
        
        /* 即時更新指示 */
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background-color: #22C55E;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
            100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
        }
        
        /* 按鍵樣式優化 */
        div.stButton > button {
            background-color: #3B82F6 !important;
            border-radius: 8px !important;
        }
        
        div.stButton > button:hover {
            background-color: #2563EB !important;
        }


        /* ========================================== */
        /* ========================================== */
        /* 底部導航 - 簡化版（按鈕在 layout 流中） */
        /* ========================================== */

        /* 按鈕樣式 - 48x48 圓形白色按鈕 */
        button[data-testid="baseButton-nav_status"],
        button[data-testid="baseButton-nav_history"] {
            width: 48px !important;
            height: 48px !important;
            border-radius: 50% !important;
            padding: 0 !important;
            min-width: 0 !important;
            font-size: 20px !important;
            background: #ffffff !important;
            color: #9CA3AF !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
            transition: all 0.2s ease !important;
        }

        /* Hover 效果 */
        button[data-testid="baseButton-nav_status"]:hover,
        button[data-testid="baseButton-nav_history"]:hover {
            transform: scale(1.05) !important;
        }


        /* 內容不被導航列遮住 */
        .main .block-container {
            padding-bottom: 120px !important;
        }


    
        
        /* ============================================================
           強制限制登入表單（st.form）寬度並使其水平置中
           ============================================================ */
        div[data-testid="stForm"] {
            max-width: 400px !important;              /* 限制最大寬度，防止橫向拉長 */
            width: 100% !important;
            margin: 40px auto !important;            /* 頂部外距 40px，auto 達成水平置中 */
            background: #ffffff !important;          /* 純白卡片背景 */
            border-radius: 32px !important;          /* 大圓角 */
            padding: 30px !important;                 /* 內部留白 */
            border: 1px solid #E5E7EB !important;     /* 柔和細邊框 */
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important; /* 懸浮感陰影 */
            box-sizing: border-box !important;
        }

        /* 確保 Form 內部的元素不會溢出 */
        div[data-testid="stForm"] > div {
            width: 100% !important;
            box-sizing: border-box !important;
        }



    </style>

    """, unsafe_allow_html=True)

    init_session()

    if not st.session_state.user_id:

        page_login()

        return

    role = st.session_state.get("role", "student")

    is_coach = (role == "coach")

    coach_pages = ["學員狀態", "學員歷史"]

    student_pages = ["個人", "記錄飲食", "歷史", "體重記錄", "訓練記錄", "TDEE", "TDEE 問卷"]

    if is_coach:
        _available_pages = list(coach_pages) + ["學員資料"]
    else:
        _available_pages = list(student_pages)

    if st.session_state.page not in _available_pages:
        st.session_state.page = "學員狀態" if is_coach else "個人"

    # ----- 暫時定義 page 以維持向下相容 -----
    # ----- 路由：直接使用 st.session_state.page（Stage 2-6 簡化） -----


    if is_coach:

        if st.session_state.page == "學員狀態":

            page_coach_overview()

        elif st.session_state.page == "學員資料":

            page_coach_student_detail()

        elif st.session_state.page == "學員歷史":
            page_coach_student_history()
    else:

        if st.session_state.page not in ["TDEE 問卷", "個人"]:

            goals_check = sheets.get_user_goals(st.session_state.user_id)

            if goals_check.get("bmr", 0) <= 0 or goals_check.get("calorie", 0) <= 0:

                st.warning("請先設定營養目標")

                if st.button("前往 TDEE 問卷"):

                    st.session_state.page = "TDEE 問卷"

                    st.rerun()

                return

        if st.session_state.page == "個人":

            page_personal()

        elif st.session_state.page == "記錄飲食":

            page_log_meal()

        elif st.session_state.page == "歷史":

            page_history()

        elif st.session_state.page == "體重記錄":

            page_weight()

        elif st.session_state.page == "訓練記錄":

            page_training()

        elif st.session_state.page == "TDEE":

            page_tdee()

        elif st.session_state.page == "TDEE 問卷":

            page_tdee_questionnaire()




    # ==========================================
    # 底部導航 - 角色自適應版（教練 2 顆、學員 7 顆）
    # ==========================================
    if is_coach:
        _nav_items = [
            ("學員狀態", "👤"),
            ("學員歷史", "📅"),
        ]
        _pad_l, _nav_outer, _pad_r = st.columns([3, 1, 3])
    else:
        _nav_items = [
            ("個人", "👤"),
            ("記錄飲食", "🍴"),
            ("歷史", "🕐"),
            ("體重記錄", "⚖️"),
            ("訓練記錄", "🏋️"),
            ("TDEE", "📊"),
            ("TDEE 問卷", "📋"),
        ]
        _pad_l, _nav_outer, _pad_r = st.columns([1, 7, 1])

    with _nav_outer:
        _btn_cols = st.columns(len(_nav_items))
        for _i, (_page_name, _emoji) in enumerate(_nav_items):
            with _btn_cols[_i]:
                if st.button(_emoji, key=f"nav_{_page_name}", help=_page_name):
                    st.session_state.page = _page_name
                    st.rerun()


    # ==========================================
if __name__ == "__main__":

    main()


