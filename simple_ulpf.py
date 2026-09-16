"""A deliberately small, lossless Universal Log Pre-processing Framework.

Run: python simple_ulpf.py process samples/cisco_asa_syslog.log
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent
DEFAULT_CONFIG = ROOT / "sources.json"
DEFAULT_OUTPUT = ROOT / "output"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect(raw: str) -> str | None:
    text = raw.lstrip()
    if "CEF:" in text:
        return "cef"
    if "LEEF:" in text:
        return "leef"
    if text.startswith("{"):
        return "json"
    if re.match(r"^(<\d+>)?[A-Z][a-z]{2}\s+\d+\s+\d\d:\d\d:\d\d\s+", text):
        return "syslog"
    return None


def kv_pairs(text: str) -> dict[str, str]:
    """Read common key=value fragments, including quoted values."""
    return {key: value.strip('"') for key, value in re.findall(r"([\w.]+)=((?:\"[^\"]*\")|\S+)", text)}


def parse_syslog(raw: str) -> dict:
    match = re.match(r"(?:<(\d+)>)?(\w{3}\s+\d+\s+\d\d:\d\d:\d\d)\s+(\S+)\s+(.*)", raw.strip())
    if not match:
        raise ValueError("not an RFC3164-style syslog line")
    pri, timestamp, host, message = match.groups()
    event = {"timestamp": timestamp, "host": host, "message": message, **kv_pairs(message)}
    if pri:
        event["pri"] = int(pri)
    asa = re.search(r"(%ASA-(\d+)-(\d+)):", message)
    if asa:
        event.update({"tag": asa.group(1), "severity": asa.group(2), "event_code": asa.group(3)})
        connection = re.search(r"\b(Built|Teardown|Deny|Denied|Reset).*?\bsrc\s+\S+:(\S+)/(\d+)\s+dst\s+\S+:(\S+)/(\d+)", message, re.I)
        if connection:
            action, src, src_port, dst, dst_port = connection.groups()
            event.update({"action": action.lower(), "src": src, "src_port": src_port, "dst": dst, "dst_port": dst_port})
    return event


def parse_cef(raw: str) -> dict:
    body = raw.split("CEF:", 1)[1].strip()
    parts = body.split("|", 7)
    if len(parts) < 7:
        raise ValueError("invalid CEF header")
    version, vendor, product, product_version, code, name, severity, *extension = parts
    event = {"cef_version": version, "vendor": vendor, "product": product, "event_code": code,
             "name": name, "severity": severity, **kv_pairs(extension[0] if extension else "")}
    return event


def parse_leef(raw: str) -> dict:
    body = raw.split("LEEF:", 1)[1].strip()
    header, _, extension = body.partition("\t")
    parts = header.split("|")
    if len(parts) < 5:
        raise ValueError("invalid LEEF header")
    version, vendor, product, product_version, event_code = parts[:5]
    return {"leef_version": version, "vendor": vendor, "product": product,
            "event_code": event_code, **kv_pairs(extension.replace("\t", " "))}


def parse_json(raw: str) -> dict:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("JSON event must be an object")
    return value


PARSERS = {"syslog": parse_syslog, "cef": parse_cef, "leef": parse_leef, "json": parse_json}


def load_sources(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["sources"]


def identify(parsed: dict, fmt: str, sources: list[dict]) -> dict:
    for source in sources:
        if source["format"] != fmt:
            continue
        match = source.get("match", {})
        field = match.get("field")
        expected = match.get("equals")
        if not field or str(parsed.get(field, "")).lower() == str(expected).lower():
            return source
    raise ValueError(f"no configured source for {fmt}")


def coerce(value, kind: str):
    if value in (None, ""):
        return None
    if kind == "int":
        return int(value)
    return str(value)


def normalize(raw: bytes, parsed: dict, fmt: str, source: dict) -> dict:
    event_id = str(uuid.uuid4())
    network = {}
    activity = {}
    for target, rule in source.get("map", {}).items():
        value = coerce(parsed.get(rule["from"]), rule.get("type", "str"))
        if value is None:
            continue
        (network if target in {"src_ip", "src_port", "dst_ip", "dst_port", "protocol"} else activity)[target] = value
    if not network.get("src_ip") or not network.get("dst_ip"):
        raise ValueError("network source and destination are required")
    used = {rule["from"] for rule in source.get("map", {}).values()}
    return {
        "event_id": event_id,
        "time": parsed.get("timestamp", now()),
        "ingested_at": now(),
        "source": {"id": source["id"], "format": fmt, "vendor": source.get("vendor", "unknown")},
        "network": network,
        "activity": activity,
        "unmapped": {key: value for key, value in parsed.items() if key not in used},
        "raw_ref": event_id,
    }


def save(event: dict, raw: bytes, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    raw_record = {"event_id": event["event_id"], "raw_b64": base64.b64encode(raw).decode("ascii")}
    with (output / "normalized.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")
    with (output / "raw.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(raw_record) + "\n")


def process_line(raw: bytes, sources: list[dict], output: Path) -> dict:
    text = raw.decode("utf-8", errors="replace")
    fmt = detect(text)
    if not fmt:
        raise ValueError("unknown log format")
    parsed = PARSERS[fmt](text)
    event = normalize(raw, parsed, fmt, identify(parsed, fmt, sources))
    save(event, raw, output)
    return event


def process_file(path: Path, sources: list[dict], output: Path) -> None:
    for line in path.read_bytes().splitlines(keepends=True):
        if not line.strip():
            continue
        try:
            event = process_line(line, sources, output)
            print(f"OK  {event['event_id']}  {event['source']['id']}")
        except Exception as error:
            print(f"SKIP  {error}")


def show(event_id: str, output: Path) -> None:
    normalized = next((json.loads(line) for line in (output / "normalized.jsonl").read_text().splitlines()
                       if json.loads(line)["event_id"] == event_id), None)
    raw = next((json.loads(line) for line in (output / "raw.jsonl").read_text().splitlines()
                if json.loads(line)["event_id"] == event_id), None)
    if not normalized or not raw:
        raise SystemExit("event not found")
    print("RAW:")
    print(base64.b64decode(raw["raw_b64"]).decode("utf-8", errors="replace"))
    print("NORMALIZED:")
    print(json.dumps(normalized, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple ULPF prototype")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    commands = parser.add_subparsers(dest="command", required=True)
    process = commands.add_parser("process", help="process one log file")
    process.add_argument("file", type=Path)
    show_command = commands.add_parser("show", help="show the raw and normalized pair")
    show_command.add_argument("event_id")
    args = parser.parse_args()
    if args.command == "process":
        process_file(args.file, load_sources(args.config), args.output)
    else:
        show(args.event_id, args.output)


if __name__ == "__main__":
    main()
