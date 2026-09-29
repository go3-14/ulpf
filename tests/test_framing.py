from ingest.framing import LineJoiner

def test_line_joiner_groups_started_records():
    joiner = LineJoiner(r"^<Event")
    assert joiner.push(b"<Event>") == []
    assert joiner.push(b"body") == []
    assert joiner.push(b"<Event>") == [b"<Event>\nbody"]
