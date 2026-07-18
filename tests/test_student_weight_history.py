from __future__ import annotations

from datetime import date
import inspect

from domain.history import build_weight_history_series
from pages import student as student_pages
from ui import styles


def _points(records, start=date(2026, 7, 12), end=date(2026, 7, 18)):
    return build_weight_history_series(records, start, end)


def test_weight_summary_uses_latest_change_and_actual_measurement_count():
    points = _points(
        [
            {"timestamp": "2026-07-10T08:00:00+08:00", "weight_kg": 52},
            {"timestamp": "2026-07-15T08:00:00+08:00", "weight_kg": 51.5},
            {"timestamp": "2026-07-18T08:00:00+08:00", "weight_kg": 51},
        ]
    )

    markup = student_pages.build_weight_history_summary_html(points)

    assert "目前體重" in markup
    assert "51.0 kg" in markup
    assert "-1.0 kg" in markup
    assert "2 次" in markup


def test_flat_weight_figure_has_padding_and_only_measured_markers():
    points = _points(
        [{"timestamp": "2026-07-10T08:00:00+08:00", "weight_kg": 50}]
    )

    figure = student_pages.build_weight_history_figure(points, 7)

    assert list(figure.data[0].y) == [50.0] * 7
    assert list(figure.data[1].x) == []
    assert list(figure.layout.yaxis.range) == [49.0, 51.0]
    assert len(figure.layout.xaxis.tickvals) == 7


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

    assert len(figure.layout.xaxis.tickvals) < 30
    assert list(figure.data[1].y) == [52.0, 51.0]
    assert figure.layout.height == 300


def test_history_page_renders_weight_before_legacy_nutrition_content():
    source = inspect.getsource(student_pages.page_history)
    renderer_source = inspect.getsource(
        student_pages._render_student_weight_history
    )

    assert source.index("_render_student_weight_history(uid)") < source.index(
        'st.subheader("每日攝取")'
    )
    assert "st.segmented_control(" in renderer_source
    assert '("7 天", "30 天")' in renderer_source
    assert 'key="weight_history_range"' in renderer_source
    assert 'key="student_weight_history_chart"' in renderer_source
    assert 'open_daily_record_tab("體重")' in renderer_source


def test_weight_history_has_scoped_three_column_mobile_styles():
    stylesheet = next(
        value
        for value in styles.apply_global_styles.__code__.co_consts
        if isinstance(value, str) and ".st-key-student_weight_history" in value
    )

    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in stylesheet
    assert ".st-key-student_weight_history_chart" in stylesheet
    assert "height: 260px !important;" in stylesheet
