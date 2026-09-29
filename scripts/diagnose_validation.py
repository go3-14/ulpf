"""Validate a real normalized sample against the intact bundled OCSF schema."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingest.pipeline import process
from storage.normalized_store import get_normalized


SCHEMA = ROOT / "schema" / "ocsf" / "classes" / "network_activity.json"
SAMPLE = ROOT / "samples" / "cisco_asa_syslog.log"


def main() -> int:
    raw = next(line for line in SAMPLE.read_bytes().splitlines() if line.strip())
    event_id = process(raw)
    if not event_id:
        print("NORMALIZATION FAILED")
        return 1
    event = get_normalized(event_id)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(event),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    print(f"event_id: {event_id}")
    print(f"top_level_keys: {sorted(event)}")
    if not errors:
        print("VALID: no schema errors")
        return 0
    for error in errors:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        print(f"{pointer or '/'}: {error.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
