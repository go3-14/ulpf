import pytest

from schema.transforms import TransformError, apply_transform, parse_time_ms


def test_port_transform_rejects_bad_port():
    assert apply_transform("443", {"type": "port"}) == 443
    with pytest.raises(TransformError):
        apply_transform("70000", {"type": "port"})


def test_parse_time_ms_epoch_and_iso():
    assert parse_time_ms("1000", {}) == 1000000
    assert isinstance(parse_time_ms("2026-09-15T10:00:00Z", {}), int)
