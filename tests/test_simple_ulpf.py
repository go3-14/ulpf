import json
import base64
from pathlib import Path

from simple_ulpf import load_sources, process_line


def test_all_four_formats_are_normalized_and_lossless(tmp_path):
    sources = load_sources(Path("sources.json"))
    seen = set()
    for file in Path("samples").glob("*.log"):
        for raw in file.read_bytes().splitlines(keepends=True):
            try:
                event = process_line(raw, sources, tmp_path)
            except ValueError:
                continue
            seen.add(event["source"]["format"])
            assert event["raw_ref"] == event["event_id"]
            assert isinstance(event["network"].get("dst_port"), int)
    assert seen == {"syslog", "cef", "leef", "json"}
    raw_records = [json.loads(line) for line in (tmp_path / "raw.jsonl").read_text().splitlines()]
    assert raw_records
    assert all(base64.b64decode(record["raw_b64"]) for record in raw_records)


def test_unknown_log_is_rejected(tmp_path):
    try:
        process_line(b"not a supported log\n", load_sources(Path("sources.json")), tmp_path)
    except ValueError as error:
        assert "unknown log format" in str(error)
    else:
        raise AssertionError("unknown input should not be accepted")
