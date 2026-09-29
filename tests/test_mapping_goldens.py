from scripts.test_mappings import _get_path


def test_mapping_golden_path_lookup():
    assert _get_path({"a": {"b": 3}}, "a.b") == 3
