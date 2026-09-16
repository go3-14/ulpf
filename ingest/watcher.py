import json
import logging
import shutil
import threading
import time
from pathlib import Path

from config import SPOOL_DIR
from ingest import pipeline


logger = logging.getLogger("ulpf.ingest.watcher")


def watch(spool_dir=None, poll_interval=1.0, processed_dir=None, stop_event: threading.Event | None = None):
    spool = Path(spool_dir or SPOOL_DIR)
    processed = Path(processed_dir or spool / ".processed")
    state_path = spool / ".ulpf_offsets.json"
    spool.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    offsets = _load_offsets(state_path)
    stop_event = stop_event or threading.Event()

    while not stop_event.is_set():
        for path in sorted(spool.glob("*.log")):
            try:
                offset = offsets.get(str(path), 0)
                new_offset = _consume_file(path, offset)
                offsets[str(path)] = new_offset
                _save_offsets(state_path, offsets)
                if new_offset >= path.stat().st_size:
                    target = processed / path.name
                    shutil.move(str(path), target)
                    offsets.pop(str(path), None)
                    _save_offsets(state_path, offsets)
                    logger.info("processed spool file %s", path)
            except Exception:
                logger.error("watcher failed on %s", path, exc_info=True)
        stop_event.wait(poll_interval)


def _consume_file(path: Path, offset: int) -> int:
    with open(path, "rb") as handle:
        handle.seek(offset)
        data = handle.read()
    if not data:
        return offset
    last_newline = data.rfind(b"\n")
    if last_newline == -1:
        return offset
    chunk = data[: last_newline + 1]
    for line in chunk.splitlines(keepends=True):
        try:
            pipeline.process(line)
        except Exception:
            logger.error("unexpected ingestion error for %s", path, exc_info=True)
    return offset + len(chunk)


def _load_offsets(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_offsets(path: Path, offsets: dict) -> None:
    path.write_text(json.dumps(offsets, indent=2), encoding="utf-8")
