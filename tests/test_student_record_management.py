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


def test_history_manager_uses_date_summary_and_native_dialogs():
    source = inspect.getsource(history_records)

    assert '@st.dialog("修改紀錄")' in source
    assert '@st.dialog("刪除紀錄")' in source
    assert '@st.dialog("新增歷史紀錄")' in source
    assert "today = auth.today_date()" in source
    assert "max_value=today" in source
    assert "metrics.sum_totals(records)" in source
    assert "get_record_id_schema_status" in source
    assert "record_id" in source


def test_history_manager_uses_compact_horizontal_actions_and_scrolling_list():
    source = inspect.getsource(history_records.render_daily_record_manager)

    assert 'key="history_add_actions"' in source
    assert "horizontal=True" in source
    assert 'key="history_record_list"' in source
    assert "height=300" in source
    assert 'key=f"history_record_actions_{row_key}"' in source
    assert 'key=f"history_edit_{row_key}"' in source
    assert 'key=f"history_delete_{row_key}"' in source
    assert "st.columns([6, 1, 1]" not in source


def test_backdated_timestamp_keeps_selected_day_and_taipei_offset():
    timestamp = history_records._selected_day_timestamp(
        history_records.date(2026, 7, 1)
    )

    assert timestamp.startswith("2026-07-01T")
    assert timestamp.endswith("+08:00")
