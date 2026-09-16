import statistics
import threading
import time
from collections import Counter, deque


_lock = threading.Lock()
_start = time.time()
_latencies = deque(maxlen=1000)
_events = deque()
processed_total = 0
failed_total = 0
processed_by_format = Counter()
processed_by_source = Counter()
failed_by_reason = Counter()


def record_success(fmt: str, source_id: str, duration_seconds: float) -> None:
    global processed_total
    now = time.time()
    with _lock:
        processed_total += 1
        processed_by_format[fmt] += 1
        processed_by_source[source_id] += 1
        _latencies.append(duration_seconds * 1000)
        _events.append(now)
        _trim(now)


def record_failure(fmt: str | None, reason: str) -> None:
    global failed_total
    with _lock:
        failed_total += 1
        failed_by_reason[reason] += 1
        if fmt:
            processed_by_format[fmt] += 0


def snapshot() -> dict:
    now = time.time()
    with _lock:
        _trim(now)
        ordered = sorted(_latencies)
        p50 = statistics.median(ordered) if ordered else 0
        p99 = ordered[int(len(ordered) * 0.99) - 1] if ordered else 0
        return {
            "processed_total": processed_total,
            "failed_total": failed_total,
            "processed_by_format": dict(processed_by_format),
            "processed_by_source": dict(processed_by_source),
            "failed_by_reason": dict(failed_by_reason),
            "events_per_second": len(_events) / 60,
            "p50_latency_ms": p50,
            "p99_latency_ms": p99,
            "uptime_seconds": int(now - _start),
        }


def _trim(now: float) -> None:
    while _events and now - _events[0] > 60:
        _events.popleft()
