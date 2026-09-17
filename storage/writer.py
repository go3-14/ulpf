from __future__ import annotations

import json
import os
import pathlib
import threading
import time

DATA_ROOT = pathlib.Path(os.environ.get("ULPF_DATA_DIR", pathlib.Path(__file__).parents[1] / "storage_data"))


class PartitionedNDJSONWriter:
    def __init__(self, kind: str):
        self.kind = kind
        self._handles: dict[tuple[str, str], object] = {}
        self._counts: dict[tuple[str, str], int] = {}
        self._lock = threading.Lock()

    def write(self, partition: str, record: dict) -> tuple[str, int, int]:
        day = time.strftime("%Y-%m-%d", time.gmtime())
        directory = DATA_ROOT / self.kind / f"dt={day}" / f"source={partition}"
        directory.mkdir(parents=True, exist_ok=True)
        key = (day, partition)
        with self._lock:
            count = self._counts.get(key, 0) + 1
            self._counts[key] = count
            path = directory / f"{self.kind}-{((count - 1) // 10000) + 1:04d}.ndjson"
            handle = open(path, "a+", encoding="utf-8")
            handle.seek(0, os.SEEK_END)
            offset = handle.tell()
            line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            handle.write(line)
            handle.flush()
            return str(path), offset, len(line.encode("utf-8"))

    def flush(self) -> None:
        for handle in self._handles.values():
            handle.flush()

