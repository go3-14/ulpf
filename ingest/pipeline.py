import time
import uuid
from ingest.context import IngestContext
from parsers.detect import detect_format
from parsers.syslog import parse_syslog
from parsers.cef import parse_cef
from parsers.leef import parse_leef
from parsers.json_log import parse_json
from parsers.xml_log import parse_xml
from parsers.csv_log import parse_csv
from mappings.loader import load_mappings
from mappings.matcher import identify_source
from schema.normalize import normalize
from schema.validate import validate_event
from storage.raw_store import store_raw
from storage.normalized_store import store_normalized
from storage.failed import store_failed
from storage.index import add_index
from ingest import metrics

PARSERS = {
    "syslog": parse_syslog,
    "cef": parse_cef,
    "leef": parse_leef,
    "json": parse_json, "xml": parse_xml, "csv": parse_csv
}

MAPPINGS = load_mappings()
CATCHALL_MAPPING = {
    "source": "ulpf_catchall", "format": "json", "mapping_version": "builtin-1",
    "ocsf": {"class_uid": 0, "category_uid": 0},
    "field_map": {}, "defaults": {"activity_id": 0, "severity_id": 0}
}

def reload_mappings(directory=None):
    global MAPPINGS
    MAPPINGS = load_mappings(directory)
    return len(MAPPINGS)

def process(raw_bytes: bytes, source_id_hint: str | None = None,
            record_failure: bool = True, *, ctx: IngestContext | None = None) -> str | None:
    t0 = time.perf_counter()
    if ctx is None:
        now_ms = int(time.time() * 1000)
        ctx = IngestContext(origin="cli", received_ms=now_ms, reference_ms=now_ms)
    if source_id_hint is None:
        source_id_hint = ctx.source_hint
    raw_text = raw_bytes.decode("utf-8", errors="replace").strip()
    if not raw_text:
        return None

    fmt = detect_format(raw_text)
    if fmt is None:
        return _fail(raw_bytes, "unrecognized format", None, record_failure)

    parser_fn = PARSERS.get(fmt)
    if not parser_fn:
        return _fail(raw_bytes, f"no parser registered for format {fmt}", fmt, record_failure)

    parsed = parser_fn(raw_text)
    if parsed is None:
        return _fail(raw_bytes, f"failed to parse as {fmt}", fmt, record_failure)

    source_id = source_id_hint or identify_source(parsed, fmt, MAPPINGS)
    if source_id is None or source_id not in MAPPINGS:
        # Recognized but unmapped input is still a valid Base Event. This keeps
        # the universal ingestion contract lossless and replayable.
        source_id = f"unmapped_{fmt}"
        mapping = dict(CATCHALL_MAPPING, format=fmt, source=source_id)
    else:
        mapping = MAPPINGS[source_id]

    for rule in mapping.get("extract", []):
        import re
        match = re.search(rule.get("regex", ""), str(parsed.get("message", raw_text)))
        if match:
            parsed.update({k: v for k, v in match.groupdict().items() if v is not None})
    event_id = str(uuid.uuid4())
    normalized = normalize(parsed, mapping, event_id, source_id, fmt)

    try:
        validate_event(normalized)
    except Exception as e:
        return _fail(raw_bytes, f"OCSF validation failed: {e}", fmt, record_failure)

    path, offset, length = store_raw(event_id, raw_bytes, source_id)
    add_index(event_id, path, offset, length)
    store_normalized(event_id, normalized, source_id)

    metrics.record_success(fmt, source_id, time.perf_counter() - t0)
    return event_id

def _fail(raw_bytes, reason, fmt, record_failure=True):
    """Record new ingestion failures, but never duplicate them during replay."""
    if record_failure:
        store_failed(raw_bytes, reason)
        metrics.record_failure(fmt, reason)
    return None

def replay_failed(storage_dir=None, limit=None):
    from storage.failed import iter_failed
    recovered = 0
    for record in iter_failed(storage_dir):
        if limit is not None and recovered >= limit:
            break
        if process(record["raw_bytes"], record_failure=False):
            recovered += 1
    return recovered
