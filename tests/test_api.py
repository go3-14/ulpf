from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_api_ingest_lookup_and_search():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["mappings_loaded"] >= 4

    raw = Path("samples/paloalto_cef.log").read_bytes().splitlines(True)[0]
    response = client.post("/ingest", content=raw)
    assert response.status_code == 200
    event_id = response.json()["event_ids"][0]
    assert event_id

    event_response = client.get(f"/events/{event_id}")
    assert event_response.status_code == 200
    assert event_response.json()["metadata"]["uid"] == event_id

    raw_response = client.get(f"/events/{event_id}/raw")
    assert raw_response.status_code == 200
    assert raw_response.content == raw

    assert client.get("/events/not-real").status_code == 404
    cef_rows = client.get("/events?format=cef").json()
    assert cef_rows
    assert all(row["event"]["metadata"]["labels"][2] == "cef" for row in cef_rows)
