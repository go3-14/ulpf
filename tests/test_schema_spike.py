from __future__ import annotations

import pathlib
import sys

import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_event


def valid_network_activity() -> dict:
    """A hand-written minimal OCSF Network Activity event for the Phase 0 gate."""
    return {
        "activity_id": 6,
        "category_uid": 4,
        "class_uid": 4001,
        "metadata": {
            "uid": "2b6c6ef8-9c15-4d18-9b17-f75be960c6ce",
            "version": "1.9.0",
            "product": {"name": "ULPF", "vendor_name": "ULPF"},
        },
        "severity_id": 1,
        "time": 1_789_724_800_000,
        "type_uid": 400106,
        "src_endpoint": {"ip": "192.0.2.10", "port": 443},
    }


def test_hand_written_valid_event_passes() -> None:
    validate_event(valid_network_activity())


def test_string_port_fails_validation() -> None:
    event = valid_network_activity()
    event["src_endpoint"]["port"] = "443"

    with pytest.raises(ValueError, match="src_endpoint.port"):
        validate_event(event)
