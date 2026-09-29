from ingest.pipeline import process


def test_unknown_input_emits_fallback_event(monkeypatch, tmp_path):
    import config
    monkeypatch.setattr(config, "STORAGE_DIR", tmp_path)
    event_id = process(b"not a recognized record")
    assert event_id
