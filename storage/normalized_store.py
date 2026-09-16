import json
from pathlib import Path

from config import STORAGE_DIR
from storage.index import add_normalized_index, get_normalized_location
from storage.writer import PartitionedNDJSONWriter, read_record_at


NORMALIZED_WRITER = PartitionedNDJSONWriter("normalized", "events")


def store_normalized(event_id: str, event: dict, source_id: str) -> tuple[str, int, int]:
    record = {"event_id": event_id, "event": event}
    path, offset, length = NORMALIZED_WRITER.write(source_id, record)
    add_normalized_index(event_id, path, offset, length)
    return path, offset, length


def read_normalized(event_id: str) -> dict:
    loc = get_normalized_location(event_id)
    if loc is None:
        raise KeyError(event_id)
    return read_record_at(*loc)["event"]


def search(**filters) -> list[dict]:
    limit = int(filters.pop("limit", 50) or 50)
    root = STORAGE_DIR / "normalized"
    results = []
    if not root.exists():
        return results
    for path in sorted(root.rglob("*.ndjson")):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                rec = json.loads(line)
                event = rec["event"]
                if _matches(event, filters):
                    results.append({"event_id": rec["event_id"], "event": event})
                    if len(results) >= limit:
                        return results
    return results


def _matches(event: dict, filters: dict) -> bool:
    labels = event.get("metadata", {}).get("labels", [])
    checks = {
        "source": labels[1] if len(labels) > 1 else None,
        "format": labels[2] if len(labels) > 2 else None,
        "src_ip": event.get("src_endpoint", {}).get("ip"),
        "dst_ip": event.get("dst_endpoint", {}).get("ip"),
        "dst_port": event.get("dst_endpoint", {}).get("port"),
        "activity_id": event.get("activity_id"),
        "severity_id": event.get("severity_id"),
    }
    since = filters.get("since")
    until = filters.get("until")
    if since and event.get("time", 0) < int(since):
        return False
    if until and event.get("time", 0) > int(until):
        return False
    for key, expected in filters.items():
        if expected in (None, "") or key in ("since", "until"):
            continue
        actual = checks.get(key)
        if actual is None:
            return False
        if str(actual) != str(expected):
            return False
    return True
