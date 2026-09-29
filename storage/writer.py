import atexit
import datetime
import json
import os
import pathlib
import threading
from config import STORAGE_DIR

MAX_FILE_SIZE = 64 * 1024 * 1024  # 64 MB

# Module-level registry so flush_all() can be called from watcher/listener shutdown paths
_WRITERS: list["PartitionedNDJSONWriter"] = []

class PartitionedNDJSONWriter:
    def __init__(self, base_dir: pathlib.Path | None = None, subfolder: str = "normalized"):
        self._explicit_base_dir = base_dir
        self.subfolder = subfolder
        self._handles = {}     # path -> file object
        self._locks = {}       # path -> threading.Lock
        self._counts = {}      # path -> unflushed count
        self._dict_lock = threading.Lock()
        atexit.register(self.close_all)
        _WRITERS.append(self)

    def _get_base_dir(self) -> pathlib.Path:
        if self._explicit_base_dir:
            d = pathlib.Path(self._explicit_base_dir) / self.subfolder
        else:
            import config
            d = pathlib.Path(config.STORAGE_DIR) / self.subfolder
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_handle_and_lock(self, source_id: str, prefix: str = "events"):
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        part_dir = self._get_base_dir() / f"dt={today}" / f"source={source_id}"
        part_dir.mkdir(parents=True, exist_ok=True)

        idx = 1
        while True:
            file_path = part_dir / f"{prefix}-{idx:04d}.ndjson"
            if file_path.exists() and file_path.stat().st_size >= MAX_FILE_SIZE:
                idx += 1
            else:
                break

        key = str(file_path.resolve())
        with self._dict_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            if key not in self._handles or self._handles[key].closed:
                f = open(file_path, "a", encoding="utf-8")
                self._handles[key] = f
                self._counts[key] = 0
            return file_path, self._handles[key], self._locks[key]

    def write(self, source_id: str, record: dict, prefix: str = "events") -> tuple[str, int, int]:
        line = json.dumps(record, ensure_ascii=False) + "\n"
        line_bytes = line.encode("utf-8")

        file_path, handle, file_lock = self._get_handle_and_lock(source_id, prefix)

        with file_lock:
            offset = handle.tell()
            handle.write(line)
            length = len(line_bytes)
            handle.flush()
            import config
            if config.ULPF_FSYNC == "every":
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    pass
            
            key = str(file_path.resolve())
            self._counts[key] = self._counts.get(key, 0) + 1

            return str(file_path), offset, length

    def flush_all(self):
        with self._dict_lock:
            for key, handle in list(self._handles.items()):
                if handle.closed:
                    continue
                file_lock = self._locks.get(key)
                if file_lock:
                    with file_lock:
                        handle.flush()
                        import config
                        if config.ULPF_FSYNC != "off":
                            try:
                                os.fsync(handle.fileno())
                            except OSError:
                                pass
                        self._counts[key] = 0

    def close_all(self):
        with self._dict_lock:
            for key, handle in list(self._handles.items()):
                if not handle.closed:
                    file_lock = self._locks.get(key)
                    if file_lock:
                        with file_lock:
                            try:
                                handle.flush()
                                import config
                                if config.ULPF_FSYNC != "off":
                                    os.fsync(handle.fileno())
                            except OSError:
                                pass
                            handle.close()
            self._handles.clear()
            self._locks.clear()
            self._counts.clear()


def flush_all() -> None:
    """Flush and close all active writers. Called from watcher/listener finally blocks
    to ensure buffered events are committed to disk before process exit."""
    for writer in list(_WRITERS):
        writer.close_all()
