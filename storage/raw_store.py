import base64
import json
import time
from storage.writer import PartitionedNDJSONWriter
from storage.index import get_index

RAW_WRITER = PartitionedNDJSONWriter(subfolder="raw")

def store_raw(event_id: str, raw_bytes: bytes, source_id: str) -> tuple:
    try:
        text, encoding = raw_bytes.decode("utf-8"), "utf-8"
        record = {"event_id": event_id, "raw": text, "raw_encoding": encoding}
    except UnicodeDecodeError:
        record = {
            "event_id": event_id,
            "raw_b64": base64.b64encode(raw_bytes).decode("ascii"),
            "raw_encoding": "base64"
        }
    record["source_id"] = source_id
    record["received_at"] = int(time.time() * 1000)
    return RAW_WRITER.write(source_id, record, prefix="raw")

def read_raw(event_id: str) -> bytes | None:
    idx = get_index(event_id)
    if not idx:
        return None
    file_path, offset, length = idx
    try:
        with open(file_path, "rb") as f:
            f.seek(offset)
            data = f.read(length)
            record = json.loads(data.decode("utf-8"))
            if record.get("raw_encoding") == "base64":
                return base64.b64decode(record["raw_b64"])
            return record["raw"].encode("utf-8")
    except Exception:
        return None

def reset_writers():
    RAW_WRITER.close_all()

