import base64
import time

from storage.index import get_raw_location
from storage.writer import PartitionedNDJSONWriter, read_record_at


RAW_WRITER = PartitionedNDJSONWriter("raw", "raw")


def store_raw(event_id: str, raw_bytes: bytes, source_id: str) -> tuple[str, int, int]:
    try:
        text, encoding = raw_bytes.decode("utf-8"), "utf-8"
        record = {"event_id": event_id, "raw": text, "raw_encoding": encoding}
    except UnicodeDecodeError:
        record = {
            "event_id": event_id,
            "raw_b64": base64.b64encode(raw_bytes).decode("ascii"),
            "raw_encoding": "base64",
        }
    record["source_id"] = source_id
    record["received_at"] = int(time.time() * 1000)
    return RAW_WRITER.write(source_id, record)


def read_raw(event_id: str) -> bytes:
    loc = get_raw_location(event_id)
    if loc is None:
        raise KeyError(event_id)
    record = read_record_at(*loc)
    if record.get("raw_encoding") == "base64":
        return base64.b64decode(record["raw_b64"])
    return record["raw"].encode("utf-8")
