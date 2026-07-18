from __future__ import annotations

import base64
import inspect

from pages import student as student_pages
from ui import styles


def test_login_page_uses_project_prime_brand_copy():
    source = inspect.getsource(student_pages.page_login)

    assert 'key="auth_brand"' in source
    assert 'role="heading" aria-level="1"' in source
    assert "<h1" not in source
    assert '<span class="auth-brand-english">Project Prime</span>' in source
    assert 'class="auth-brand-logo"' in source
    assert 'alt="巔峰計畫"' in source
    assert 'class="auth-brand-chinese"' not in source
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


def test_brand_mark_asset_is_bundled_as_png_data_uri():
    assert student_pages.BRAND_MARK_PATH.is_file()
    assert not (student_pages.BRAND_MARK_PATH.parent / "project_prime_logo.png").exists()

    data_uri = student_pages._load_brand_mark_data_uri()
    prefix, payload = data_uri.split(",", maxsplit=1)

    assert prefix == "data:image/png;base64"
    assert base64.b64decode(payload) == student_pages.BRAND_MARK_PATH.read_bytes()


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
    assert "grid-template-columns: max-content max-content 105px !important;" in stylesheet
    assert "grid-template-columns: max-content max-content 80px !important;" in stylesheet
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
    assert ".st-key-auth_brand .auth-brand-logo-frame" in stylesheet
    assert ".st-key-auth_brand .auth-brand-logo" in stylesheet
    assert "display: inline-flex !important;" not in stylesheet
    assert "flex-wrap" not in brand_title_block
    assert "flex:" not in brand_title_block
    assert "min-width: 0 !important;" in stylesheet
    assert "width: 100% !important;" in stylesheet
    assert "height: 31px !important;" in stylesheet
    assert "height: 24px !important;" in stylesheet
    assert "object-fit: cover !important;" in stylesheet
    assert "object-position: center !important;" in stylesheet


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
