from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from config import STORAGE_DIR

DATA_ROOT = STORAGE_DIR
_WRITERS: list["PartitionedNDJSONWriter"] = []


class PartitionedNDJSONWriter:
    def __init__(self, kind: str):
        self.kind = kind
        self._handles: dict[tuple[str, str], object] = {}
        self._counts: dict[tuple[str, str], int] = {}
        self._locks: dict[tuple[str, str], threading.Lock] = {}
        self._locks_guard = threading.Lock()
        _WRITERS.append(self)

    def _partition_lock(self, key: tuple[str, str]) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(key, threading.Lock())

    def write(self, partition: str, record: dict) -> tuple[str, int, int]:
        day = time.strftime("%Y-%m-%d", time.gmtime())
        directory = DATA_ROOT / self.kind / f"dt={day}" / f"source={partition}"
        directory.mkdir(parents=True, exist_ok=True)
        key = (day, partition)
        with self._partition_lock(key):
            count = self._counts.get(key, 0) + 1
            self._counts[key] = count
            path = directory / f"{self.kind}-{((count - 1) // 10000) + 1:04d}.ndjson"
            handle_key = (str(path), partition)
            handle = self._handles.get(handle_key)
            if handle is None:
                handle = open(path, "a+", encoding="utf-8")
                self._handles[handle_key] = handle
            handle.seek(0, os.SEEK_END)
            offset = handle.tell()
            line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            handle.write(line)
            handle.flush()
            return str(path), offset, len(line.encode("utf-8"))

    def flush(self) -> None:
        for handle in self._handles.values():
            handle.flush()

    def close(self) -> None:
        for handle in self._handles.values():
            handle.flush()
            handle.close()
        self._handles.clear()


def flush_all() -> None:
    for writer in _WRITERS:
        writer.close()
