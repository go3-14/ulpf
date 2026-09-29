import csv
import json
from datetime import datetime, timezone
from pathlib import Path

def _get(event, path):
    value = event
    for part in path.split('.'):
        if not isinstance(value, dict): return None
        value = value.get(part)
    return value

def event_to_flat(event):
    labels = _get(event, "metadata.labels") or []
    source = next((x.split(":", 1)[1] for x in labels if x.startswith("source:")), None)
    return {"event_id": _get(event, "metadata.uid"), "time": event.get("time"),
            "class_uid": event.get("class_uid"), "source_id": source,
            "severity_id": event.get("severity_id"), "message": event.get("message"),
            "unmapped_json": json.dumps(event.get("unmapped", {}), sort_keys=True),
            "fallback": any(x == "fallback:true" for x in labels)}

def export_es_bulk(events, output):
    with Path(output).open("w", encoding="utf-8", newline="\n") as fh:
        for event in events:
            eid = _get(event, "metadata.uid")
            cls = event.get("class_uid", 0)
            fh.write(json.dumps({"index": {"_index": f"ulpf-{cls}", "_id": eid}}) + "\n")
            copy = dict(event)
            if isinstance(copy.get("time"), int):
                copy["@timestamp"] = datetime.fromtimestamp(copy["time"] / 1000, timezone.utc).isoformat()
            fh.write(json.dumps(copy, ensure_ascii=False) + "\n")

def export_splunk_hec(events, output):
    with Path(output).open("w", encoding="utf-8", newline="\n") as fh:
        for event in events:
            labels = _get(event, "metadata.labels") or []
            source = next((x.split(":", 1)[1] for x in labels if x.startswith("source:")), "ulpf")
            fh.write(json.dumps({"time": event.get("time", 0) / 1000, "host": source,
                                "source": "ulpf", "sourcetype": f"ocsf:{event.get('class_uid', 0)}",
                                "event": event}, ensure_ascii=False) + "\n")

def export_csv_flat(events, output):
    rows = [event_to_flat(event) for event in events]
    fields = ["event_id", "time", "class_uid", "source_id", "severity_id", "message", "unmapped_json", "fallback"]
    with Path(output).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
