import json
import pathlib
import threading
import config

_index_map = {}
_index_lock = threading.Lock()
_index_loaded = False

def _get_index_file() -> pathlib.Path:
    return pathlib.Path(config.STORAGE_DIR) / "index" / "raw_index.ndjson"

def _ensure_loaded():
    global _index_loaded
    if _index_loaded:
        return
    with _index_lock:
        if _index_loaded:
            return
        _index_map.clear()
        idx_file = _get_index_file()
        if idx_file.exists():
            with open(idx_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        _index_map[rec["event_id"]] = (rec["file"], rec["offset"], rec["length"])
                    except (json.JSONDecodeError, KeyError):
                        continue
        _index_loaded = True

def add_index(event_id: str, path: str, offset: int, length: int):
    _ensure_loaded()
    with _index_lock:
        if event_id in _index_map:
            return False
        _index_map[event_id] = (path, offset, length)
        idx_file = _get_index_file()
        idx_file.parent.mkdir(parents=True, exist_ok=True)
        with open(idx_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event_id": event_id, "file": path, "offset": offset, "length": length}) + "\n")
        return True


def get_index(event_id: str) -> tuple[str, int, int] | None:
    _ensure_loaded()
    with _index_lock:
        return _index_map.get(event_id)
