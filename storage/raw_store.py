from __future__ import annotations

import base64
import json
import time

from storage.index import get_index
from storage.writer import PartitionedNDJSONWriter

RAW_WRITER = PartitionedNDJSONWriter("raw")


def store_raw(event_id: str, raw_bytes: bytes, source_id: str) -> tuple:
    try:
        record = {"event_id": event_id, "raw": raw_bytes.decode("utf-8"), "raw_encoding": "utf-8"}
    except UnicodeDecodeError:
        record = {"event_id": event_id, "raw_b64": base64.b64encode(raw_bytes).decode("ascii"), "raw_encoding": "base64"}
    record.update({"source_id": source_id, "received_at": int(time.time() * 1000)})
    return RAW_WRITER.write(source_id, record)


def read_raw(event_id: str) -> bytes:
    location = get_index(event_id)
    if not location:
        raise KeyError(event_id)
    path, offset, _length = location
    with open(path, encoding="utf-8") as handle:
        handle.seek(offset)
        record = json.loads(handle.readline())
    if record["raw_encoding"] == "base64":
        return base64.b64decode(record["raw_b64"])
    return record["raw"].encode("utf-8")
