from pathlib import Path

from ingest.pipeline import process
from storage.normalized_store import read_normalized


def test_all_sample_files_process_good_lines_and_deadletter_bad_lines():
    successes = []
    failures = 0
    for path in Path("samples").glob("*.log"):
        for line in path.read_bytes().splitlines(keepends=True):
            event_id = process(line)
            if event_id:
                successes.append(event_id)
            else:
                failures += 1
    assert len(successes) >= 10
    assert failures >= 4
    event = read_normalized(successes[0])
    assert event["metadata"]["uid"] == successes[0]
    assert event["type_uid"] == event["class_uid"] * 100 + event["activity_id"]
