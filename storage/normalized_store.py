import glob
import json
import pathlib
import config
from storage.writer import PartitionedNDJSONWriter

NORM_WRITER = PartitionedNDJSONWriter(subfolder="normalized")

def store_normalized(event_id: str, normalized: dict, source_id: str) -> tuple:
    return NORM_WRITER.write(source_id, normalized, prefix="events")

def get_normalized(event_id: str) -> dict | None:
    results = search_normalized(limit=10000)
    for ev in results:
        if ev.get("metadata", {}).get("uid") == event_id:
            return ev
    return None

def search_normalized(
    source: str | None = None,
    fmt: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    dst_port: int | None = None,
    activity_id: int | None = None,
    severity_id: int | None = None,
    limit: int = 50
) -> list[dict]:
    norm_dir = pathlib.Path(config.STORAGE_DIR) / "normalized"
    if not norm_dir.exists():
        return []


    results = []
    files = sorted(glob.glob(str(norm_dir / "**" / "*.ndjson"), recursive=True), reverse=True)

    for fpath in files:
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
                    if activity_id is not None and ev.get("activity_id") != activity_id:
                        continue
                    if severity_id is not None and ev.get("severity_id") != severity_id:
                        continue

                    results.append(ev)
                    if len(results) >= limit:
                        return results
        except Exception:
            continue

    return results

def reset_writers():
    NORM_WRITER.close_all()

