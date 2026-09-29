import json
import logging
import os
import pathlib
import shutil
import threading
import time
import inspect
from config import SPOOL_DIR, POLL_INTERVAL
from ingest.pipeline import process
from ingest.context import IngestContext
from storage.writer import flush_all

logger = logging.getLogger("ulpf.watcher")

def _process_line(line, ctx):
    """Keep compatibility with simple process stubs used by integrations/tests."""
    if "ctx" in inspect.signature(process).parameters:
        return process(line, ctx=ctx)
    return process(line)

def watch(spool_dir: str | pathlib.Path | None = None,
          poll_interval: float = POLL_INTERVAL,
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

    partial_buffers = {}  # filepath -> bytes buffer of trailing un-terminated line

    logger.info(f"Starting spool watcher on {s_dir}")

    try:
        while stop_event is None or not stop_event.is_set():
            try:
                log_files = sorted(s_dir.glob("*.log"))
                for fpath in log_files:
                    fkey = str(fpath.resolve())
                    if fkey not in state:
                        state[fkey] = 0

                    current_offset = state[fkey]
                    file_size = fpath.stat().st_size

                    # A producer may rotate or truncate a spool file while it is
                    # being watched.  Never seek beyond the new file contents.
                    if file_size < current_offset:
                        state[fkey] = 0
                        current_offset = 0
                        partial_buffers.pop(fkey, None)

                    if file_size > current_offset:
                        with open(fpath, "rb") as fh:
                            fh.seek(current_offset)
                            new_bytes = fh.read()

                        # Combine with the prior unterminated suffix.  The suffix
                        # has already been read from disk, so only bytes from the
                        # newly-read portion may advance the persisted offset.
                        previous_partial = partial_buffers.get(fkey, b"")
                        buf = previous_partial + new_bytes

                        lines = buf.split(b"\n")
                        # If buffer ends with \n, all elements are complete lines
                        # Otherwise, the last element is an incomplete partial line
                        if buf.endswith(b"\n"):
                            complete_lines = lines
                            partial_buffers[fkey] = b""
                        else:
                            complete_lines = lines[:-1]
                            partial_buffers[fkey] = lines[-1]

                        # ``new_bytes`` starts at the persisted read offset, so
                        # every byte in it has now been observed. The trailing
                        # partial suffix is retained in memory and is combined
                        # with only future bytes on the next poll.
                        state[fkey] += len(new_bytes)

                        for line_no, line in enumerate(complete_lines, 1):
                            line_stripped = line.strip()
                            if line_stripped:
                                try:
                                    # The newline is a framing delimiter, not part
                                    # of the event. Preserve all other whitespace
                                    # so raw storage remains lossless.
                                    _process_line(line, IngestContext(origin="file", origin_id=fpath.name,
                                                                       offset=current_offset, line_no=line_no))
                                except Exception as ex:
                                    logger.error(f"Error processing line from {fpath.name}: {ex}", exc_info=True)

                        # Persist after the bytes have been durably handed to
                        # the processor. Atomic replace prevents a torn state
                        # file from replaying an arbitrary offset after crash.
                        tmp_state = state_file.with_suffix(".tmp")
                        with open(tmp_state, "w", encoding="utf-8") as sf:
                            json.dump(state, sf)
                            sf.flush()
                            os.fsync(sf.fileno())
                        os.replace(tmp_state, state_file)

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
    finally:
        flush_all()
        logger.info("Watcher flushed all writers on shutdown.")
