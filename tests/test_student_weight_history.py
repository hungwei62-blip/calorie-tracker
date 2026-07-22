from __future__ import annotations

from datetime import date
import inspect

import pytest

from domain.history import build_weight_history_series
from pages import student as student_pages
from ui import styles


def _points(records, start=date(2026, 7, 12), end=date(2026, 7, 18)):
    return build_weight_history_series(records, start, end)


def test_weight_card_header_shows_latest_value_and_change():
    points = _points(
        [
            {"timestamp": "2026-07-10T08:00:00+08:00", "weight_kg": 52},
            {"timestamp": "2026-07-15T08:00:00+08:00", "weight_kg": 51.5},
            {"timestamp": "2026-07-18T08:00:00+08:00", "weight_kg": 51},
        ]
    )

    heading = student_pages.build_weight_history_card_header_html(points)
    assert "51.0" in heading
    assert "kg" in heading
    assert "↓ -1.0 kg" in heading
    assert "weight-history-summary" not in heading


def test_flat_weight_figure_has_padding_and_only_measured_markers():
    points = _points(
        [{"timestamp": "2026-07-10T08:00:00+08:00", "weight_kg": 50}]
    )

    figure = student_pages.build_weight_history_figure(points, 7)

    assert list(figure.data[0].y) == [50.0] * 7
    assert list(figure.data[1].x) == []
    assert list(figure.layout.yaxis.range) == [49.5, 50.5]
    assert len(figure.layout.xaxis.tickvals) == 4
    assert figure.data[0].line.shape == "spline"
    assert figure.data[0].line.color == "#A8D5C2"
    assert figure.data[0].mode == "lines+markers+text"
    assert list(figure.data[0].text) == ["50.0"] * 7
    assert figure.data[0].textposition == "top center"
    assert figure.data[0].fill == "tozeroy"
    assert figure.data[0].fillgradient.type == "vertical"
    assert list(figure.data[0].fillgradient.colorscale) == [
        (0.0, "rgba(168,213,194,0.00)"),
        (0.55, "rgba(168,213,194,0.22)"),
        (1.0, "rgba(168,213,194,0.72)"),
    ]
    assert figure.data[0].fillgradient.start == 49.5
    assert figure.data[0].fillgradient.stop == 50.5
    assert figure.layout.yaxis.visible is False
    assert figure.layout.margin.l == 18
    assert figure.layout.margin.b == 22
    assert list(figure.layout.xaxis.range) == [date(2026, 7, 12), date(2026, 7, 18)]
    assert figure.layout.xaxis.automargin is False


def test_small_weight_change_uses_balanced_minimum_visible_span():
    points = _points(
        [
            {"timestamp": "2026-07-15T08:00:00+08:00", "weight_kg": 67.0},
            {"timestamp": "2026-07-18T08:00:00+08:00", "weight_kg": 66.6},
        ]
    )

    figure = student_pages.build_weight_history_figure(points, 7)

    assert list(figure.layout.yaxis.range) == pytest.approx([66.5, 67.1])


def test_thirty_day_figure_reduces_tick_density_and_marks_real_records():
    points = build_weight_history_series(
        [
            {"timestamp": "2026-06-20T08:00:00+08:00", "weight_kg": 52},
            {"timestamp": "2026-07-18T08:00:00+08:00", "weight_kg": 51},
        ],
        date(2026, 6, 19),
        date(2026, 7, 18),
    )

    figure = student_pages.build_weight_history_figure(points, 30)

    assert len(figure.layout.xaxis.tickvals) == 5
    assert list(figure.data[1].y) == [52.0, 51.0]
    assert figure.data[1].marker.color == "#A8D5C2"
    assert figure.layout.height == 220


def test_history_page_uses_clean_heading_and_renders_all_history_sections():
    source = inspect.getsource(student_pages.page_history)
    renderer_source = inspect.getsource(
        student_pages._render_student_weight_history
    )

    assert 'st.subheader("體重變化")' not in renderer_source
    assert 'key="student_history_page"' in source
    assert 'st.header("歷史紀錄")' not in source
    assert '("歷史紀錄", "修改紀錄")' in source
    assert 'default="歷史紀錄"' in source
    assert 'key="student_history_tabs"' in source
    assert 'on_change="rerun"' in source
    assert "if history_tab.open:" in source
    assert "elif edit_tab.open:" in source
    assert source.index("if history_tab.open:") < source.index(
        "_render_student_weight_history(uid)"
    ) < source.index("elif edit_tab.open:") < source.index(
        "render_daily_record_manager(uid, _clear_analysis_cache)"
    )
    assert "📜" not in source
    assert source.index("_render_student_weight_history(uid)") < source.index(
        "_render_student_nutrition_history(uid)"
    ) < source.index("_render_student_water_history(uid)") < source.index(
        "_render_student_training_history(uid)"
    )
    assert "st.dataframe" not in source
    assert "st.bar_chart" not in source
    assert "營養目標尚未設定" not in source
    assert "st.segmented_control(" in renderer_source
    assert '("7 天", "30 天")' in renderer_source
    assert 'key="weight_history_range"' in renderer_source
    assert 'key="student_weight_history_card"' in renderer_source
    assert 'key="student_weight_history_chart"' in renderer_source
    assert 'open_daily_record_tab("體重")' in renderer_source
    assert "build_weight_history_card_footer_html" not in renderer_source
    assert "本期間實際量測" not in inspect.getsource(student_pages)


def test_weight_history_has_scoped_card_and_mobile_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-student_weight_history" in value
    )

    assert ".st-key-student_weight_history_card" in stylesheet
    assert ".weight-history-card-heading" in stylesheet
    assert "font-size: 30px !important;" in stylesheet
    assert "flex-wrap: nowrap !important;" in stylesheet
    assert ".st-key-student_weight_history_chart" in stylesheet
    assert "padding-left: 18px !important;" in stylesheet
    assert "height: 230px !important;" not in stylesheet
    assert ".weight-history-card-footer" not in stylesheet
    assert "padding: 18px 18px 4px !important;" in stylesheet
    assert "margin-bottom: 0 !important;" in stylesheet
    assert ".st-key-student_history_page" in stylesheet
    assert "padding-top: 32px !important;" in stylesheet
    assert "--history-primary: #A8D5C2;" in stylesheet
    assert "--history-background: #F7FAF8;" in stylesheet
    assert "--history-secondary: #7D8C8A;" in stylesheet
    assert "--history-border: #E6EDEB;" in stylesheet
    assert ".stApp:has(.st-key-student_history_page)" in stylesheet


def test_history_record_manager_has_scoped_calendar_summary_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-student_daily_record_manager" in value
    )

    assert ".st-key-history_daily_summary" in stylesheet
    assert ".st-key-history_daily_summary_values" in stylesheet
    assert ".history-daily-summary-values" in stylesheet
    assert ".st-key-history_daily_summary_actions" in stylesheet
    assert ".st-key-history_dialog_add_actions" in stylesheet
    assert ".st-key-history_manage_dialog" in stylesheet
    assert ".st-key-history_delete_dialog" in stylesheet
    assert ".st-key-history_dialog_totals" in stylesheet
    assert "flex-wrap: nowrap !important;" in stylesheet
    assert "white-space: nowrap !important;" in stylesheet
    assert "background: #F6E8DE !important;" in stylesheet
    assert "color: #B88470 !important;" in stylesheet
    assert "border-color: #EBCFC0 !important;" in stylesheet
    assert "background: #FFFFFF !important;" in stylesheet
    assert "font-size: 16px !important;" in stylesheet
    assert "min-height: 112px !important;" in stylesheet
    assert ".st-key-history_day_manage button" in stylesheet
    assert "display: grid !important;" in stylesheet
    assert ".st-key-student_history_tabs" in stylesheet
    assert "margin-top: -8px !important;" in stylesheet
    assert "background-color: transparent !important;" in stylesheet

    all_styles = "\n".join(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str)
    )
    assert ".stTabs *" not in all_styles
    assert ".st-key-student_history_page button > div" in all_styles
