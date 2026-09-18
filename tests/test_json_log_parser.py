from parsers.json_log import parse_json


def test_json_nested_objects_and_arrays_flatten():
    parsed = parse_json('{"user":{"name":"alice"},"tags":["edge","web"],"items":[{"name":"dns"}]}')
    assert parsed == {"user.name": "alice", "tags": "edge,web", "items.0.name": "dns"}


def test_invalid_json_returns_none():
    assert parse_json("{not valid") is None
