import pathlib
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mappings_loaded"] >= 4

def test_api_ingest_lookup_raw_flow(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", tmp_path / "storage")
    import storage.raw_store
    import storage.normalized_store
    import storage.index
    storage.raw_store.reset_writers()
    storage.normalized_store.reset_writers()
    storage.index._index_loaded = False
    storage.index._index_map.clear()

    sample_line = "<134>Jan 10 10:00:00 fw01 %ASA-6-302013: Built inbound TCP connection 12345 for outside:192.168.1.50/49152 to inside:10.0.0.5/80"
    
    # 1. POST /ingest
    res = client.post("/ingest", json={"logs": sample_line})
    assert res.status_code == 200
    data = res.json()
    assert data["processed"] == 1
    event_id = data["event_ids"][0]

    # 2. GET /events/{id}
    res_ev = client.get(f"/events/{event_id}")
    assert res_ev.status_code == 200
    ev_data = res_ev.json()
    assert ev_data["metadata"]["uid"] == event_id
    assert ev_data["class_uid"] == 4001

    # 3. GET /events/{id}/raw
    res_raw = client.get(f"/events/{event_id}/raw")
    assert res_raw.status_code == 200
    assert res_raw.text == sample_line

    # 4. GET /events/{bad_id} (404)
    res_bad = client.get("/events/00000000-0000-0000-0000-000000000000")
    assert res_bad.status_code == 404

def test_api_search_and_reload():
    res_search = client.get("/events?format=cef")
    assert res_search.status_code == 200
    assert isinstance(res_search.json(), list)

    res_reload = client.post("/mappings/reload")
    assert res_reload.status_code == 200
    assert res_reload.json()["mappings_count"] >= 4
