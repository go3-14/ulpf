from collections import Counter, defaultdict
import threading

_lock = threading.Lock()
_data = defaultdict(lambda: {"events": 0, "mapped": 0, "parsed": 0, "fallback": 0, "unmapped_keys": Counter()})

def record(source, parsed, mapped, fallback=False):
    with _lock:
        parsed_count = len(parsed) if hasattr(parsed, "__len__") else int(parsed)
        mapped_count = len(mapped) if hasattr(mapped, "__len__") else int(mapped)
        item = _data[source]; item["events"] += 1; item["parsed"] += parsed_count; item["mapped"] += mapped_count
        item["fallback"] += int(fallback)
        for key in set(parsed) - set(mapped): item["unmapped_keys"][key] += 1

def report(source=None):
    with _lock:
        result = {}
        for name, item in _data.items():
            if source and name != source: continue
            result[name] = {"events": item["events"], "mapped_ratio": item["mapped"] / item["parsed"] if item["parsed"] else 1.0,
                            "fallback_rate": item["fallback"] / item["events"] if item["events"] else 0.0,
                            "top_unmapped": item["unmapped_keys"].most_common(20)}
        return result
