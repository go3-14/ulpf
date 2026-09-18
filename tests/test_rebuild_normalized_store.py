import json

import pytest

from scripts.rebuild_normalized_store import rebuild_normalized_store, replace_normalized_store
from schema.validate import validate_event


ASA_LINE = b"<134>Jan 10 10:00:00 fw01 %ASA-6-302013: Built inbound TCP connection 12345 for outside:192.168.1.50/49152 to inside:10.0.0.5/80"


def _write_raw(storage, event_id="stable-event-id", raw=ASA_LINE):
    path = storage / "raw" / "dt=2026-01-10" / "source=cisco_asa" / "raw-0001.ndjson"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "event_id": event_id,
                "raw": raw.decode("utf-8"),
                "raw_encoding": "utf-8",
                "source_id": "cisco_asa",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_rebuild_preserves_id_and_raw_payload(tmp_path):
    _write_raw(tmp_path)
    staging = tmp_path / ".rebuild"
    assert rebuild_normalized_store(tmp_path, staging) == 1
    output = staging / "normalized" / "dt=2026-01-10" / "source=cisco_asa" / "events-0001.ndjson"
    event = json.loads(output.read_text(encoding="utf-8"))
    assert event["metadata"]["uid"] == "stable-event-id"
    assert event["metadata"]["version"] == "1.9.0"
    validate_event(event)
    assert ASA_LINE == json.loads(
        (tmp_path / "raw" / "dt=2026-01-10" / "source=cisco_asa" / "raw-0001.ndjson").read_text()
    )["raw"].encode()


def test_rebuild_failure_does_not_replace_live_store(tmp_path):
    _write_raw(tmp_path, raw=b"not a recognized record")
    live = tmp_path / "normalized"
    live.mkdir()
    sentinel = live / "sentinel"
    sentinel.write_text("keep", encoding="utf-8")
    staging = tmp_path / ".rebuild"
    with pytest.raises(RuntimeError):
        rebuild_normalized_store(tmp_path, staging)
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not staging.exists()
