def test_normalized_cache_is_bounded(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(config, "NORMALIZED_CACHE_MAX", 2, raising=False)
    import storage.normalized_store as store
    store.reset_writers()
    store._EVENTS.clear()
    for i in range(3):
        store.store_normalized(f"e{i}", {"metadata": {"uid": f"e{i}"}}, "src")
    assert len(store._EVENTS) <= 2
    assert store.get_normalized("e2")["metadata"]["uid"] == "e2"
