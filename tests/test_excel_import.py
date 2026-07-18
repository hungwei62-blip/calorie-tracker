from __future__ import annotations

from services import sheets


def test_excel_precomputed_duplicates_can_be_skipped(monkeypatch):
    appended = []
    monkeypatch.setattr(sheets, "append_record", lambda **kwargs: appended.append(kwargs))
    data = {
        "records": [{"date": "2026-07-17", "timestamp": "2026-07-17T12:00:00", "calories": 500, "protein": 30, "water": 600}],
        "existing_dates": {"2026-07-17": {"timestamp": "2026-07-17T08:00:00"}},
    }
    result = sheets.import_records_from_excel(user_id="u1", precomputed_data=data, overwrite_duplicates=False)
    assert result["skipped"] == 1
    assert appended == []


def test_excel_precomputed_new_record_is_imported(monkeypatch):
    appended = []
    monkeypatch.setattr(sheets, "append_record", lambda **kwargs: appended.append(kwargs))
    data = {
        "records": [{"date": "2026-07-17", "timestamp": "2026-07-17T12:00:00", "calories": 500, "protein": 30, "water": 600}],
        "existing_dates": {},
    }
    result = sheets.import_records_from_excel(user_id="u1", precomputed_data=data)
    assert result["imported"] == 1
    assert appended[0]["image_url"] == ""
    assert appended[0]["meal_type"] == "食物"


def test_excel_duplicate_can_be_overwritten(monkeypatch):
    appended = []
    deleted = []
    monkeypatch.setattr(sheets, "append_record", lambda **kwargs: appended.append(kwargs))
    monkeypatch.setattr(sheets, "delete_record", lambda timestamp, user_id: deleted.append((timestamp, user_id)))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    data = {
        "records": [{"date": "2026-07-17", "timestamp": "2026-07-17T12:00:00", "calories": 500, "protein": 30, "water": 600}],
        "existing_dates": {"2026-07-17": {"timestamp": "2026-07-17T08:00:00"}},
    }
    result = sheets.import_records_from_excel(user_id="u1", precomputed_data=data, overwrite_duplicates=True)
    assert result["overwritten"] == 1
    assert deleted == [("2026-07-17T12:00:00", "u1")]
    assert appended[0]["food_summary"] == "由 Excel 匯入（覆寫）"
    assert appended[0]["meal_type"] == "食物"
