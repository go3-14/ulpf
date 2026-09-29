from ingest.context import IngestContext
from ingest.identity import event_id_for


def test_file_identity_is_stable_for_same_offset_and_bytes():
    ctx = IngestContext(origin="file", origin_id="sample.log#deadbeef", offset=0)
    assert event_id_for(b"hello", ctx) == event_id_for(b"hello", ctx)


def test_file_identity_changes_with_offset():
    first = IngestContext(origin="file", origin_id="sample.log#deadbeef", offset=0)
    second = IngestContext(origin="file", origin_id="sample.log#deadbeef", offset=100)
    assert event_id_for(b"hello", first) != event_id_for(b"hello", second)


def test_network_identity_uses_received_time_and_sequence():
    first = IngestContext(origin="udp", received_ms=10, seq=1)
    second = IngestContext(origin="udp", received_ms=10, seq=2)
    assert event_id_for(b"hello", first) != event_id_for(b"hello", second)
