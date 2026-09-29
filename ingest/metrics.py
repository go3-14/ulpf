import threading
import time

_lock = threading.Lock()
_metrics = {
    "processed_total": 0,
    "failed_total": 0,
    "duplicates_total": 0,
    "fallback_total": 0,
    "fallback_by_reason": {},
    "skipped_empty_total": 0,
    "dropped_total": 0,
    "processed_by_format": {},
    "processed_by_source": {},
    "failed_by_reason": {},
    "durations": [],
    "start_time": time.time()
}

def record_success(fmt: str, source_id: str, duration_sec: float):
    with _lock:
        _metrics["processed_total"] += 1
        _metrics["processed_by_format"][fmt] = _metrics["processed_by_format"].get(fmt, 0) + 1
        _metrics["processed_by_source"][source_id] = _metrics["processed_by_source"].get(source_id, 0) + 1
        _metrics["durations"].append(duration_sec * 1000.0)
        if len(_metrics["durations"]) > 1000:
            _metrics["durations"].pop(0)

def record_failure(fmt: str | None, reason: str):
    with _lock:
        _metrics["failed_total"] += 1
        _metrics["failed_by_reason"][reason] = _metrics["failed_by_reason"].get(reason, 0) + 1

def record_duplicate():
    with _lock:
        _metrics["duplicates_total"] += 1

def record_fallback(reason: str):
    with _lock:
        _metrics["fallback_total"] += 1
        _metrics["fallback_by_reason"][reason] = _metrics["fallback_by_reason"].get(reason, 0) + 1

def get_metrics() -> dict:
    with _lock:
        durations = sorted(_metrics["durations"])
        p50 = durations[len(durations) // 2] if durations else 0.0
        p99 = durations[int(len(durations) * 0.99)] if durations else 0.0
        uptime = time.time() - _metrics["start_time"]
        return {
            "processed_total": _metrics["processed_total"],
            "failed_total": _metrics["failed_total"],
            "duplicates_total": _metrics["duplicates_total"],
            "fallback_total": _metrics["fallback_total"],
            "fallback_by_reason": dict(_metrics["fallback_by_reason"]),
            "skipped_empty_total": _metrics["skipped_empty_total"],
            "dropped_total": _metrics["dropped_total"],
            "processed_by_format": dict(_metrics["processed_by_format"]),
            "processed_by_source": dict(_metrics["processed_by_source"]),
            "failed_by_reason": dict(_metrics["failed_by_reason"]),
            "p50_latency_ms": round(p50, 3),
            "p99_latency_ms": round(p99, 3),
            "uptime_seconds": round(uptime, 1)
        }
