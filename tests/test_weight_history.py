from __future__ import annotations

from datetime import date

import pytest

from domain.history import build_weight_history_series, history_date_range


def _weight(timestamp: str, value: object) -> dict[str, object]:
    return {"timestamp": timestamp, "weight_kg": value}


@pytest.mark.parametrize(
    ("days", "expected_start"),
    [(7, date(2026, 7, 12)), (30, date(2026, 6, 19))],
)
def test_history_range_is_inclusive_of_today(days, expected_start):
    assert history_date_range(date(2026, 7, 18), days) == (
        expected_start,
        date(2026, 7, 18),
    )


def test_weight_before_range_is_carried_through_today():
    points = build_weight_history_series(
        [_weight("2026-07-08T09:00:00+08:00", 50)],
        date(2026, 7, 12),
        date(2026, 7, 18),
    )

    assert [point.weight_kg for point in points] == [50.0] * 7
    assert not any(point.measured for point in points)
    assert all(point.source_date == date(2026, 7, 8) for point in points)


def test_days_before_first_measurement_remain_empty_then_forward_fill():
    points = build_weight_history_series(
        [_weight("2026-07-15T09:00:00+08:00", 51.5)],
        date(2026, 7, 12),
        date(2026, 7, 18),
    )

    assert [point.weight_kg for point in points] == [
        None,
        None,
        None,
        51.5,
        51.5,
        51.5,
        51.5,
    ]
    assert points[3].measured is True
    assert all(not point.measured for point in points[4:])


def test_latest_timestamp_wins_when_day_has_multiple_measurements():
    points = build_weight_history_series(
        [
            _weight("2026-07-18T08:00:00+08:00", 52),
            _weight("2026-07-18T20:00:00+08:00", 51.7),
        ],
        date(2026, 7, 18),
        date(2026, 7, 18),
    )

    assert points[0].weight_kg == 51.7
    assert points[0].measured is True


def test_invalid_and_future_records_do_not_affect_series():
    records = [
        _weight("invalid", 60),
        _weight("2026-07-17T08:00:00+08:00", "bad"),
        _weight("2026-07-17T09:00:00+08:00", 0),
        _weight("2026-07-17T10:00:00+08:00", -1),
        _weight("2026-07-17T11:00:00+08:00", float("nan")),
        _weight("2026-07-19T08:00:00+08:00", 99),
    ]

    points = build_weight_history_series(
        records, date(2026, 7, 17), date(2026, 7, 18)
    )

    assert [point.weight_kg for point in points] == [None, None]


def test_invalid_ranges_are_rejected():
    with pytest.raises(ValueError):
        history_date_range(date(2026, 7, 18), 0)
    with pytest.raises(ValueError):
        build_weight_history_series([], date(2026, 7, 18), date(2026, 7, 17))
