from __future__ import annotations

import json
import pathlib
import threading

from config import STORAGE_DIR

_INDEX: dict[str, tuple[str, int, int]] = {}
_INDEX_PATH = STORAGE_DIR / "index" / "raw_index.ndjson"
_LOCK = threading.Lock()


def rebuild() -> None:
    if not _INDEX_PATH.exists():
        return
    with _INDEX_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
                _INDEX[row["event_id"]] = (row["path"], int(row["offset"]), int(row["length"]))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue


rebuild()


def add_index(event_id: str, path: str, offset: int, length: int) -> None:
    with _LOCK:
        _INDEX[event_id] = (path, offset, length)
        _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _INDEX_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"event_id": event_id, "path": path, "offset": offset, "length": length}) + "\n")


def get_index(event_id: str):
    return _INDEX.get(event_id)
