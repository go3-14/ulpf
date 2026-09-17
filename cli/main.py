from __future__ import annotations

import argparse
import json
import logging
import pathlib
import sys
import threading

import uvicorn

from api.main import app
from config import API_HOST, API_PORT, LOG_LEVEL
from ingest import metrics, pipeline
from ingest.syslog_listener import listen
from ingest.watcher import watch
from storage.normalized_store import get_normalized, search
from storage.raw_store import read_raw


def configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s", stream=sys.stderr)


def serve() -> None:
    stop_event = threading.Event()
    watcher_thread = threading.Thread(target=watch, kwargs={"stop_event": stop_event}, daemon=True, name="ulpf-watcher")
    listener_thread = threading.Thread(target=listen, kwargs={"stop_event": stop_event}, daemon=True, name="ulpf-udp-listener")
    watcher_thread.start()
    listener_thread.start()
    try:
        uvicorn.run(app, host=API_HOST, port=API_PORT)
    finally:
        stop_event.set()
        watcher_thread.join(timeout=3)
        listener_thread.join(timeout=3)


def main(argv=None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(prog="ulpf")
    sub = parser.add_subparsers(dest="command", required=True)
    process_parser = sub.add_parser("process")
    process_parser.add_argument("filepath")
    sub.add_parser("serve")
    sub.add_parser("status")
    sub.add_parser("reload")
    lookup_parser = sub.add_parser("lookup")
    lookup_parser.add_argument("event_id")
    search_parser = sub.add_parser("search")
    search_parser.add_argument("--src-ip")
    search_parser.add_argument("--source")
    search_parser.add_argument("--format")
    args = parser.parse_args(argv)
    if args.command == "serve":
        serve()
    elif args.command == "process":
        for line in pathlib.Path(args.filepath).read_bytes().splitlines(keepends=True):
            print(pipeline.process(line) or "FAILED")
    elif args.command == "status":
        print(json.dumps({"processed_total": metrics.processed_total, "failed_total": metrics.failed_total}, indent=2))
    elif args.command == "reload":
        print(pipeline.reload_mappings())
    elif args.command == "lookup":
        print("RAW:")
        print(read_raw(args.event_id).decode("utf-8", errors="replace"))
        print("NORMALIZED:")
        print(json.dumps(get_normalized(args.event_id), indent=2))
    elif args.command == "search":
        print(json.dumps(search(src_ip=args.src_ip, source=args.source, format=args.format), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
