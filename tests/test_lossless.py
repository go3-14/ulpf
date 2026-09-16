from ingest.pipeline import process
from storage.raw_store import read_raw


def test_read_raw_returns_identical_bytes():
    raw = b"<166>Jan 10 10:00:00 asa-fw %ASA-6-302013: Built tcp src outside:192.0.2.10/123 dst inside:198.51.100.20/443\n"
    event_id = process(raw)
    assert event_id
    assert read_raw(event_id) == raw
