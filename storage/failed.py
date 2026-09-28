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

def iter_failed(storage_dir=None):
    import glob, json, pathlib
    import config
    root = pathlib.Path(storage_dir or config.STORAGE_DIR) / "failed"
    for path in glob.glob(str(root / "**" / "*.ndjson"), recursive=True):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    record = json.loads(line)
                    if record.get("raw_encoding") == "base64":
                        record["raw_bytes"] = base64.b64decode(record["raw_b64"])
                    else:
                        record["raw_bytes"] = record.get("raw", "").encode("utf-8")
                    yield record
                except (ValueError, OSError):
                    continue

def list_failed(storage_dir=None, limit=100):
    result = []
    for index, record in enumerate(iter_failed(storage_dir)):
        if index >= limit:
            break
        result.append({"id": index, "raw": record.get("raw", record.get("raw_b64", "")),
                       "reason": record.get("reason", "unknown"),
                       "timestamp": record.get("timestamp")})
    return result
