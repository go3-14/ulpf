from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import storage.writer as writer_module
from storage.writer import PartitionedNDJSONWriter


def test_same_partition_writes_are_complete_json(tmp_path, monkeypatch):
    monkeypatch.setattr(writer_module, "DATA_ROOT", tmp_path)
    writer = PartitionedNDJSONWriter("concurrency")

    def write_one(index):
        writer.write("same-source", {"index": index, "payload": "x" * 80})

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(write_one, range(240)))
    writer.close()
    files = list((tmp_path / "concurrency").rglob("*.ndjson"))
    rows = [json.loads(line) for path in files for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 240
    assert {row["index"] for row in rows} == set(range(240))
