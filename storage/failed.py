import base64
import time
from storage.writer import PartitionedNDJSONWriter

FAILED_WRITER = PartitionedNDJSONWriter(subfolder="failed")

def store_failed(raw_bytes: bytes, reason: str) -> tuple:
    try:
        text = raw_bytes.decode("utf-8")
        record = {"raw": text, "raw_encoding": "utf-8", "reason": reason, "timestamp": int(time.time() * 1000)}
    except UnicodeDecodeError:
        record = {
            "raw_b64": base64.b64encode(raw_bytes).decode("ascii"),
            "raw_encoding": "base64",
            "reason": reason,
            "timestamp": int(time.time() * 1000)
        }
    return FAILED_WRITER.write("failed", record, prefix="failed")
