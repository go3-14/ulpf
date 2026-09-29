import glob
import json
import pathlib
import config
import ipaddress
from collections import OrderedDict
from storage.writer import PartitionedNDJSONWriter

NORM_WRITER = PartitionedNDJSONWriter(subfolder="normalized")

# In-memory event cache: event_id -> normalized OCSF dict
# Provides O(1) lookup for GET /events/{id} for events ingested in this process lifetime.
_EVENTS: "OrderedDict[str, dict]" = OrderedDict()

def _cache_put(event_id: str, event: dict) -> None:
    _EVENTS.pop(event_id, None)
    _EVENTS[event_id] = event
    while len(_EVENTS) > getattr(config, "NORMALIZED_CACHE_MAX", 10000):
        _EVENTS.popitem(last=False)


def store_normalized(event_id: str, normalized: dict, source_id: str) -> tuple:
    _cache_put(event_id, normalized)
    return NORM_WRITER.write(source_id, normalized, prefix="events")


def get_normalized(event_id: str) -> dict | None:
    # O(1) path — in-memory hit
    if event_id in _EVENTS:
        _EVENTS.move_to_end(event_id)
        return _EVENTS[event_id]

    # O(n) fallback — scan disk for events from a previous process run
    norm_dir = pathlib.Path(config.STORAGE_DIR) / "normalized"
    if not norm_dir.exists():
        return None
    for fpath in glob.glob(str(norm_dir / "**" / "*.ndjson"), recursive=True):
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    ev = json.loads(line)
                    if ev.get("metadata", {}).get("uid") == event_id:
                        _cache_put(event_id, ev)  # populate cache for next call
                        return ev
        except Exception:
            continue
    return None


def search_normalized(
    source: str | None = None,
    fmt: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    dst_port: int | None = None,
    src_port: int | None = None,
    user: str | None = None,
    class_uid: int | None = None,
    q: str | None = None,
    cursor: int = 0,
    activity_id: int | None = None,
    severity_id: int | None = None,
    since: int | None = None,
    until: int | None = None,
    limit: int = 50
) -> list[dict]:
    norm_dir = pathlib.Path(config.STORAGE_DIR) / "normalized"
    if not norm_dir.exists():
        return []

    results = []
    skipped = 0
    files = sorted(glob.glob(str(norm_dir / "**" / "*.ndjson"), recursive=True), reverse=True)

    for fpath in files:
        # Fast partition pruning: skip file if source filter can't match this path
        if source and f"source={source}" not in fpath:
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    ev = json.loads(line)
                    meta = ev.get("metadata", {})
                    labels = meta.get("labels", [])

                    if source and source not in labels:
                        continue
                    if fmt and fmt not in labels:
                        continue
                    if src_ip and ev.get("src_endpoint", {}).get("ip") != src_ip:
                        continue
                    if dst_ip and ev.get("dst_endpoint", {}).get("ip") != dst_ip:
                        continue
                    if dst_port is not None and ev.get("dst_endpoint", {}).get("port") != dst_port:
                        continue
                    if src_port is not None and ev.get("src_endpoint", {}).get("port") != src_port:
                        continue
                    if user and user not in str(ev.get("user_name", ev.get("user", ""))):
                        continue
                    if class_uid is not None and ev.get("class_uid") != class_uid:
                        continue
                    if q and q not in str(ev.get("message", "")):
                        continue
                    if activity_id is not None and ev.get("activity_id") != activity_id:
                        continue
                    if severity_id is not None and ev.get("severity_id") != severity_id:
                        continue
                    if since is not None and ev.get("time", 0) < since:
                        continue
                    if until is not None and ev.get("time", 0) > until:
                        continue

                    if skipped < cursor:
                        skipped += 1
                        continue
                    results.append(ev)
                    if len(results) >= limit:
                        return results
        except Exception:
            continue

    return results


def reset_writers():
    """Close all writers and clear the in-memory cache. Used by tests for isolation."""
    _EVENTS.clear()
    NORM_WRITER.close_all()
