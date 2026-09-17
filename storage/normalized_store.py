from __future__ import annotations

import json

from storage.writer import PartitionedNDJSONWriter

NORMALIZED_WRITER = PartitionedNDJSONWriter("normalized")
_EVENTS: dict[str, dict] = {}


def store_normalized(event_id: str, event: dict, source_id: str) -> None:
    _EVENTS[event_id] = event
    NORMALIZED_WRITER.write(source_id, {"event_id": event_id, "source_id": source_id, "event": event})


def get_normalized(event_id: str) -> dict:
    if event_id not in _EVENTS:
        raise KeyError(event_id)
    return _EVENTS[event_id]

