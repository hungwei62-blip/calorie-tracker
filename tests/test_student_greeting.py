from __future__ import annotations

import inspect

from pages import common
from pages import student as student_pages


class _SessionState(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class _StreamlitStub:
    def __init__(self, **session_values):
        self.session_state = _SessionState(session_values)


def test_existing_session_name_is_used_without_sheet_lookup(monkeypatch):
    fake_st = _StreamlitStub(name="王小明", user_id="student-1")
    monkeypatch.setattr(student_pages, "st", fake_st)
    monkeypatch.setattr(
        student_pages.sheets,
        "get_users_rows",
        lambda: (_ for _ in ()).throw(AssertionError("不應查詢 Users")),
    )

    assert student_pages._resolve_student_name() == "王小明"


def test_legacy_session_resolves_and_caches_name_by_user_id(monkeypatch):
    fake_st = _StreamlitStub(name=None, username="account-1", user_id="student-1")
    monkeypatch.setattr(student_pages, "st", fake_st)
    monkeypatch.setattr(
        student_pages.sheets,
        "get_users_rows",
        lambda: [
            {"user_id": "student-1", "username": "account-1", "name": "林同學"}
        ],
    )

    assert student_pages._resolve_student_name() == "林同學"
    assert fake_st.session_state.name == "林同學"


def test_missing_student_name_never_falls_back_to_username(monkeypatch):
    fake_st = _StreamlitStub(name="", username="login-account", user_id="student-1")
    monkeypatch.setattr(student_pages, "st", fake_st)
    monkeypatch.setattr(
        student_pages.sheets,
        "get_users_rows",
        lambda: [{"user_id": "student-1", "username": "login-account", "name": ""}],
    )

    assert student_pages._resolve_student_name() == "學員"


def test_welcome_html_escapes_name_and_uses_hello_format():
    markup = student_pages._build_student_welcome_html(
        '<王 & "小明">', "data:image/jpeg;base64,abc"
    )

    assert 'Hello, &lt;王 &amp; &quot;小明&quot;&gt;!' in markup
    assert '<王 & "小明">' not in markup


def test_auth_flow_stores_real_name_and_home_does_not_use_username():
    login_source = inspect.getsource(student_pages.page_login)
    personal_source = inspect.getsource(student_pages.page_personal)
    init_source = inspect.getsource(common.init_session)

    assert 'st.session_state.name = str(user.get("name")' in login_source
    assert "st.session_state.name = new_name.strip()" in login_source
    assert '"name": None' in init_source
    assert "_resolve_student_name()" in personal_source
    assert "session_state.get('username'" not in personal_source
