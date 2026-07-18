from __future__ import annotations

import base64
import inspect

from pages import common
from pages import student as student_pages
from pages import coach as coach_pages
from ui import styles


def test_shared_avatar_returns_local_jpeg_as_data_uri(tmp_path):
    avatar_bytes = b"test-jpeg-content"
    avatar_path = tmp_path / "avatar.jpg"
    avatar_path.write_bytes(avatar_bytes)

    source = common.get_default_avatar_source(str(avatar_path))

    assert source == "data:image/jpeg;base64," + base64.b64encode(
        avatar_bytes
    ).decode("ascii")


def test_shared_avatar_uses_fallback_for_missing_file(tmp_path):
    missing_path = tmp_path / "missing.jpg"

    assert common.get_default_avatar_source(str(missing_path)) == (
        common.DEFAULT_AVATAR_FALLBACK
    )


def test_student_and_coach_pages_use_the_shared_avatar_source():
    student_source = inspect.getsource(student_pages.page_personal)
    coach_source = inspect.getsource(coach_pages.page_coach_overview)

    assert "get_default_avatar_source()" in student_source
    assert "get_default_avatar_source()" in coach_source
    assert "os.path.exists" not in student_source


def test_coach_overview_has_same_scoped_top_spacing_as_student_home():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-coach_overview_header" in value
    )

    assert stylesheet.count(
        '.main .block-container:has(.st-key-coach_overview_header),'
    ) == 2
    assert stylesheet.count(
        '[data-testid="stMainBlockContainer"]:has(.st-key-coach_overview_header)'
    ) == 2
    assert ".st-key-coach_overview_header .coach-home-welcome" in stylesheet
    assert "padding-top: 32px !important;" in stylesheet
