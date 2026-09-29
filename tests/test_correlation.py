from ingest.correlation import correlate

def test_correlate_groups_sources():
    events = [{"time": 1000, "src_endpoint": {"ip": "1.2.3.4"}, "metadata": {"uid": "a", "labels": ["source:ssh"]}},
              {"time": 2000, "src_endpoint": {"ip": "1.2.3.4"}, "metadata": {"uid": "b", "labels": ["source:fw"]}}]
    assert correlate(events)[0]["key"] == "1.2.3.4"
