import atexit
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from config import STORAGE_DIR


class PartitionedNDJSONWriter:
    def __init__(self, kind: str, prefix: str, root: Path | None = None, rotate_bytes: int = 64 * 1024 * 1024):
        self.kind = kind
        self.prefix = prefix
        self.root = root or STORAGE_DIR
        self.rotate_bytes = rotate_bytes
        self._lock = threading.Lock()
        self._handles = {}
        self._counts = {}
        self._last_flush = time.time()
        atexit.register(self.flush_all)

    def _partition_dir(self, source_id: str | None) -> Path:
        dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if source_id:
            return self.root / self.kind / f"dt={dt}" / f"source={source_id}"
        return self.root / self.kind / f"dt={dt}"

    def _open_handle(self, source_id: str | None):
        part_dir = self._partition_dir(source_id)
        part_dir.mkdir(parents=True, exist_ok=True)
        key = str(part_dir)
        handle = self._handles.get(key)
        if handle and handle.tell() < self.rotate_bytes:
            return handle

        if handle:
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()

        seq = self._counts.get(key, 1)
        while True:
            path = part_dir / f"{self.prefix}-{seq:04d}.ndjson"
            if not path.exists() or path.stat().st_size < self.rotate_bytes:
                break
            seq += 1
        self._counts[key] = seq
        handle = open(path, "ab")
        handle.seek(0, os.SEEK_END)
        self._handles[key] = handle
        return handle

    def write(self, source_id: str | None, record: dict) -> tuple[str, int, int]:
        data = (json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        with self._lock:
            handle = self._open_handle(source_id)
            offset = handle.tell()
            handle.write(data)
            handle.flush()
            self._last_flush = time.time()
            return str(Path(handle.name)), offset, len(data)

    def flush_all(self):
        with self._lock:
            for handle in list(self._handles.values()):
                try:
                    handle.flush()
                    os.fsync(handle.fileno())
                except OSError:
                    pass

    def close_all(self):
        with self._lock:
            for handle in list(self._handles.values()):
                try:
                    handle.flush()
                    os.fsync(handle.fileno())
                    handle.close()
                except OSError:
                    pass
            self._handles.clear()


def read_record_at(path: str, offset: int, length: int) -> dict:
    with open(path, "rb") as handle:
        handle.seek(offset)
        data = handle.read(length)
    return json.loads(data.decode("utf-8"))
