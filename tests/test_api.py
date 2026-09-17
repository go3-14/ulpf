from __future__ import annotations

import pathlib
import shutil

import storage.index as index_module
import storage.normalized_store as normalized_module
import storage.writer as writer_module
from api.main import app
from fastapi.testclient import TestClient
from ingest import pipeline
from mappings.loader import MAPPINGS_DIR


def test_api_endpoints(tmp_path, monkeypatch):
    monkeypatch.setattr(writer_module, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(index_module, "_INDEX_PATH", tmp_path / "index" / "raw_index.ndjson")
    monkeypatch.setattr(normalized_module, "STORAGE_DIR", tmp_path)
    index_module._INDEX.clear()
    normalized_module._EVENTS.clear()
    pipeline.reload_mappings()
    client = TestClient(app)
    raw = b'<164>Dec 27 14:58:25 asa-fw %ASA-4-106023: Deny tcp src outside:10.65.63.155/56166 dst inside:10.5.0.30/8000\n'

    health = client.get("/health")
    assert health.status_code == 200 and health.json()["mappings_loaded"] >= 4
    ingested = client.post("/ingest", content=raw)
    assert ingested.status_code == 200
    event_id = ingested.json()["event_ids"][0]
    normalized = client.get(f"/events/{event_id}")
    assert normalized.status_code == 200 and normalized.json()["metadata"]["uid"] == event_id
    raw_response = client.get(f"/events/{event_id}/raw")
    assert raw_response.status_code == 200 and raw_response.content == raw
    assert client.get("/events/00000000-0000-0000-0000-000000000000").status_code == 404

    cef_line = (pathlib.Path(__file__).parents[1] / "samples" / "paloalto_cef.log").read_bytes().splitlines(keepends=True)[0]
    client.post("/ingest", content=cef_line)
    cef_results = client.get("/events", params={"format": "cef"})
    assert cef_results.status_code == 200
    assert all(event["metadata"]["labels"][2] == "cef" for event in cef_results.json()["events"])

    mapping_copy = tmp_path / "mappings"
    shutil.copytree(MAPPINGS_DIR, mapping_copy)
    (mapping_copy / "extra.yaml").write_text((mapping_copy / "cisco_asa.yaml").read_text(encoding="utf-8").replace("source: cisco_asa", "source: extra"), encoding="utf-8")
    reloaded = client.post("/mappings/reload", params={"directory": str(mapping_copy)})
    assert reloaded.status_code == 200 and reloaded.json()["mappings_loaded"] == 5
    pipeline.reload_mappings()
