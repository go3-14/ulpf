from mappings.loader import load_mappings


def test_loader_exposes_file_identity_and_defaults(tmp_path):
    path = tmp_path / "example.yaml"
    path.write_text("source: example\nformat: json\nfield_map: {}\n", encoding="utf-8")
    mapping = load_mappings(tmp_path)["example"]
    assert mapping.version == "1"
    assert mapping.id == "example"
    assert len(mapping.sha256) == 64


def test_loader_metadata_changes_when_file_changes(tmp_path):
    path = tmp_path / "example.yaml"
    path.write_text("source: example\nformat: json\nfield_map: {}\n", encoding="utf-8")
    first = load_mappings(tmp_path)["example"].sha256
    path.write_text("source: example\nversion: '2'\nformat: json\nfield_map: {}\n", encoding="utf-8")
    mapping = load_mappings(tmp_path)["example"]
    assert mapping.version == "2"
    assert mapping.sha256 != first
