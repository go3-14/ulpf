import argparse
import json
import logging
import sys
import threading
import uvicorn
from config import API_HOST, API_PORT, LOG_LEVEL
from ingest import metrics
from ingest.pipeline import process, reload_mappings
from ingest.syslog_listener import listen
from ingest.watcher import watch
from storage.normalized_store import get_normalized, search_normalized
from storage.raw_store import read_raw

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr
    )

def cmd_process(args):
    filepath = args.filepath
    processed = 0
    failed = 0
    with open(filepath, "rb") as fh:
        content = fh.read()

    lines = [l for l in content.splitlines() if l.strip()]

    # If the file is a pretty-printed multi-line JSON document
    stripped_content = content.strip()
    if stripped_content.startswith(b"{") or stripped_content.startswith(b"["):
        try:
            import json
            json.loads(stripped_content.decode("utf-8", errors="replace"))
            lines = [stripped_content]
        except json.JSONDecodeError:
            pass

    for line in lines:
        if not line.strip():
            continue
        eid = process(line)
        if eid:
            processed += 1
            print(f"PROCESSED: {eid}")
        else:
            failed += 1
            print(f"FAILED: {line.decode('utf-8', errors='replace')}")
    print(f"\nSummary: {processed} processed, {failed} failed.")


def cmd_serve(args):
    setup_logging()
    logger = logging.getLogger("ulpf.serve")
    logger.info("Starting ULPF Service...")

    stop_event = threading.Event()

    watcher_thread = threading.Thread(
        target=watch,
        kwargs={"stop_event": stop_event},
        daemon=True
    )
    watcher_thread.start()

    listener_thread = threading.Thread(
        target=listen,
        kwargs={"stop_event": stop_event},
        daemon=True
    )
    listener_thread.start()

    try:
        from api.main import app
        uvicorn.run(app, host=API_HOST, port=API_PORT)
    finally:
        logger.info("Shutting down background services...")
        stop_event.set()
        watcher_thread.join(timeout=2.0)
        listener_thread.join(timeout=2.0)
        logger.info("Shutdown complete.")

def cmd_status(args):
    m = metrics.get_metrics()
    print(json.dumps(m, indent=2))

def cmd_lookup(args):
    event_id = args.event_id
    raw = read_raw(event_id)
    norm = get_normalized(event_id)

    print("=== RAW LOG ===")
    if raw:
        print(raw.decode("utf-8", errors="replace"))
    else:
        print("<NOT FOUND>")

    print("\n=== NORMALIZED OCSF EVENT ===")
    if norm:
        print(json.dumps(norm, indent=2))
    else:
        print("<NOT FOUND>")

def cmd_search(args):
    results = search_normalized(
        source=args.source,
        fmt=args.format,
        src_ip=args.src_ip,
        dst_ip=args.dst_ip,
        dst_port=args.dst_port,
        limit=args.limit
    )
    print(json.dumps(results, indent=2))

def cmd_reload(args):
    count = reload_mappings()
    print(f"Reloaded mappings. Total active: {count}")

def main():
    setup_logging()
    parser = argparse.ArgumentParser(prog="ulpf", description="Universal Log Pre-processing Framework")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # process
    p_proc = subparsers.add_parser("process", help="Process a log file")
    p_proc.add_argument("filepath", help="Path to log file")
    p_proc.set_defaults(func=cmd_process)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start long-running service (watcher + listener + REST API)")
    p_serve.set_defaults(func=cmd_serve)

    # status
    p_stat = subparsers.add_parser("status", help="Print metrics and status")
    p_stat.set_defaults(func=cmd_status)

    # lookup
    p_look = subparsers.add_parser("lookup", help="Lookup event by ID (raw and normalized)")
    p_look.add_argument("event_id", help="Event UUID")
    p_look.set_defaults(func=cmd_lookup)

    # search
    p_search = subparsers.add_parser("search", help="Search normalized events")
    p_search.add_argument("--source", help="Filter by source ID")
    p_search.add_argument("--format", help="Filter by format")
    p_search.add_argument("--src-ip", help="Filter by source IP")
    p_search.add_argument("--dst-ip", help="Filter by destination IP")
    p_search.add_argument("--dst-port", type=int, help="Filter by destination port")
    p_search.add_argument("--limit", type=int, default=50, help="Max results to return")
    p_search.set_defaults(func=cmd_search)

    # reload
    p_reload = subparsers.add_parser("reload", help="Reload YAML mappings")
    p_reload.set_defaults(func=cmd_reload)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
