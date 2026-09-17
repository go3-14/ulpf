from __future__ import annotations

import pathlib

from ingest.pipeline import process
import storage.index as index_module
import storage.writer as writer_module
from storage.normalized_store import get_normalized
from storage.raw_store import read_raw


def test_real_cisco_sample_round_trips_and_validates(tmp_path, monkeypatch):
    monkeypatch.setattr(writer_module, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(index_module, "_INDEX_PATH", tmp_path / "index" / "raw_index.ndjson")
    index_module._INDEX.clear()
    sample = pathlib.Path(__file__).parents[1] / "samples" / "cisco_asa_syslog.log"
    lines = sample.read_bytes().splitlines(keepends=True)
    for raw in lines[:-1]:
        event_id = process(raw)
        assert event_id
        event = get_normalized(event_id)
        assert event["type_uid"] == event["class_uid"] * 100 + event["activity_id"]
        assert isinstance(event["src_endpoint"]["port"], int)
        assert isinstance(event["time"], int)
        assert event["metadata"]["uid"] == event_id
        assert event["unmapped"]
        assert read_raw(event_id) == raw

    assert process(lines[-1]) is None
