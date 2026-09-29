import pytest
from schema.validate import validate_event

def test_phase0_valid_event():
    valid_event = {
        "class_uid": 4001,
        "category_uid": 4,
        "activity_id": 1,
        "type_uid": 400101,
        "time": 1700000000000,
        "severity_id": 1,
        "metadata": {
            "uid": "test-uuid-1234",
            "version": "1.9.0",
            "logged_time": 1700000000000,
            "product": {
                "name": "ULPF",
                "vendor_name": "ULPF"
            }
        },
        "src_endpoint": {
            "ip": "192.168.1.1",
            "port": 443
        }
    }
    # Must not raise
    validate_event(valid_event)

def test_phase0_invalid_event_type_mismatch():
    invalid_event = {
        "class_uid": 4001,
        "category_uid": 4,
        "activity_id": 1,
        "type_uid": 400101,
        "time": 1700000000000,
        "severity_id": 1,
        "metadata": {
            "uid": "test-uuid-1234",
            "version": "1.9.0",
            "logged_time": 1700000000000,
            "product": {
                "name": "ULPF",
                "vendor_name": "ULPF"
            }
        },
        "src_endpoint": {
            "ip": "192.168.1.1",
            "port": "443"  # STRING PORT MUST FAIL VALIDATION
        }
    }
    with pytest.raises(ValueError) as excinfo:
        validate_event(invalid_event)
    assert "OCSF validation failed" in str(excinfo.value)


def test_phase0_rejects_misspelled_endpoint_property():
    invalid_event = {
        "class_uid": 4001,
        "category_uid": 4,
        "activity_id": 1,
        "type_uid": 400101,
        "time": 1700000000000,
        "severity_id": 1,
        "metadata": {
            "uid": "test-uuid-1234",
            "version": "1.9.0",
            "logged_time": 1700000000000,
            "product": {"name": "ULPF", "vendor_name": "ULPF"},
        },
        "src_endpoint": {"ip": "192.168.1.1", "ipp": "192.168.1.1"},
    }
    with pytest.raises(ValueError, match="OCSF validation failed"):
        validate_event(invalid_event)
