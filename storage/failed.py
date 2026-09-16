import base64
import time

from storage.writer import PartitionedNDJSONWriter


FAILED_WRITER = PartitionedNDJSONWriter("failed", "failed")


def store_failed(raw_bytes: bytes, reason: str) -> tuple[str, int, int]:
    try:
        raw = raw_bytes.decode("utf-8")
        record = {"raw": raw, "raw_encoding": "utf-8"}
    except UnicodeDecodeError:
        record = {"raw_b64": base64.b64encode(raw_bytes).decode("ascii"), "raw_encoding": "base64"}
    record["reason"] = reason
    record["received_at"] = int(time.time() * 1000)
    return FAILED_WRITER.write(None, record)
