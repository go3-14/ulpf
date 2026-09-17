from __future__ import annotations

import json
import logging
import pathlib
import shutil
import threading

from config import POLL_INTERVAL, SPOOL_DIR
from ingest.pipeline import process
from storage.writer import flush_all

logger = logging.getLogger("ulpf.ingest.watcher")


def watch(spool_dir=SPOOL_DIR, poll_interval=POLL_INTERVAL, processed_dir=None, stop_event=None):
    stop_event = stop_event or threading.Event()
    spool = pathlib.Path(spool_dir)
    processed = pathlib.Path(processed_dir) if processed_dir else spool / ".processed"
    state_path = spool / ".ulpf_offsets.json"
    spool.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        state = {}
    try:
        while not stop_event.is_set():
            for path in sorted(spool.glob("*.log")):
                if stop_event.is_set():
                    break
                _consume(path, state, state_path, processed)
            stop_event.wait(poll_interval)
    finally:
        flush_all()


def _consume(path: pathlib.Path, state: dict, state_path: pathlib.Path, processed: pathlib.Path) -> None:
    key = str(path)
    offset = int(state.get(key, 0))
    try:
        with path.open("rb") as handle:
            handle.seek(offset)
            data = handle.read()
    except OSError:
        return
    boundary = data.rfind(b"\n")
    if boundary < 0:
        return
    complete = data[: boundary + 1]
    for line in complete.splitlines(keepends=True):
        try:
            process(line)
        except Exception:
            logger.exception("unexpected watcher error while processing %s", path)
    new_offset = offset + len(complete)
    state[key] = new_offset
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    try:
        size = path.stat().st_size
    except OSError:
        return
    if new_offset == size and data.endswith(b"\n"):
        destination = processed / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
        state.pop(key, None)
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        logger.info("completed spool file %s", path)
