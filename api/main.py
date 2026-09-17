from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Request, Response

from ingest import metrics, pipeline
from storage.normalized_store import get_normalized, search
from storage.raw_store import read_raw

app = FastAPI(title="ULPF")


@app.get("/health")
def health():
    return {"status": "ok", "mappings_loaded": len(pipeline.MAPPINGS)}


@app.post("/ingest")
async def ingest(request: Request):
    body = await request.body()
    lines = body.splitlines(keepends=True) or [body]
    event_ids = [event_id for line in lines if (event_id := pipeline.process(line))]
    return {"event_ids": event_ids}


@app.get("/events/{event_id}")
def event(event_id: str):
    try:
        return get_normalized(event_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="event not found")


@app.get("/events/{event_id}/raw")
def raw_event(event_id: str):
    try:
        return Response(content=read_raw(event_id), media_type="text/plain")
    except KeyError:
        raise HTTPException(status_code=404, detail="event not found")


@app.get("/events")
def events(source: str | None = None, format: str | None = None, src_ip: str | None = None, dst_ip: str | None = None, dst_port: int | None = None, activity_id: int | None = None, severity_id: int | None = None, since: int | None = None, until: int | None = None, limit: int = Query(50, ge=1, le=1000)):
    return {"events": search(source=source, format=format, src_ip=src_ip, dst_ip=dst_ip, dst_port=dst_port, activity_id=activity_id, severity_id=severity_id, since=since, until=until, limit=limit)}


@app.get("/metrics")
def metrics_endpoint():
    return {"processed_total": metrics.processed_total, "failed_total": metrics.failed_total}


@app.post("/mappings/reload")
def mappings_reload(directory: str | None = None):
    return {"mappings_loaded": pipeline.reload_mappings(directory)}
