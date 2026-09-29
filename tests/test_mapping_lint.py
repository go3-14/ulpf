import pytest
from mappings.loader import load_mappings


def test_loader_rejects_invalid_extract_regex(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        "source: bad\nformat: json\nfield_map: {}\nextract:\n  - regex: '[unclosed'\n", encoding="utf-8")
    with pytest.raises(ValueError, match="regex"):
        load_mappings(tmp_path)


def test_loader_rejects_unknown_transform(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        "source: bad\nformat: json\nfield_map:\n  x: {to: message, type: made_up}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="transform"):
        load_mappings(tmp_path)
