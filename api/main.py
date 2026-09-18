from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from ingest import metrics
from ingest.pipeline import process, reload_mappings, MAPPINGS
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
            eid = process(line.encode("utf-8"))
            if eid:
                event_ids.append(eid)
    return {"processed": len(event_ids), "event_ids": event_ids}

@app.post("/mappings/reload")
def reload_mappings_endpoint():
    count = reload_mappings()
    return {"status": "reloaded", "mappings_count": count}
