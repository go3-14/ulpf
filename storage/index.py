import json
import threading
from pathlib import Path

from config import STORAGE_DIR


_lock = threading.Lock()
_raw_index = {}
_normalized_index = {}


def _index_path(name: str) -> Path:
    path = STORAGE_DIR / "index"
    path.mkdir(parents=True, exist_ok=True)
    return path / name


def _append(name: str, record: dict) -> None:
    path = _index_path(name)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")


def add_index(event_id: str, path: str, offset: int, length: int) -> None:
    record = {"event_id": event_id, "path": path, "offset": offset, "length": length}
    with _lock:
        _raw_index[event_id] = (path, offset, length)
        _append("raw_index.ndjson", record)


def add_normalized_index(event_id: str, path: str, offset: int, length: int) -> None:
    record = {"event_id": event_id, "path": path, "offset": offset, "length": length}
    with _lock:
        _normalized_index[event_id] = (path, offset, length)
        _append("normalized_index.ndjson", record)


def get_raw_location(event_id: str):
    with _lock:
        return _raw_index.get(event_id)


def get_normalized_location(event_id: str):
    with _lock:
        return _normalized_index.get(event_id)


def rebuild() -> None:
    with _lock:
        _raw_index.clear()
        _normalized_index.clear()
        for filename, target in (("raw_index.ndjson", _raw_index), ("normalized_index.ndjson", _normalized_index)):
            path = _index_path(filename)
            if not path.exists():
                continue
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    target[rec["event_id"]] = (rec["path"], rec["offset"], rec["length"])
