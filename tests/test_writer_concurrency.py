import json
import pathlib
import threading
from storage.writer import PartitionedNDJSONWriter

def test_writer_concurrency(tmp_path):
    writer = PartitionedNDJSONWriter(base_dir=tmp_path, subfolder="concurrent_test")
    threads = []
    num_threads = 10
    events_per_thread = 50

    def worker(thread_id):
        for i in range(events_per_thread):
            record = {
                "thread_id": thread_id,
                "seq": i,
                "payload": f"data-{thread_id}-{i}" * 10
            }
            writer.write("cisco_asa", record, prefix="events")

    for t_id in range(num_threads):
        t = threading.Thread(target=worker, args=(t_id,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    writer.flush_all()
    writer.close_all()

    # Verify all generated ndjson files parse line-by-line without corrupt lines
    ndjson_files = list(tmp_path.rglob("*.ndjson"))
    assert len(ndjson_files) > 0

    total_records = 0
    for fpath in ndjson_files:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)  # Will raise JSONDecodeError if lines were interleaved / corrupted
                assert "thread_id" in rec
                assert "seq" in rec
                total_records += 1

    assert total_records == num_threads * events_per_thread
