from fastapi import FastAPI, HTTPException, Query, Request, Response

from ingest import metrics, pipeline
from storage.normalized_store import read_normalized, search
from storage.raw_store import read_raw


app = FastAPI(title="ULPF")


@app.get("/health")
def health():
    return {"status": "ok", "mappings_loaded": len(pipeline.MAPPINGS)}


@app.get("/events/{event_id}")
def get_event(event_id: str):
    try:
        return read_normalized(event_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="event not found")


@app.get("/events/{event_id}/raw")
def get_raw(event_id: str):
    try:
        raw = read_raw(event_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="event not found")
    return Response(content=raw, media_type="text/plain")


@app.get("/events")
def list_events(
    source: str | None = None,
    format: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    dst_port: int | None = None,
    activity_id: int | None = None,
    severity_id: int | None = None,
    since: int | None = None,
    until: int | None = None,
    limit: int = Query(50, ge=1, le=500),
):
    return search(
        source=source,
        format=format,
        src_ip=src_ip,
        dst_ip=dst_ip,
        dst_port=dst_port,
        activity_id=activity_id,
        severity_id=severity_id,
        since=since,
        until=until,
        limit=limit,
    )


@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()


@app.post("/ingest")
async def ingest_body(request: Request):
    body = await request.body()
    ids = []
    for line in body.splitlines(keepends=True):
        if line.strip():
            ids.append(pipeline.process(line))
    return {"event_ids": ids}


@app.post("/mappings/reload")
def reload_mappings(directory: str | None = None):
    return {"mappings_loaded": pipeline.reload_mappings(directory)}
