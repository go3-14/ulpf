from ingest.coverage import record, report

def test_coverage_report_tracks_unmapped_keys():
    record("x", {"a": 1, "b": 2}, {"a": 1})
    assert report("x")["x"]["top_unmapped"][0][0] == "b"
