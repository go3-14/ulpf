import time
import uuid
from parsers.detect import detect_format
from parsers.syslog import parse_syslog
from parsers.cef import parse_cef
from parsers.leef import parse_leef
from parsers.json_log import parse_json
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
    "json": parse_json
}

MAPPINGS = load_mappings()

def reload_mappings(directory=None):
    global MAPPINGS
    MAPPINGS = load_mappings(directory)
    return len(MAPPINGS)

def process(raw_bytes: bytes, source_id_hint: str | None = None) -> str | None:
    t0 = time.perf_counter()
    raw_text = raw_bytes.decode("utf-8", errors="replace").strip()
    if not raw_text:
        return None

    fmt = detect_format(raw_text)
    if fmt is None:
        return _fail(raw_bytes, "unrecognized format", None)

    parser_fn = PARSERS.get(fmt)
    if not parser_fn:
        return _fail(raw_bytes, f"no parser registered for format {fmt}", fmt)

    parsed = parser_fn(raw_text)
    if parsed is None:
        return _fail(raw_bytes, f"failed to parse as {fmt}", fmt)

    source_id = source_id_hint or identify_source(parsed, fmt, MAPPINGS)
    if source_id is None or source_id not in MAPPINGS:
        return _fail(raw_bytes, f"no mapping matched (format={fmt})", fmt)

    event_id = str(uuid.uuid4())
    normalized = normalize(parsed, MAPPINGS[source_id], event_id, source_id, fmt)

    try:
        validate_event(normalized)
    except Exception as e:
        return _fail(raw_bytes, f"OCSF validation failed: {e}", fmt)

    path, offset, length = store_raw(event_id, raw_bytes, source_id)
    add_index(event_id, path, offset, length)
    store_normalized(event_id, normalized, source_id)

    metrics.record_success(fmt, source_id, time.perf_counter() - t0)
    return event_id

def _fail(raw_bytes, reason, fmt):
    store_failed(raw_bytes, reason)
    metrics.record_failure(fmt, reason)
    return None
