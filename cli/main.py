import argparse
import json
import logging
import sys
import threading

import uvicorn

from api.main import app
from config import API_HOST, API_PORT, LOG_LEVEL
from ingest import metrics, pipeline
from ingest.syslog_listener import listen
from ingest.watcher import watch
from storage.normalized_store import read_normalized, search
from storage.raw_store import read_raw


def configure_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def cmd_process(args):
    ids = []
    with open(args.filepath, "rb") as handle:
        for line in handle:
            event_id = pipeline.process(line)
            ids.append(event_id)
            print(event_id or "FAILED")
    return 0 if any(ids) else 1


def cmd_lookup(args):
    event = read_normalized(args.event_id)
    raw = read_raw(args.event_id)
    print("RAW:")
    print(raw.decode("utf-8", errors="replace"))
    print("NORMALIZED:")
    print(json.dumps(event, indent=2))
    return 0


def cmd_search(args):
    rows = search(
        source=args.source,
        format=args.format,
        src_ip=args.src_ip,
        dst_ip=args.dst_ip,
        dst_port=args.dst_port,
        limit=args.limit,
    )
    print(json.dumps(rows, indent=2))
    return 0


def cmd_status(_args):
    print(json.dumps(metrics.snapshot(), indent=2))
    return 0


def cmd_reload(args):
    print(pipeline.reload_mappings(args.directory))
    return 0


def cmd_serve(_args):
    stop_event = threading.Event()
    threading.Thread(target=watch, kwargs={"stop_event": stop_event}, daemon=True).start()
    threading.Thread(target=listen, kwargs={"stop_event": stop_event}, daemon=True).start()
    try:
        uvicorn.run(app, host=API_HOST, port=API_PORT)
    finally:
        stop_event.set()
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="ulpf")
    sub = parser.add_subparsers(dest="command", required=True)

    process = sub.add_parser("process")
    process.add_argument("filepath")
    process.set_defaults(func=cmd_process)

    lookup = sub.add_parser("lookup")
    lookup.add_argument("event_id")
    lookup.set_defaults(func=cmd_lookup)

    search_cmd = sub.add_parser("search")
    search_cmd.add_argument("--source")
    search_cmd.add_argument("--format")
    search_cmd.add_argument("--src-ip")
    search_cmd.add_argument("--dst-ip")
    search_cmd.add_argument("--dst-port", type=int)
    search_cmd.add_argument("--limit", type=int, default=50)
    search_cmd.set_defaults(func=cmd_search)

    status = sub.add_parser("status")
    status.set_defaults(func=cmd_status)

    reload_cmd = sub.add_parser("reload")
    reload_cmd.add_argument("--directory")
    reload_cmd.set_defaults(func=cmd_reload)

    serve = sub.add_parser("serve")
    serve.set_defaults(func=cmd_serve)
    return parser


def main(argv=None):
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
