from storage import normalized_store


def test_normalized_cache_and_disk_fallback_with_time_filters(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", tmp_path / "storage")
    normalized_store.reset_writers()
    event = {
        "metadata": {"uid": "event-1", "labels": ["source-a", "json"]},
        "time": 100,
        "src_endpoint": {"ip": "192.0.2.1"},
    }
    normalized_store.store_normalized("event-1", event, "source-a")
    assert normalized_store.get_normalized("event-1") is event

    normalized_store._EVENTS.clear()
    assert normalized_store.get_normalized("event-1")["metadata"]["uid"] == "event-1"
    assert normalized_store.search_normalized(source="source-a", since=100, until=100) == [event]
    assert normalized_store.search_normalized(since=101) == []
    normalized_store.reset_writers()
