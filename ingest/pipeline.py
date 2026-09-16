import logging
import time
import uuid

from ingest import metrics
from mappings.loader import load_mappings
from mappings.matcher import identify_source
from parsers.cef import parse_cef
from parsers.detect import detect_format
from parsers.json_log import parse_json
from parsers.leef import parse_leef
from parsers.syslog import parse_syslog
from schema.normalize import normalize
from schema.validate import validate_event
from storage.failed import store_failed
from storage.index import add_index, rebuild
from storage.normalized_store import store_normalized
from storage.raw_store import store_raw


logger = logging.getLogger("ulpf.ingest.pipeline")
PARSERS = {"syslog": parse_syslog, "cef": parse_cef, "leef": parse_leef, "json": parse_json}
MAPPINGS = load_mappings()
rebuild()


def reload_mappings(directory=None):
    global MAPPINGS
    MAPPINGS = load_mappings(directory)
    logger.info("loaded mappings: %s", sorted(MAPPINGS))
    return len(MAPPINGS)


def process(raw_bytes: bytes, source_id_hint: str | None = None) -> str | None:
    t0 = time.perf_counter()
    raw_text = raw_bytes.decode("utf-8", errors="replace")

    fmt = detect_format(raw_text)
    if fmt is None:
        return _fail(raw_bytes, "unrecognized format", None)

    try:
        parsed = PARSERS[fmt](raw_text)
    except Exception as exc:
        logger.warning("parser raised for format %s: %s", fmt, exc)
        return _fail(raw_bytes, f"failed to parse as {fmt}: {exc}", fmt)
    if parsed is None:
        return _fail(raw_bytes, f"failed to parse as {fmt}", fmt)

    source_id = source_id_hint or identify_source(parsed, fmt, MAPPINGS)
    if source_id is None or source_id not in MAPPINGS:
        return _fail(raw_bytes, f"no mapping matched (format={fmt})", fmt)

    event_id = str(uuid.uuid4())
    normalized = normalize(parsed, MAPPINGS[source_id], event_id, source_id, fmt)

    try:
        validate_event(normalized)
    except Exception as exc:
        return _fail(raw_bytes, f"OCSF validation failed: {exc}", fmt)

    path, offset, length = store_raw(event_id, raw_bytes, source_id)
    add_index(event_id, path, offset, length)
    store_normalized(event_id, normalized, source_id)

    metrics.record_success(fmt, source_id, time.perf_counter() - t0)
    return event_id


def _fail(raw_bytes: bytes, reason: str, fmt: str | None):
    logger.warning("dead-lettered event: %s", reason)
    store_failed(raw_bytes, reason)
    metrics.record_failure(fmt, reason)
    return None
