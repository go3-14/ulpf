import json
import threading

from storage.writer import PartitionedNDJSONWriter


def test_writer_concurrency(tmp_path):
    writer = PartitionedNDJSONWriter("normalized", "events", root=tmp_path)

    def write_many(start):
        for i in range(100):
            writer.write("source", {"n": start + i})

    threads = [threading.Thread(target=write_many, args=(i * 100,)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    writer.close_all()

    rows = []
    for path in tmp_path.rglob("*.ndjson"):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    assert len(rows) == 500
