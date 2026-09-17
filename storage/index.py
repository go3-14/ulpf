from __future__ import annotations

import json
import pathlib

from storage.writer import DATA_ROOT

_INDEX: dict[str, tuple[str, int, int]] = {}
_INDEX_PATH = DATA_ROOT / "index" / "raw_index.ndjson"


def add_index(event_id: str, path: str, offset: int, length: int) -> None:
    _INDEX[event_id] = (path, offset, length)
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _INDEX_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event_id": event_id, "path": path, "offset": offset, "length": length}) + "\n")


def get_index(event_id: str):
    return _INDEX.get(event_id)
