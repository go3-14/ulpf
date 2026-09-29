import argparse
import json
import logging
import sys
from pathlib import Path
_R = str(Path(__file__).resolve().parent.parent)
if _R not in sys.path: sys.path.insert(0, _R)
import threading
import uvicorn
from config import API_HOST, API_PORT, LOG_LEVEL, TCP_PORT, TLS_CERT, TLS_KEY
from ingest import metrics
from ingest.pipeline import process, reload_mappings, replay_failed
from ingest.context import IngestContext
from ingest.syslog_listener import listen
from ingest.watcher import watch
from storage.normalized_store import get_normalized, search_normalized
from storage.raw_store import read_raw
from storage.index import get_record

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

    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        eid = process(line, ctx=IngestContext(origin="file", origin_id=str(filepath).replace("\\", "/"), line_no=line_no))
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
        kwargs={"stop_event": stop_event, "tcp_port": TCP_PORT, "tls_cert": TLS_CERT, "tls_key": TLS_KEY},
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
    if args.provenance:
        print("\n=== PROVENANCE ===")
        print(json.dumps(get_record(event_id) or {}, indent=2, default=str))

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
        src_port=args.src_port, user=args.user, class_uid=args.class_uid,
        q=args.q, cursor=args.cursor,
        limit=args.limit
    )
    print(json.dumps(results, indent=2))

def cmd_correlate(args):
    from ingest.correlation import correlate
    events = search_normalized(limit=1000)
    print(json.dumps(correlate(events, key=args.key, window=args.window, min_sources=args.min_sources), indent=2))

def cmd_reload(args):
    count = reload_mappings()
    print(f"Reloaded mappings. Total active: {count}")

def cmd_test_mappings(args):
    from scripts.test_mappings import run
    print(f"passed {len(run(mapping_id=args.mapping))} mapping golden tests")

def cmd_onboard(args):
    from cli.onboarding import write_draft
    write_draft(args.sample, args.source_id, args.out)
    print(f"wrote draft mapping to {args.out}")

def cmd_validate_mapping(args):
    from mappings.loader import load_mappings
    from cli.onboarding import build_draft
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "candidate.yaml"
        import yaml
        path.write_text(yaml.safe_dump(yaml.safe_load(open(args.mapping, encoding="utf-8"))), encoding="utf-8")
        loaded = load_mappings(directory)
        print(json.dumps({"valid": bool(loaded), "source": next(iter(loaded), None)}))

def cmd_replay(args):
    print(f"Recovered: {replay_failed(limit=args.limit)}")

def cmd_suggest(args):
    from pathlib import Path
    from ingest.pipeline import PARSERS
    from parsers.detect import detect_format
    t0 = time.perf_counter()
    raw = Path(args.sample).read_text(encoding="utf-8").splitlines()[0]
    fmt = detect_format(raw)
    parsed = PARSERS[fmt](raw) if fmt else {}
    mapping = {"source": args.source, "format": fmt or "json", "field_map": {k: {"to": k, "type": "str"} for k in parsed}}
    import yaml
    print(yaml.safe_dump(mapping, sort_keys=False))

def cmd_test_mapping(args):
    import yaml, time
    from pathlib import Path
    from ingest.pipeline import PARSERS
    from parsers.detect import detect_format
    from schema.normalize import normalize
    from schema.validate import validate_event
    raw = Path(args.sample).read_text(encoding="utf-8").splitlines()[0]
    fmt = detect_format(raw)
    with open(args.mapping, encoding="utf-8") as fh: mapping = yaml.safe_load(fh)
    parsed = PARSERS[fmt](raw)
    event = normalize(parsed, mapping, "mapping-test", mapping["source"], fmt)
    validate_event(event)
    print(yaml.safe_dump(event, sort_keys=False))
    print(f"validated in {time.perf_counter() - t0:.6f}s")

def cmd_demo(args):
    from tui.app import DemoApp
    DemoApp().run()

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
    p_look.add_argument("--provenance", action="store_true", help="Include ingestion provenance")
    p_look.set_defaults(func=cmd_lookup)

    # search
    p_search = subparsers.add_parser("search", help="Search normalized events")
    p_search.add_argument("--source", help="Filter by source ID")
    p_search.add_argument("--format", help="Filter by format")
    p_search.add_argument("--src-ip", help="Filter by source IP")
    p_search.add_argument("--dst-ip", help="Filter by destination IP")
    p_search.add_argument("--dst-port", type=int, help="Filter by destination port")
    p_search.add_argument("--src-port", type=int)
    p_search.add_argument("--user")
    p_search.add_argument("--class-uid", type=int)
    p_search.add_argument("--q")
    p_search.add_argument("--cursor", type=int, default=0)
    p_search.add_argument("--limit", type=int, default=50, help="Max results to return")
    p_search.set_defaults(func=cmd_search)
    p_corr = subparsers.add_parser("correlate", help="Correlate events across sources")
    p_corr.add_argument("--key", default="src_ip"); p_corr.add_argument("--window", type=int, default=300)
    p_corr.add_argument("--min-sources", type=int, default=2); p_corr.set_defaults(func=cmd_correlate)

    # reload
    p_reload = subparsers.add_parser("reload", help="Reload YAML mappings")
    p_reload.set_defaults(func=cmd_reload)
    p_tm = subparsers.add_parser("test-mappings", help="Run YAML mapping golden tests")
    p_tm.add_argument("--mapping")
    p_tm.set_defaults(func=cmd_test_mappings)
    p_on = subparsers.add_parser("onboard", help="Draft a mapping from a sample")
    p_on.add_argument("--sample", required=True); p_on.add_argument("--source-id", default="new_source")
    p_on.add_argument("--out", required=True); p_on.set_defaults(func=cmd_onboard)
    p_vm = subparsers.add_parser("validate-mapping", help="Validate a mapping file")
    p_vm.add_argument("mapping"); p_vm.add_argument("--sample", required=False); p_vm.set_defaults(func=cmd_validate_mapping)
    p_replay = subparsers.add_parser("replay-failed", help="Retry failed-event store records")
    p_replay.add_argument("--limit", type=int)
    p_replay.set_defaults(func=cmd_replay)
    p_suggest = subparsers.add_parser("suggest", help="Draft YAML mapping from a sample")
    p_suggest.add_argument("sample"); p_suggest.add_argument("--source", default="new_source")
    p_suggest.set_defaults(func=cmd_suggest)
    p_test = subparsers.add_parser("test", help="Test a mapping against a sample")
    p_test.add_argument("mapping"); p_test.add_argument("sample")
    p_test.set_defaults(func=cmd_test_mapping)
    p_demo = subparsers.add_parser("demo", help="Launch the live Textual demonstration harness")
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
