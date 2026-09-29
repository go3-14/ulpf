from exports.exporters import event_to_flat, export_es_bulk, export_splunk_hec


def _event():
    return {"class_uid": 4001, "time": 1700000000000, "severity_id": 1,
            "message": "deny", "metadata": {"uid": "e1", "labels": ["source:fw"]}}


def test_flat_and_stream_exports(tmp_path):
    assert event_to_flat(_event())["event_id"] == "e1"
    es = tmp_path / "events.ndjson"
    export_es_bulk([_event()], es)
    assert len(es.read_text(encoding="utf-8").splitlines()) == 2
    hec = tmp_path / "hec.ndjson"
    export_splunk_hec([_event()], hec)
    assert '"event"' in hec.read_text(encoding="utf-8")
