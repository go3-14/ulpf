from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from ingest import metrics
from ingest.pipeline import process, reload_mappings, replay_failed, MAPPINGS, PARSERS
from ingest.context import IngestContext
from parsers.detect import detect_format
from schema.normalize import normalize
from schema.validate import validate_event
import pathlib
import re
import time
import yaml
from storage.normalized_store import get_normalized, search_normalized
from storage.raw_store import read_raw

app = FastAPI(title="ULPF - Universal Log Pre-processing Framework API", version="3.0.0")

class IngestRequest(BaseModel):
    logs: list[str] | str

@app.get("/health")
def health():
    return {"status": "ok", "mappings_loaded": len(MAPPINGS)}

@app.get("/events/{event_id}")
def get_event(event_id: str):
    ev = get_normalized(event_id)
    if not ev:
        raise HTTPException(status_code=404, detail=f"Event ID {event_id} not found")
    return ev

@app.get("/events/{event_id}/raw")
def get_event_raw(event_id: str):
    raw_bytes = read_raw(event_id)
    if not raw_bytes:
        raise HTTPException(status_code=404, detail=f"Raw log for Event ID {event_id} not found")
    return Response(content=raw_bytes, media_type="text/plain")

@app.get("/events")
def search_events(
    source: str | None = None,
    format: str | None = Query(None, alias="format"),
    src_ip: str | None = None,
    dst_ip: str | None = None,
    dst_port: int | None = None,
    activity_id: int | None = None,
    severity_id: int | None = None,
    since: int | None = None,
    until: int | None = None,
    limit: int = Query(50, ge=1, le=1000)
):
    results = search_normalized(
        source=source,
        fmt=format,
        src_ip=src_ip,
        dst_ip=dst_ip,
        dst_port=dst_port,
        activity_id=activity_id,
        severity_id=severity_id,
        since=since,
        until=until,
        limit=limit
    )
    return results

@app.get("/metrics")
def get_metrics_endpoint():
    return metrics.get_metrics()

@app.post("/ingest")
def ingest_logs(payload: IngestRequest):
    lines = [payload.logs] if isinstance(payload.logs, str) else payload.logs
    event_ids = []
    for line in lines:
        if line.strip():
            eid = process(line.encode("utf-8"), ctx=IngestContext(origin="http"))
            if eid:
                event_ids.append(eid)
    return {"processed": len(event_ids), "event_ids": event_ids}

@app.post("/mappings/reload")
def reload_mappings_endpoint():
    count = reload_mappings()
    return {"status": "reloaded", "mappings_count": count}

@app.get("/failed")
def failed_events(limit: int = Query(100, ge=1, le=1000)):
    from storage.failed import list_failed
    return list_failed(limit=limit)

@app.post("/replay")
def replay_events(limit: int | None = None):
    return {"recovered": replay_failed(limit=limit)}

@app.post("/onboarding/suggest")
def suggest_mapping(payload: dict):
    sample = str(payload.get("sample", "")).splitlines()[0]
    fmt = detect_format(sample)
    if not fmt or fmt not in PARSERS:
        raise HTTPException(400, "Could not detect sample format")
    parsed = PARSERS[fmt](sample) or {}
    return {"source": payload.get("source", "new_source"), "format": fmt,
            "mapping_version": "1.0.0",
            "ocsf": {"version": "1.9.0", "class_uid": 4001, "category_uid": 4},
            "defaults": {"activity_id": 6, "severity_id": 1},
            "field_map": {k: {"to": k, "type": "str"} for k in parsed}}

@app.post("/onboarding/test")
def test_mapping(payload: dict):
    mapping = payload.get("mapping")
    if isinstance(mapping, str):
        mapping = yaml.safe_load(mapping)
    samples = str(payload.get("sample", "")).splitlines()
    results = []
    started = time.perf_counter()
    for sample in samples:
        if not sample.strip(): continue
        fmt = detect_format(sample)
        parsed = PARSERS[fmt](sample) if fmt in PARSERS else None
        if not parsed: raise HTTPException(400, f"Could not parse sample as {fmt}")
        event = normalize(parsed, mapping, "mapping-test", mapping["source"], fmt)
        validate_event(event)
        results.append(event)
    return {"valid": True, "events": results, "elapsed_ms": round((time.perf_counter()-started)*1000, 2)}

@app.post("/onboarding/save")
def save_mapping(payload: dict):
    mapping = payload.get("mapping")
    if isinstance(mapping, str): mapping = yaml.safe_load(mapping)
    source = str(mapping.get("source", "new_source"))
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", source): raise HTTPException(400, "Invalid source id")
    path = pathlib.Path(__file__).parent.parent / "mappings" / f"{source}.yaml"
    path.write_text(yaml.safe_dump(mapping, sort_keys=False), encoding="utf-8")
    return {"saved": str(path), "mappings_count": reload_mappings()}
