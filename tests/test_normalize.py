from schema.normalize import normalize


def _config():
    return {
        "ocsf": {"class_uid": 4001, "category_uid": 4},
        "field_map": {
            "empty": {"to": "message", "type": "str"},
            "spaces": {"to": "activity_name", "type": "str"},
            "none": {"to": "user.name", "type": "str"},
            "normal": {"to": "metadata.product.name", "type": "str"},
            "null_transform": {"to": "metadata.product.vendor_name", "type": "str"},
        },
        "defaults": {"activity_id": 1, "severity_id": 1},
    }


def test_empty_values_remain_unmapped_and_normal_values_are_consumed():
    parsed = {
        "empty": "",
        "spaces": "   ",
        "none": None,
        "normal": "mapped",
    }

    event = normalize(parsed, _config(), "event-1", "source", "json")

    assert event["metadata"]["product"]["name"] == "mapped"
    assert event["unmapped"] == {"empty": "", "spaces": "   ", "none": None}


def test_transform_returning_none_does_not_consume_source(monkeypatch):
    monkeypatch.setattr("schema.normalize.apply_transform", lambda value, spec: None)
    parsed = {"null_transform": "present"}

    event = normalize(parsed, _config(), "event-2", "source", "json")

    assert event["unmapped"] == {"null_transform": "present"}


def test_consumed_and_unmapped_partition_parsed_keys():
    parsed = {"normal": "mapped", "unmapped": "leftover", "empty": ""}
    event = normalize(parsed, _config(), "event-3", "source", "json")

    assert set(parsed) == {"normal"} | set(event["unmapped"])
