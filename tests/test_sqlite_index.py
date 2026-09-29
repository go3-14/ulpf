import importlib


def test_index_uses_sqlite_and_exposes_provenance(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "STORAGE_DIR", tmp_path)
    import storage.index as index
    importlib.reload(index)
    assert index.add_index("e1", str(tmp_path / "raw.ndjson"), 3, 9,
                           origin="file", origin_id="x#abc", origin_offset=3,
                           origin_line=2, raw_sha256="deadbeef") is True
    row = index.get_record("e1")
    assert row["origin"] == "file"
    assert row["origin_id"] == "x#abc"
    assert row["raw_sha256"] == "deadbeef"
    assert (tmp_path / "index" / "index.sqlite3").exists()
