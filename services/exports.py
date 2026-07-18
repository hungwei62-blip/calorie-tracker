"""Safe report export builders independent from Streamlit pages."""

from __future__ import annotations

import csv
import io
from typing import Any

from domain.validation import safe_csv_cell
from services import sheets


def build_history_csv(
    student: dict[str, Any],
    daily: dict,
    weights: list[dict[str, Any]],
    trainings: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    start_date,
    end_date,
) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    def write_row(values) -> None:
        writer.writerow([safe_csv_cell(value) for value in values])

    name = student.get("name", student.get("username", "未知"))
    write_row(["學員：" + str(name)])
    write_row(["區間：" + start_date.isoformat() + " ~ " + end_date.isoformat()])
    write_row([])
    write_row(
        [
            "日期", "熱量 (kcal)", "蛋白質 (g)", "醣類 (g)",
            "脂質 (g)", "水量 (ml)", "體重 (kg)", "訓練項目",
        ]
    )
    weight_by_day = {
        str(row.get("timestamp", ""))[:10]: row.get("weight_kg", "")
        for row in weights
        if str(row.get("timestamp", ""))[:10]
    }
    training_by_day = {
        str(row.get("timestamp", ""))[:10]: sheets.format_training_record(row)
        for row in trainings
        if str(row.get("timestamp", ""))[:10]
    }
    for day in sorted(daily):
        values = daily[day]
        day_key = day.isoformat()
        weight = weight_by_day.get(day_key, "")
        weight_text = f"{weight:.1f}" if isinstance(weight, (int, float)) else weight
        write_row(
            [
                day_key,
                f"{values['calorie']:.0f}",
                f"{values['protein']:.0f}",
                f"{values['carb']:.0f}",
                f"{values['fat']:.0f}",
                f"{values['water']:.0f}",
                weight_text,
                training_by_day.get(day_key, ""),
            ]
        )
    if notes:
        write_row([])
        write_row(["教練備註"])
        write_row(["時間", "教練", "內容"])
        for note in notes:
            write_row(
                [
                    str(note.get("timestamp", ""))[:19],
                    note.get("coach_id", ""),
                    str(note.get("note", "")).replace("\n", " "),
                ]
            )
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")

