from __future__ import annotations

import inspect

from pages import coach as coach_pages
from pages import student as student_pages


def test_coach_history_uses_student_chart_renderer_and_named_page_container():
    source = inspect.getsource(coach_pages.page_coach_student_history)

    assert 'key="coach_student_history_page"' in source
    assert 'st.header("學員歷史")' in source
    assert 'key="student_history_page"' in source
    assert "render_student_history_charts(" in source
    assert "allow_record_actions=False" in source
    assert "go.Figure" not in source
    assert "st.dataframe" not in source


def test_shared_history_renderer_contains_all_four_student_sections():
    source = inspect.getsource(student_pages.render_student_history_charts)

    assert "_render_student_weight_history(" in source
    assert "_render_student_nutrition_history(" in source
    assert "_render_student_water_history(" in source
    assert "_render_student_training_history(" in source
    assert "history_data.records" in source
    assert "history_data.weights" in source
    assert "history_data.trainings" in source


def test_history_bundle_loads_each_source_once(monkeypatch):
    calls = {"records": 0, "weights": 0, "trainings": 0}

    def records(user_id):
        calls["records"] += 1
        return [{"user_id": user_id}]

    def weights(user_id):
        calls["weights"] += 1
        return [{"user_id": user_id}]

    def trainings(user_id):
        calls["trainings"] += 1
        return [{"user_id": user_id}]

    monkeypatch.setattr(student_pages, "_fetch_records_cached", records)
    monkeypatch.setattr(student_pages.sheets, "get_weight_records", weights)
    monkeypatch.setattr(student_pages.sheets, "get_training_records", trainings)

    bundle = student_pages.load_student_history_data("student-1")

    assert calls == {"records": 1, "weights": 1, "trainings": 1}
    assert bundle.records == [{"user_id": "student-1"}]
    assert bundle.weights == [{"user_id": "student-1"}]
    assert bundle.trainings == [{"user_id": "student-1"}]


def test_coach_history_keeps_import_and_export_inside_data_tools():
    source = inspect.getsource(coach_pages._render_coach_history_data_tools)

    assert '"資料工具"' in source
    assert 'on_change="rerun"' in source
    assert "if not tools.open:" in source
    assert 'st.button(\n            "準備下載檔案"' in source
    assert "application.import_student_records" in source
    assert "_build_history_csv" in source
    assert "_build_history_pdf" in source
    assert '"7 天", "30 天", "自訂日期"' in source
    assert "sheets.get_records" not in source
    assert "sheets.get_weight_records" not in source
    assert "sheets.get_training_records" not in source
    assert source.index('"準備下載檔案"') < source.index("sheets.get_notes")


def test_closed_data_tools_do_not_load_or_build_exports(monkeypatch):
    class ClosedExpander:
        open = False

    monkeypatch.setattr(
        coach_pages.st, "expander", lambda *args, **kwargs: ClosedExpander()
    )
    monkeypatch.setattr(
        coach_pages.sheets,
        "get_notes",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("notes must stay lazy")
        ),
    )
    monkeypatch.setattr(
        coach_pages,
        "_build_history_pdf",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("PDF must stay lazy")
        ),
    )

    coach_pages._render_coach_history_data_tools(
        {},
        "student-1",
        "Student",
        student_pages.StudentHistoryData([], [], []),
    )


def test_open_data_tools_wait_for_prepare_before_export(monkeypatch):
    class OpenExpander:
        open = True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(coach_pages.st, "session_state", {})
    monkeypatch.setattr(
        coach_pages.st, "expander", lambda *args, **kwargs: OpenExpander()
    )
    monkeypatch.setattr(coach_pages.st, "subheader", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        coach_pages.st, "file_uploader", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        coach_pages.st,
        "segmented_control",
        lambda *args, **kwargs: "7 天",
    )
    monkeypatch.setattr(coach_pages.st, "button", lambda *args, **kwargs: False)
    monkeypatch.setattr(coach_pages.st, "caption", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        coach_pages.sheets,
        "get_notes",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("notes must wait for the prepare button")
        ),
    )
    monkeypatch.setattr(
        coach_pages,
        "_build_history_pdf",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("PDF must wait for the prepare button")
        ),
    )

    coach_pages._render_coach_history_data_tools(
        {},
        "student-1",
        "Student",
        student_pages.StudentHistoryData([], [], []),
    )


def test_prepare_export_reuses_chart_rows_and_only_loads_notes(monkeypatch):
    class OpenExpander:
        open = True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    class Column:
        def download_button(self, *args, **kwargs):
            return None

    calls = {"notes": 0, "csv": 0, "pdf": 0}
    monkeypatch.setattr(coach_pages.st, "session_state", {})
    monkeypatch.setattr(
        coach_pages.st, "expander", lambda *args, **kwargs: OpenExpander()
    )
    monkeypatch.setattr(coach_pages.st, "subheader", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        coach_pages.st, "file_uploader", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        coach_pages.st,
        "segmented_control",
        lambda *args, **kwargs: "7 天",
    )
    monkeypatch.setattr(coach_pages.st, "button", lambda *args, **kwargs: True)
    monkeypatch.setattr(coach_pages.st, "columns", lambda count: [Column(), Column()])

    def get_notes(user_id):
        calls["notes"] += 1
        return []

    def build_csv(*args, **kwargs):
        calls["csv"] += 1
        return b"csv"

    def build_pdf(*args, **kwargs):
        calls["pdf"] += 1
        return b"pdf"

    monkeypatch.setattr(coach_pages.sheets, "get_notes", get_notes)
    monkeypatch.setattr(coach_pages, "_build_history_csv", build_csv)
    monkeypatch.setattr(coach_pages, "_build_history_pdf", build_pdf)
    monkeypatch.setattr(
        coach_pages.sheets,
        "get_records",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("records must be reused from the chart bundle")
        ),
    )

    coach_pages._render_coach_history_data_tools(
        {},
        "student-1",
        "Student",
        student_pages.StudentHistoryData([], [], []),
    )

    assert calls == {"notes": 1, "csv": 1, "pdf": 1}
    assert coach_pages.st.session_state[
        coach_pages._HISTORY_EXPORT_CACHE_KEY
    ]["signature"][0] == "student-1"


def test_coach_history_preloads_after_authorization():
    source = inspect.getsource(coach_pages.page_coach_student_history)

    assert source.index("application.get_student(") < source.index(
        "load_student_history_data(user_id)"
    )
    assert "history_data=history_data" in source
    assert "history_data\n        )" in source
