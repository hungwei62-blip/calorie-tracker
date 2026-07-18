"""教練端頁面。"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from io import BytesIO
import html
import io as _io
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as _plt
from matplotlib.backends.backend_pdf import PdfPages as _PdfPages
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from services import metrics, sheets
from domain.history import aggregate_daily as _history_aggregate_daily
from domain.history import parse_record_date as _parse_record_date
from pages.common import _clear_analysis_cache, get_default_avatar_source


COACH_NUTRIENT_SPECS = (
    ("卡路里", "calories", "calorie", "kcal", "#ff6068"),
    ("水", "water", "water", "ml", "#90cbfb"),
    ("蛋白質", "protein", "protein", "g", "#bbf250"),
)


def _non_negative_number(value: object) -> float:
    """Return a finite non-negative number for progress rendering."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) and number > 0 else 0.0


def calculate_coach_nutrient_progress(
    actual: object, goal: object
) -> tuple[float, float, float]:
    """Normalize a nutrient pair and clamp its visual progress to 0-100%."""
    actual_value = _non_negative_number(actual)
    goal_value = _non_negative_number(goal)
    percentage = min(actual_value / goal_value * 100, 100) if goal_value else 0.0
    return actual_value, goal_value, percentage


def _format_nutrient_value(value: float) -> str:
    return str(int(round(value)))


def build_coach_nutrient_progress_html(
    label: str,
    actual: object,
    goal: object,
    unit: str,
    color: str,
) -> str:
    """Build one compact, accessible horizontal nutrient progress indicator."""
    actual_value, goal_value, percentage = calculate_coach_nutrient_progress(
        actual, goal
    )
    actual_text = _format_nutrient_value(actual_value)
    goal_text = _format_nutrient_value(goal_value) if goal_value else "—"
    safe_label = html.escape(label)
    safe_unit = html.escape(unit)
    safe_color = html.escape(color, quote=True)
    value_text = f"{actual_text} / {goal_text} {safe_unit}"

    return (
        '<div class="coach-nutrient">'
        f'<span class="coach-nutrient-label">{safe_label}</span>'
        '<div class="coach-nutrient-track" role="progressbar" '
        f'aria-label="{safe_label}" aria-valuemin="0" aria-valuemax="100" '
        f'aria-valuenow="{percentage:.0f}">'
        f'<span style="width:{percentage:.2f}%;background:{safe_color}"></span>'
        "</div>"
        f'<span class="coach-nutrient-value">{value_text}</span>'
        "</div>"
    )


def build_coach_student_card_html(
    name: object,
    has_training: bool,
    totals: dict[str, object],
    goals: dict[str, object],
) -> str:
    """Build a student status card with three single-row nutrient indicators."""
    display_name = str(name or "Unknown")
    safe_name = html.escape(display_name)
    safe_initial = html.escape(display_name[0] if display_name else "?")
    training_class = "" if has_training else " not-done"
    training_html = (
        '<i class="fas fa-check"></i> Trained'
        if has_training
        else '<i class="fas fa-times"></i> Not trained'
    )
    nutrients_html = "".join(
        build_coach_nutrient_progress_html(
            label,
            totals.get(actual_key, 0),
            goals.get(goal_key, 0),
            unit,
            color,
        )
        for label, actual_key, goal_key, unit, color in COACH_NUTRIENT_SPECS
    )

    return (
        '<div class="member-card">'
        '<div class="member-top-row">'
        f'<div class="member-avatar">{safe_initial}</div>'
        f'<div class="member-name">{safe_name}</div>'
        f'<div class="training-badge{training_class}">{training_html}</div>'
        "</div>"
        f'<div class="coach-nutrient-grid">{nutrients_html}</div>'
        "</div>"
    )


def build_coach_welcome_html(display_name: object, avatar_source: str) -> str:
    """Build the coach greeting with the same avatar treatment as students."""
    safe_name = html.escape(str(display_name or "Coach"))
    safe_avatar = html.escape(avatar_source, quote=True)
    return (
        '<div class="coach-home-welcome" style="display:flex;align-items:center;'
        'gap:16px;margin-top:0;margin-bottom:25px;width:100%;">'
        f'<img src="{safe_avatar}" alt="avatar" style="width:56px;height:56px;'
        'border-radius:50%;object-fit:cover;box-shadow:0 4px 12px rgba(0,0,0,0.05);">'
        f'<span style="font-size:24px;font-weight:400;color:#1F2937;'
        'font-family:system-ui,-apple-system,sans-serif;white-space:nowrap;">'
        f'Hello ! {safe_name}</span></div>'
    )


def page_coach_overview() -> None:
    st.markdown("""<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
    .member-card { display: flex; flex-direction: column; gap: 16px; padding: 16px; background: #fff; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; }
    .member-top-row { display: flex; align-items: center; gap: 12px; }
    .member-avatar { width: 48px; height: 48px; border-radius: 50%; background: #BBE8EE; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
    .member-name { font-size: 18px; font-weight: 500; color: #1F2937; }
    .member-avatar { width: 56px; height: 56px; border-radius: 50%; background: #BBE8EE; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-right: 20px; flex-shrink: 0; }
            .member-name { font-size: 18px; font-weight: 400; color: #1F2937; }
    .training-badge { background: #DCFCE7; color: #16A34A; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 4px; }
    .training-badge.not-done { background: #F3F4F6; color: #9CA3AF; }
    .coach-nutrient-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; width: 100%; padding: 4px 0 2px; }
    .coach-nutrient { min-width: 0; display: flex; flex-direction: column; gap: 7px; }
    .coach-nutrient-label { overflow: hidden; color: #4B5563; font-size: 12px; font-weight: 500; line-height: 1.2; text-overflow: ellipsis; white-space: nowrap; }
    .coach-nutrient-track { width: 100%; height: 5px; overflow: hidden; border-radius: 999px; background: #E9ECEF; }
    .coach-nutrient-track > span { display: block; height: 100%; border-radius: inherit; }
    .coach-nutrient-value { display: block; width: 100%; overflow: hidden; color: #9CA3AF; font-size: 15px; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; line-height: 1.2; text-align: center; text-overflow: ellipsis; white-space: nowrap; }
    @media (max-width: 480px) {
        .member-card { gap: 12px; padding: 14px 12px; }
        .member-avatar { width: 48px; height: 48px; margin-right: 8px; font-size: 19px; }
        .member-name { min-width: 0; overflow: hidden; font-size: 16px; text-overflow: ellipsis; white-space: nowrap; }
        .training-badge { margin-left: auto; padding: 4px 7px; font-size: 10px; white-space: nowrap; }
        .coach-nutrient-grid { gap: 6px; }
        .coach-nutrient { gap: 6px; }
        .coach-nutrient-label { font-size: 11px; }
        .coach-nutrient-value { font-size: 13px; }
    }
    </style>""", unsafe_allow_html=True)

    coach_name = str(st.session_state.username or "Coach")
    avatar_source = get_default_avatar_source()
    with st.container(key="coach_overview_header"):
        st.markdown(
            build_coach_welcome_html(coach_name, avatar_source),
            unsafe_allow_html=True,
        )
        st.header("本日學員狀態")

    try:
        students = sheets.get_students_for_manager(st.session_state.user_id)
        all_records = sheets.get_records()
        all_trainings = sheets.get_training_records()
    except Exception as exc:
        st.error("Failed to get students: " + str(exc))
        return

    if not students:
        st.info("No students yet.")
        return

    today = date.today()
    today_prefix = today.isoformat()
    records_by_student = {}
    training_by_student = {}
    for record in all_records:
        if str(record.get("timestamp", ""))[:10] == today_prefix:
            records_by_student.setdefault(record.get("user_id", ""), []).append(record)
    for training in all_trainings:
        if str(training.get("timestamp", ""))[:10] == today_prefix:
            training_by_student[training.get("user_id", "")] = training
    for student in students:
        uid = student.get("user_id", "")
        name = student.get("name") or student.get("username") or "Unknown"
        goals = sheets.get_user_goals(uid)
        today_records = records_by_student.get(uid, [])
        totals = metrics.sum_totals(today_records).as_dict()
        training_today = training_by_student.get(uid)
        has_training = bool(training_today) and bool(training_today.get("training_types"))

        card_html = build_coach_student_card_html(
            name, has_training, totals, goals
        )
        st.markdown(card_html, unsafe_allow_html=True)
def page_coach_student_detail() -> None:

    uid = st.session_state.get("view_student_id")

    if not uid:

        st.error("未指定學員")

        return

    student = sheets.get_student_for_manager(uid, st.session_state.user_id)

    if not student:

        st.error("沒有權限查看此學員")
        st.session_state.page = "學員狀態"
        st.session_state.pop("view_student_id", None)
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
    st.subheader("匯入 Excel")

    uploaded_file = st.file_uploader(
        "選擇 Excel 檔案（每個工作表代表一個月份）",
        type=["xlsx"],
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

                if st.button("確認匯入", type="primary", width="stretch"):
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

    st.subheader("今日摘要")

    col1, col2 = st.columns(2)

    with col1:

        cal = totals.get("calories", 0)

        st.metric("熱量", f"{cal:.0f}", f"{goals.get('calorie', 0) - cal:.0f}")

    with col2:

        weight = sheets.get_latest_weight(uid)

        st.metric("體重", f"{weight:.1f}kg" if weight else "-", delta=None)

    st.divider()

    st.subheader("營養目標")

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

    st.subheader("體重趨勢")

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
            training_by_day[d] = sheets.format_training_record(r)
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
                detail = sheets.format_training_record(r)
                text_lines.append("  " + r.get("timestamp", "")[:10] + "  " + (detail or "-"))
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
            students = sheets.get_students_for_manager(st.session_state.user_id)
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

    student = sheets.get_student_for_manager(uid, st.session_state.user_id)
    if not student:
        st.error("沒有權限查看此學員，請返回總覽重新選擇。")
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
    st.subheader("匯入 Excel")

    # ============================================================
    # Excel 匯入功能
    # ============================================================
    with st.expander("📥 匯入 Excel 資料"):
        uploaded_file = st.file_uploader(
            "選擇 Excel 檔案（每個工作表代表一個月份）",
            type=["xlsx"],
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

                    if st.button("確認匯入", type="primary", width="stretch"):
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
    st.subheader("區間摘要")
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

        st.plotly_chart(fig_weight, width="stretch", config={'displayModeBar': False})
    else:
        st.info("此區間沒有體重記錄。")



    # 統一的高質感深夜底色
    st.subheader("每日攝取趨勢")

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

        st.plotly_chart(fig_cal, width="stretch", config={'displayModeBar': False})

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

        st.plotly_chart(fig_pro, width="stretch", config={'displayModeBar': False})

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

        st.plotly_chart(fig_water, width="stretch", config={'displayModeBar': False})


    else:
        st.info("此區間沒有飲食記錄。")


    st.subheader("訓練記錄")
    if trainings:
        rows = []
        for r in sorted(trainings, key=lambda x: x.get("timestamp", "")):
            rows.append({
                "日期": r.get("timestamp", "")[:10],
                "訓練內容": sheets.format_training_record(r) or "無",
            })
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("此區間沒有訓練記錄。")


    st.subheader("匯出資料")
    csv_bytes = _build_history_csv(student, daily, weights, trainings, notes, start_date, end_date)
    pdf_bytes = _build_history_pdf(student, daily, weights, trainings, notes, start_date, end_date)
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "下載 CSV",
            data=csv_bytes,
            file_name=str(name) + "_歷史_" + start_date.isoformat() + "_" + end_date.isoformat() + ".csv",
            mime="text/csv",
            width="stretch",
            key="dl_csv",
        )
    with ec2:
        st.download_button(
            "下載 PDF",
            data=pdf_bytes,
            file_name=str(name) + "_歷史_" + start_date.isoformat() + "_" + end_date.isoformat() + ".pdf",
            mime="application/pdf",
            width="stretch",
            key="dl_pdf",
        )


# =============================================================================

# END_HISTORY_BLOCK

# =============================================================================
