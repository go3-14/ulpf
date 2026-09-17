from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from config import STORAGE_DIR
from storage.writer import PartitionedNDJSONWriter

NORMALIZED_WRITER = PartitionedNDJSONWriter("normalized")
_EVENTS: dict[str, dict] = {}


def store_normalized(event_id: str, event: dict, source_id: str) -> None:
    _EVENTS[event_id] = event
    NORMALIZED_WRITER.write(source_id, {"event_id": event_id, "source_id": source_id, "event": event})


def get_normalized(event_id: str) -> dict:
    if event_id in _EVENTS:
        return _EVENTS[event_id]
    for path in (STORAGE_DIR / "normalized").rglob("*.ndjson"):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("event_id") == event_id:
                    _EVENTS[event_id] = row["event"]
                    return row["event"]
    raise KeyError(event_id)


def search(**filters) -> list[dict]:
    results = []
    for path in (STORAGE_DIR / "normalized").rglob("*.ndjson"):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)["event"]
                except (json.JSONDecodeError, KeyError):
                    continue
                labels = event.get("metadata", {}).get("labels", [])
                if filters.get("source") and filters["source"] not in labels:
                    continue
                if filters.get("format") and filters["format"] not in labels:
                    continue
                if filters.get("src_ip") is not None and filters["src_ip"] != event.get("src_endpoint", {}).get("ip"):
                    continue
                if filters.get("dst_ip") is not None and filters["dst_ip"] != event.get("dst_endpoint", {}).get("ip"):
                    continue
                if filters.get("dst_port") is not None and filters["dst_port"] != event.get("dst_endpoint", {}).get("port"):
                    continue
                if filters.get("activity_id") is not None and filters["activity_id"] != event.get("activity_id"):
                    continue
                if filters.get("severity_id") is not None and filters["severity_id"] != event.get("severity_id"):
                    continue
                if filters.get("since") is not None and event.get("time", 0) < filters["since"]:
                    continue
                if filters.get("until") is not None and event.get("time", 0) > filters["until"]:
                    continue
                results.append(event)
                if len(results) >= filters.get("limit", 50):
                    return results
    return results
