from __future__ import annotations

import json
import time

from storage.writer import PartitionedNDJSONWriter

FAILED_WRITER = PartitionedNDJSONWriter("failed")
_FAILURES: list[dict] = []


def store_failed(raw_bytes: bytes, reason: str) -> None:
    record = {"raw": raw_bytes.decode("utf-8", errors="replace"), "reason": reason, "received_at": int(time.time() * 1000)}
    _FAILURES.append(record)
    FAILED_WRITER.write("_all", record)
