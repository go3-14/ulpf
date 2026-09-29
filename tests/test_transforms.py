from datetime import datetime, timezone

import pytest

from schema.transforms import TransformError, parse_time_ms


def _ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def test_epoch_magnitudes():
    assert parse_time_ms(1_700_000_000, {}, 0) == 1_700_000_000_000
    assert parse_time_ms(1_700_000_000_000, {}, 0) == 1_700_000_000_000
    assert parse_time_ms(1_700_000_000_000_000, {}, 0) == 1_700_000_000_000
    assert parse_time_ms(1_700_000_000_000_000_000, {}, 0) == 1_700_000_000_000
    assert parse_time_ms("1700000000", {}, 0) == 1_700_000_000_000


def test_yearless_february_29_walks_back_to_leap_year():
    reference = _ms("2026-03-01T00:00:00Z")
    cfg = {"formats": ["%b %d %H:%M:%S"], "timezone": "UTC"}
    assert parse_time_ms("Feb 29 12:00:00", cfg, reference) == _ms("2024-02-29T12:00:00Z")


def test_yearless_december_log_near_new_year_uses_previous_year():
    reference = _ms("2026-01-02T00:00:00Z")
    cfg = {"formats": ["%b %d %H:%M:%S"], "timezone": "UTC"}
    assert parse_time_ms("Dec 31 23:00:00", cfg, reference) == _ms("2025-12-31T23:00:00Z")


def test_named_and_fixed_timezones_match():
    reference = _ms("2026-01-02T00:00:00Z")
    value = "Jan 02 05:30:00"
    fixed = {"formats": ["%b %d %H:%M:%S"], "timezone": "+05:30"}
    named = {"formats": ["%b %d %H:%M:%S"], "timezone": "Asia/Kolkata"}
    assert parse_time_ms(value, fixed, reference) == parse_time_ms(value, named, reference)
    assert parse_time_ms(value, fixed, reference) == _ms("2026-01-02T00:00:00Z")


def test_iso_offset_wins_over_yaml_timezone():
    cfg = {"formats": ["%Y-%m-%dT%H:%M:%S%z"], "timezone": "UTC"}
    assert parse_time_ms("2026-01-02T05:30:00+05:30", cfg, 0) == _ms("2026-01-02T00:00:00Z")
    assert parse_time_ms("2026-01-02T00:00:00Z", {"timezone": "+05:30"}, 0) == _ms("2026-01-02T00:00:00Z")


def test_space_padded_day_and_english_month_are_locale_independent():
    reference = _ms("2026-09-06T00:00:00Z")
    cfg = {"formats": ["%b %d %H:%M:%S"], "timezone": "UTC"}
    assert parse_time_ms("Sep  5 10:00:00", cfg, reference) == _ms("2026-09-05T10:00:00Z")


def test_garbage_raises_transform_error():
    with pytest.raises(TransformError):
        parse_time_ms("not-a-time", {}, _ms("2026-01-01T00:00:00Z"))
