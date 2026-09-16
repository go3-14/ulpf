import json
import logging
import os
import pathlib
import shutil
import threading
import time
from config import SPOOL_DIR
from ingest.pipeline import process

logger = logging.getLogger("ulpf.watcher")

def watch(spool_dir: str | pathlib.Path | None = None,
          poll_interval: float = 1.0,
          processed_dir: str | pathlib.Path | None = None,
          stop_event: threading.Event | None = None):
    s_dir = pathlib.Path(spool_dir) if spool_dir else SPOOL_DIR
    p_dir = pathlib.Path(processed_dir) if processed_dir else (s_dir / ".processed")
    s_dir.mkdir(parents=True, exist_ok=True)
    p_dir.mkdir(parents=True, exist_ok=True)

    state_file = s_dir / ".processed_state.json"
    state = {}
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as sf:
                state = json.load(sf)
        except Exception as e:
            logger.warning(f"Could not load state file {state_file}: {e}")

    partial_buffers = {}  # filepath -> string buffer of trailing un-terminated line

    logger.info(f"Starting spool watcher on {s_dir}")

    while stop_event is None or not stop_event.is_set():
        try:
            log_files = sorted(s_dir.glob("*.log"))
            for fpath in log_files:
                fkey = str(fpath.resolve())
                if fkey not in state:
                    state[fkey] = 0

                current_offset = state[fkey]
                file_size = fpath.stat().st_size

                if file_size > current_offset:
                    with open(fpath, "rb") as fh:
                        fh.seek(current_offset)
                        new_bytes = fh.read()

                    # Combine with existing partial buffer for this file
                    buf = partial_buffers.get(fkey, b"") + new_bytes

                    lines = buf.split(b"\n")
                    # If buffer ends with \n, all elements are complete lines
                    # Otherwise, the last element is an incomplete partial line
                    if buf.endswith(b"\n"):
                        complete_lines = lines
                        partial_buffers[fkey] = b""
                    else:
                        complete_lines = lines[:-1]
                        partial_buffers[fkey] = lines[-1]

                    consumed_bytes = sum(len(line) + 1 for line in complete_lines)
                    state[fkey] += consumed_bytes

                    for line in complete_lines:
                        line_stripped = line.strip()
                        if line_stripped:
                            try:
                                process(line_stripped)
                            except Exception as ex:
                                logger.error(f"Error processing line from {fpath.name}: {ex}", exc_info=True)

                    # Persist state
                    with open(state_file, "w", encoding="utf-8") as sf:
                        json.dump(state, sf)

                    # Move file if EOF reached and buffer clean
                    if fpath.stat().st_size == state[fkey] and not partial_buffers.get(fkey):
                        dest = p_dir / fpath.name
                        shutil.move(str(fpath), str(dest))
                        logger.info(f"Completed spool file {fpath.name}, moved to {dest}")
                        del state[fkey]
                        if fkey in partial_buffers:
                            del partial_buffers[fkey]

        except Exception as e:
            logger.error(f"Error in watcher loop: {e}", exc_info=True)

        time.sleep(poll_interval)
