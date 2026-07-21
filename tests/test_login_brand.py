from __future__ import annotations

import inspect

from pages import student as student_pages
from ui import styles


def test_login_page_uses_project_prime_brand_copy():
    source = inspect.getsource(student_pages.page_login)

    assert 'key="auth_brand"' in source
    assert 'st.session_state.auth_mode != "register"' in source
    assert 'role="heading" aria-level="1"' in source
    assert "<h1" not in source
    assert '<span class="auth-brand-english">Project Prime</span>' in source
    assert '<span class="auth-brand-chinese">巔峰計畫</span>' in source
    assert 'class="auth-brand-logo"' not in source
    assert "巔峰計畫" in source
    assert "練對、吃對" in source
    assert "剩下交給時間" in source
    assert "把自己推向人生最好的狀態" in source
    assert "吃對、練對持續做。" not in source
    assert 'st.button("註冊新學員", key="nav_to_register")' in source
    assert 'st.container(key="login_panel")' in source
    assert 'st.container(key="login_secondary_action")' in source
    assert "還沒有帳號？立即註冊" not in source
    assert "飲食控制管理系統" not in source
    assert "輕鬆記錄飲食，追蹤你的營養目標" not in source


def test_registration_page_hides_brand_and_uses_compact_centered_layout():
    source = inspect.getsource(student_pages.page_login)
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-registration_page" in value
    )

    assert 'st.container(key="registration_page", gap="small")' in source
    assert 'st.subheader("註冊學員帳號", text_alignment="center")' in source
    assert 'st.subheader("建立學員帳號")' not in source
    assert 'st.info("填寫以下資料即可建立帳號")' not in source
    assert 'with st.form("signup_form")' in source
    registration_source = source[
        source.index('st.session_state.auth_mode == "register"'):
        source.index('st.subheader("忘記密碼")')
    ]
    assert 'st.radio("記錄模式"' not in registration_source
    assert 'record_mode="simple"' in registration_source
    assert 'st.button("← 返回登入頁", key="nav_to_login")' in source
    assert ".stApp:has(.st-key-registration_page)" in stylesheet
    assert '.st-key-registration_page [data-testid="stForm"]' in stylesheet
    assert "max-width: 760px !important;" in stylesheet
    assert "margin: 6px auto !important;" in stylesheet
    assert "padding: 18px 22px !important;" in stylesheet
    assert '.block-container:has(.st-key-registration_page)' in stylesheet
    assert "padding-top: 4.25rem !important;" in stylesheet


def test_brand_mark_is_text_only():
    source = inspect.getsource(student_pages)

    assert "BRAND_MARK_PATH" not in source
    assert "_load_brand_mark_data_uri" not in source
    assert "peak_plan_logo.png" not in source


def test_login_brand_has_scoped_responsive_typography():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-auth_brand" in value
    )

    assert ".st-key-auth_brand .auth-brand-title" in stylesheet
    assert ".st-key-auth_brand .auth-brand-english" in stylesheet
    assert ".st-key-auth_brand .auth-brand-tagline" in stylesheet
    assert "display: grid !important;" in stylesheet
    assert "grid-template-columns: repeat(3, max-content) !important;" in stylesheet
    assert "width: max-content !important;" in stylesheet
    assert "max-width: 100% !important;" in stylesheet
    brand_title_block = stylesheet.split(
        ".st-key-auth_brand .auth-brand-title {", maxsplit=1
    )[1].split("}", maxsplit=1)[0]
    assert "margin: 0 auto !important;" in brand_title_block
    assert "font-size: clamp(18px, 2.8vw, 24px) !important;" in stylesheet
    assert "font-size: clamp(14px, 4.4vw, 18px) !important;" in stylesheet
    assert '"PingFang TC"' in stylesheet
    assert '"SF Pro Display"' in stylesheet
    assert '"Microsoft JhengHei"' in stylesheet
    assert "letter-spacing: 0.025em !important;" in stylesheet
    assert "max-width: 680px !important;" in stylesheet
    assert "line-height: 1.8 !important;" in stylesheet
    assert ".st-key-auth_brand .auth-brand-tagline span" in stylesheet
    assert "display: block !important;" in stylesheet
    assert ".st-key-auth_brand .auth-brand-chinese" in stylesheet
    assert 'font-family: "Noto Sans TC"' in stylesheet
    assert "display: inline-flex !important;" not in brand_title_block
    assert "flex-wrap" not in brand_title_block
    assert "flex:" not in brand_title_block
    assert "min-width: 0 !important;" in stylesheet
    assert "width: 100% !important;" in stylesheet


def test_auth_page_opts_out_of_normal_dark_mode():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-auth_brand" in value
    )

    assert ".stApp:has(.st-key-auth_brand)" in stylesheet
    assert "color-scheme: light !important;" in stylesheet
    assert "-webkit-text-fill-color: #2F3E46 !important;" in stylesheet
    assert ".stApp:has(.st-key-auth_brand) input:-webkit-autofill" in stylesheet


def test_login_actions_use_scoped_muji_button_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-login_panel" in value
    )

    assert '.st-key-login_panel div[data-testid="stFormSubmitButton"] button' in stylesheet
    assert ".st-key-login_secondary_action div.stButton > button" in stylesheet
    assert ".st-key-login_form" not in stylesheet
    assert ".st-key-nav_to_register" not in stylesheet
    assert "background: rgba(255, 255, 255, 0.72) !important;" in stylesheet
    assert "background-color: rgba(255, 255, 255, 0.72) !important;" in stylesheet
    assert "border: 1px solid rgba(112, 116, 110, 0.24) !important;" in stylesheet
    assert "box-shadow: none !important;" in stylesheet
    assert "width: fit-content !important;" in stylesheet
    assert "background: transparent !important;" in stylesheet


def test_login_page_is_locked_to_viewport_without_vertical_scroll():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-login_panel" in value
    )

    assert "html:has(.st-key-login_panel)" in stylesheet
    assert "body:has(.st-key-login_panel)" in stylesheet
    assert '.stApp:has(.st-key-login_panel) [data-testid="stMain"]' in stylesheet
    assert '.block-container:has(.st-key-login_panel)' in stylesheet
    assert "max-height: 100dvh !important;" in stylesheet
    assert "overflow: hidden !important;" in stylesheet
    assert "overscroll-behavior: none !important;" in stylesheet
    assert "@media (max-height: 700px)" in stylesheet
    assert ".st-key-login_panel [data-testid=\"stForm\"]" in stylesheet
