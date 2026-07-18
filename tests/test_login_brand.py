from __future__ import annotations

import inspect

from pages import student as student_pages
from ui import styles


def test_login_page_uses_project_prime_brand_copy():
    source = inspect.getsource(student_pages.page_login)

    assert 'key="auth_brand"' in source
    assert "PROJECT PRIME" in source
    assert "巔峰計畫" in source
    assert "吃對、練對持續做。" in source
    assert "剩下交給時間，進化沒有捷徑，" in source
    assert "但每一步都算數，把自己推向人生最好的狀態" in source
    assert "飲食控制管理系統" not in source
    assert "輕鬆記錄飲食，追蹤你的營養目標" not in source


def test_login_brand_has_scoped_responsive_typography():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-auth_brand" in value
    )

    assert ".st-key-auth_brand .auth-brand-title" in stylesheet
    assert ".st-key-auth_brand .auth-brand-tagline" in stylesheet
    assert "font-size: clamp(21px, 4vw, 32px) !important;" in stylesheet
    assert "font-size: clamp(21px, 6.4vw, 26px) !important;" in stylesheet
    assert "letter-spacing: 0.06em !important;" in stylesheet
    assert "max-width: 680px !important;" in stylesheet
    assert "line-height: 1.8 !important;" in stylesheet
    assert ".st-key-auth_brand .auth-brand-tagline span" in stylesheet
    assert "display: block !important;" in stylesheet
