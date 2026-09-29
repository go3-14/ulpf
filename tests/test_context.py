from ingest.context import IngestContext


def test_ingest_context_defaults_are_explicit_and_safe():
    ctx = IngestContext(origin="file")
    assert ctx.origin == "file"
    assert ctx.origin_id == ""
    assert ctx.offset is None
    assert ctx.line_no is None
    assert ctx.received_ms == 0
    assert ctx.reference_ms is None
    assert ctx.seq == 0
    assert ctx.source_hint is None
    assert ctx.file_state == {}


def test_context_isolated_file_state():
    first = IngestContext(origin="file")
    first.file_state["fingerprint"] = "abc"
    second = IngestContext(origin="file")
    assert second.file_state == {}
