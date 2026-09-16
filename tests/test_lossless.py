import pathlib
from ingest.pipeline import process
from storage.raw_store import read_raw

def test_lossless_raw_retrieval(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", tmp_path)
    import storage.raw_store
    import storage.normalized_store
    import storage.index
    storage.raw_store.reset_writers()
    storage.normalized_store.reset_writers()
    storage.index._index_loaded = False
    storage.index._index_map.clear()


    raw_line = b"<134>Jan 10 10:00:00 fw01 %ASA-6-302013: Built inbound TCP connection 12345 for outside:192.168.1.50/49152 to inside:10.0.0.5/80"
    event_id = process(raw_line)
    assert event_id is not None

    stored_raw = read_raw(event_id)
    assert stored_raw == raw_line
