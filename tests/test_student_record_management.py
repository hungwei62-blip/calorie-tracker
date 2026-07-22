from __future__ import annotations

import inspect

import pytest

from pages.student import history_records
from services import application, sheets
from services.security import AuthContext


class Worksheet:
    def __init__(self, values):
        self.values = [list(row) for row in values]
        self.updated = []
        self.deleted = []
        self.append_kwargs = []

    def row_values(self, row):
        return list(self.values[row - 1])

    def get_all_values(self):
        return [list(row) for row in self.values]

    def update_cell(self, row, col, value):
        self.updated.append((row, col, value))

    def update_cells(self, cells, **_kwargs):
        self.updated.extend((cell.row, cell.col, cell.value) for cell in cells)

    def delete_rows(self, row):
        self.deleted.append(row)

    def append_row(self, row, **kwargs):
        self.values.append(list(row))
        self.append_kwargs.append(kwargs)


def test_record_crud_uses_record_id_and_user_id(monkeypatch):
    worksheet = Worksheet([
        sheets.RECORDS_HEADERS,
        ["2026-07-20T08:00:00+08:00", "u1", "食物", "早餐", 500, 30, 0, 0, 0, "", 1, "rec_1"],
    ])
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: worksheet)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    assert sheets.update_record_by_id("rec_1", "u1", {"calories": 450}) is True
    assert worksheet.updated == [(2, sheets.RECORDS_HEADERS.index("calories") + 1, 450.0)]
    assert sheets.update_record_by_id("rec_1", "other", {"calories": 1}) is False
    assert sheets.delete_record_by_id("rec_1", "other") is False
    assert sheets.delete_record_by_id("rec_1", "u1") is True
    assert worksheet.deleted == [2]


def test_new_record_receives_stable_id_after_schema_migration(monkeypatch):
    worksheet = Worksheet([sheets.RECORDS_HEADERS])
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: worksheet)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    record_id = sheets.append_record(
        "2026-07-20T08:00:00+08:00", "u1", "食物", "早餐",
        500, 30, 0, 0, 0, "", 1,
    )

    assert record_id.startswith("rec_")
    assert worksheet.values[-1][-1] == record_id


def test_new_weight_preserves_iso_timestamp_with_raw_sheet_input(monkeypatch):
    worksheet = Worksheet([sheets.WEIGHT_HEADERS])
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(sheets, "_ensure_worksheet", lambda *_args: worksheet)
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    sheets.append_weight("2026-07-22T07:13:14+08:00", "u1", 66.6)

    assert worksheet.values[-1][0] == "2026-07-22T07:13:14+08:00"
    assert worksheet.append_kwargs[-1]["value_input_option"] == "RAW"


def test_weight_and_training_crud_use_owned_record_ids(monkeypatch):
    weight_ws = Worksheet([
        sheets.WEIGHT_HEADERS,
        ["2026-07-20T08:00:00+08:00", "u1", 66.5, "wgt_1"],
    ])
    training_ws = Worksheet([
        sheets.TRAINING_HEADERS,
        ["2026-07-20", "u1", "有氧訓練", "", "跑步", "", "trn_1"],
    ])
    monkeypatch.setattr(sheets, "_get_sheet", lambda: object())
    monkeypatch.setattr(
        sheets, "_ensure_worksheet",
        lambda _sheet, title, _headers: weight_ws if title == "Weight" else training_ws,
    )
    monkeypatch.setattr(sheets, "clear_read_caches", lambda: None)

    assert sheets.update_weight_by_id("wgt_1", "u1", 66.2) is True
    assert sheets.update_weight_by_id("wgt_1", "u2", 70) is False
    assert sheets.update_training_by_id(
        "trn_1", "u1", ["有氧訓練"], cardio_detail="單車 30 分鐘"
    ) is True
    assert sheets.delete_training_by_id("trn_1", "u2") is False
    assert sheets.delete_weight_by_id("wgt_1", "u1") is True
    assert sheets.delete_training_by_id("trn_1", "u1") is True


def test_application_rejects_cross_student_record_changes(monkeypatch):
    monkeypatch.setattr(
        sheets, "update_record_by_id",
        lambda *_args, **_kwargs: pytest.fail("repository must not be called"),
    )
    with pytest.raises(application.PermissionDenied):
        application.update_own_record(
            AuthContext(user_id="u1", role="student"),
            "u2", "rec_1", {"calories": 100},
        )


def test_history_manager_uses_calendar_summary_and_single_level_dialogs():
    source = inspect.getsource(history_records)

    assert '@st.dialog("修改紀錄")' in source
    assert '@st.dialog("刪除紀錄")' in source
    assert '@st.dialog("新增歷史紀錄")' not in source
    assert "today = auth.today_date()" in source
    assert "history_record_calendar(" in source
    assert "metrics.sum_totals(nutrition_records)" in source
    assert "get_record_id_schema_status" in source
    assert "record_id" in source


def test_history_manager_uses_one_summary_row_without_main_page_details():
    source = inspect.getsource(history_records.render_daily_record_manager)

    assert 'key="history_daily_summary"' in source
    assert 'key="history_daily_summary_actions"' in source
    assert 'key="history_day_manage"' in source
    assert 'key="history_day_delete"' in source
    assert "horizontal=True" in source
    assert "st.date_input" not in source
    assert "st.metric" not in source
    assert 'key="history_add_actions"' not in source
    assert 'key="history_record_list"' not in source
    assert "當日明細" not in source


def test_dialog_flow_keeps_add_edit_and_confirmed_single_record_delete():
    manage_source = inspect.getsource(history_records._render_manage_day_dialog)
    manage_wrapper = inspect.getsource(history_records._manage_day_dialog)
    delete_source = inspect.getsource(history_records._render_delete_day_dialog)
    delete_wrapper = inspect.getsource(history_records._delete_day_dialog)

    assert 'key="history_dialog_add_actions"' in manage_source
    assert "if not items:" in manage_source
    assert "_render_daily_totals_edit_form" in manage_source
    assert 'key="history_dialog_totals"' in manage_source
    assert "build_daily_totals_html(_daily_totals_for_items(items))" in manage_source
    assert "_render_add_form" in manage_source
    assert "_render_edit_form" in manage_source
    assert "_find_record_item" in manage_source
    assert 'key="history_manage_dialog"' in manage_wrapper
    assert "請選擇要刪除的紀錄" in delete_source
    assert "刪除後無法復原" in delete_source
    assert 'key="history_delete_confirm"' in delete_source
    assert "_delete_record(kind, record_id, user_id)" in delete_source
    assert 'key="history_delete_dialog"' in delete_wrapper


def test_daily_totals_sum_multiple_food_and_water_records_into_three_lines():
    items = [
        ("2026-07-22T08:00:00+08:00", "food", {
            "calories": 420, "protein": 25, "water_ml": 0,
        }),
        ("2026-07-22T12:00:00+08:00", "food", {
            "calories": 580, "protein": 35, "water_ml": 0,
        }),
        ("2026-07-22T09:00:00+08:00", "water", {
            "calories": 0, "protein": 0, "water_ml": 500,
        }),
        ("2026-07-22T15:00:00+08:00", "water", {
            "calories": 0, "protein": 0, "water_ml": 750,
        }),
    ]

    totals = history_records._daily_totals_for_items(items)
    markup = history_records.build_daily_totals_html(totals)

    assert totals["calories"] == 1000
    assert totals["protein"] == 60
    assert totals["water"] == 1250
    assert "熱量 <strong>1,000</strong> kcal" in markup
    assert "蛋白質 <strong>60</strong> g" in markup
    assert "飲水 <strong>1,250</strong> ml" in markup
    assert markup.count("<div>") == 3


def test_replacing_daily_totals_changes_only_rows_needed_for_aggregate(monkeypatch):
    updates = []
    appends = []
    monkeypatch.setattr(
        history_records, "current_auth_context",
        lambda: AuthContext(user_id="u1", role="student"),
    )
    monkeypatch.setattr(
        application, "update_own_record",
        lambda _context, user_id, record_id, values: updates.append(
            (user_id, record_id, values)
        ) or True,
    )
    monkeypatch.setattr(
        application, "append_student_record",
        lambda *_args, **kwargs: appends.append(kwargs) or "rec_new",
    )
    items = [
        ("2026-07-19T12:00:00+08:00", "food", {
            "record_id": "food_new", "calories": 500, "protein": 30,
        }),
        ("2026-07-19T08:00:00+08:00", "food", {
            "record_id": "food_old", "calories": 700, "protein": 40,
        }),
        ("2026-07-19T15:00:00+08:00", "water", {
            "record_id": "water_new", "water_ml": 600,
        }),
        ("2026-07-19T09:00:00+08:00", "water", {
            "record_id": "water_old", "water_ml": 500,
        }),
    ]

    history_records._replace_daily_nutrition_totals(
        history_records.date(2026, 7, 19), items, "u1",
        calories=2177, protein=101, water_ml=1400,
    )

    assert updates == [
        ("u1", "food_new", {"calories": 1477.0, "protein": 61.0}),
        ("u1", "water_new", {"water_ml": 900.0}),
    ]
    assert appends == []


def test_replacing_daily_totals_creates_missing_nutrition_rows(monkeypatch):
    appends = []
    monkeypatch.setattr(
        history_records, "current_auth_context",
        lambda: AuthContext(user_id="u1", role="student"),
    )
    monkeypatch.setattr(
        application, "append_student_record",
        lambda *_args, **kwargs: appends.append(kwargs) or "rec_new",
    )

    history_records._replace_daily_nutrition_totals(
        history_records.date(2026, 7, 19),
        [("2026-07-19", "weight", {"record_id": "wgt_1"})],
        "u1", calories=900, protein=55, water_ml=1200,
    )

    assert [row["meal_type"] for row in appends] == ["食物", "飲水"]
    assert appends[0]["calories"] == 900
    assert appends[0]["protein"] == 55
    assert appends[1]["water_ml"] == 1200


def test_history_food_add_uses_fixed_summary_without_content_input():
    add_source = inspect.getsource(history_records._render_add_form)

    assert 'st.text_input("食物內容")' not in add_source
    assert 'food_summary="手動紀錄"' in add_source
    assert 'calories = st.number_input("熱量 (kcal)"' in add_source
    assert 'protein = st.number_input("蛋白質 (g)"' in add_source
    assert "calorie_value == 0 and protein_value == 0" in add_source


def test_backdated_timestamp_keeps_selected_day_and_taipei_offset():
    timestamp = history_records._selected_day_timestamp(
        history_records.date(2026, 7, 1)
    )

    assert timestamp.startswith("2026-07-01T")
    assert timestamp.endswith("+08:00")
