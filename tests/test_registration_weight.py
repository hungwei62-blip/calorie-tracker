from __future__ import annotations

import inspect

from pages import common
from pages import student as student_pages


def test_initial_registration_weight_uses_registration_timestamp(monkeypatch):
    appended = []
    monkeypatch.setattr(
        student_pages.sheets,
        "append_weight",
        lambda timestamp, user_id, weight: appended.append(
            (timestamp, user_id, weight)
        ),
    )

    warning = student_pages._save_initial_registration_weight(
        "2026-07-18T10:30:00+08:00", "student-1", 61.5
    )

    assert warning is None
    assert appended == [("2026-07-18T10:30:00+08:00", "student-1", 61.5)]


def test_initial_weight_failure_returns_recovery_message(monkeypatch):
    monkeypatch.setattr(
        student_pages.sheets,
        "append_weight",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("sheet unavailable")),
    )

    warning = student_pages._save_initial_registration_weight(
        "2026-07-18T10:30:00+08:00", "student-1", 61.5
    )

    assert "帳號已建立" in warning
    assert "日常紀錄" in warning


def test_registration_reuses_one_timestamp_and_personal_page_shows_warning():
    login_source = inspect.getsource(student_pages.page_login)
    personal_source = inspect.getsource(student_pages.page_personal)
    session_source = inspect.getsource(common.init_session)

    assert "registration_timestamp = auth.now_iso()" in login_source
    assert "pwd_hash, registration_timestamp" in login_source
    assert "registration_timestamp, uid, initial_weight" in login_source
    assert '"initial_weight_save_warning": None' in session_source
    assert '"initial_weight_save_warning", None' in personal_source
    assert "st.warning(initial_weight_warning)" in personal_source
