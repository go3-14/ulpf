from fastapi.testclient import TestClient


def test_provenance_endpoint_returns_ingest_metadata(monkeypatch):
    import api.main as main
    monkeypatch.setattr(main, "get_record", lambda event_id: {
        "event_id": event_id, "origin": "file", "origin_id": "x#abc",
        "origin_offset": 4, "origin_line": 3, "mapping_id": "src",
        "mapping_version": "1.0", "mapping_sha256": "sha", "raw_sha256": "raw",
    })
    response = TestClient(main.app).get("/events/e1/provenance")
    assert response.status_code == 200
    body = response.json()
    assert body["origin_id"] == "x#abc"
    assert body["ulpf_version"] == "3.0.0"
