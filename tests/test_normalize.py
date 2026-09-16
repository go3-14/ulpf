import pytest

from mappings.loader import load_mappings
from schema.normalize import normalize
from schema.validate import validate_event


def test_normalize_types_and_unmapped():
    cfg = load_mappings()["cisco_asa"]
    event = normalize(
        {
            "timestamp": "Jan 10 10:00:00",
            "src": "192.0.2.10",
            "spt": "12345",
            "dst": "198.51.100.20",
            "dpt": "443",
            "action": "Built",
            "severity": "6",
            "extra_field": "kept",
        },
        cfg,
        "event-1",
        "cisco_asa",
        "syslog",
    )
    assert event["type_uid"] == event["class_uid"] * 100 + event["activity_id"]
    assert isinstance(event["src_endpoint"]["port"], int)
    assert event["unmapped"]["extra_field"] == "kept"
    validate_event(event)


def test_validator_rejects_string_port():
    cfg = load_mappings()["cisco_asa"]
    event = normalize({"src": "192.0.2.10", "spt": "443"}, cfg, "event-2", "cisco_asa", "syslog")
    event["src_endpoint"]["port"] = "443"
    with pytest.raises(ValueError):
        validate_event(event)
