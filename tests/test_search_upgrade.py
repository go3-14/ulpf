from storage.normalized_store import search_normalized


def test_search_supports_class_ports_query_and_cursor(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "STORAGE_DIR", tmp_path)
    import storage.normalized_store as store
    store.reset_writers()
    store.store_normalized("e1", {"class_uid": 4001, "time": 2, "message": "deny", "metadata": {"uid": "e1", "labels": ["source:fw"]}, "src_endpoint": {"port": 4}}, "fw")
    result = search_normalized(class_uid=4001, src_port=4, q="deny", limit=1)
    assert result[0]["metadata"]["uid"] == "e1"
