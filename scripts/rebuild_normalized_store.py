"""Rebuild normalized records with the currently bundled OCSF schema.

The command preserves raw files, the raw index, and every existing event ID. It
builds a complete replacement beside the live normalized directory and swaps it
into place only after every raw record has parsed, normalized, and validated.
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
import time
from pathlib import Path

# Support both ``python -m scripts.rebuild_normalized_store`` and direct
# execution via ``python scripts/rebuild_normalized_store.py``.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest.pipeline import PARSERS
from mappings.loader import load_mappings
from parsers.detect import detect_format
from schema.normalize import normalize
from schema.validate import validate_event


def _raw_bytes(record: dict) -> bytes:
    if record.get("raw_encoding") == "base64":
        return base64.b64decode(record["raw_b64"])
    return str(record["raw"]).encode("utf-8")


def rebuild_normalized_store(
    storage_dir: Path, staging_dir: Path, mapping_dir: Path | None = None
) -> int:
    """Build ``staging_dir/normalized`` and return the rebuilt record count."""
    raw_dir = storage_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"raw store does not exist: {raw_dir}")
    if staging_dir.exists():
        raise FileExistsError(f"staging directory already exists: {staging_dir}")

    mappings = load_mappings(mapping_dir)
    count = 0
    try:
        for raw_path in sorted(raw_dir.rglob("*.ndjson")):
            relative = raw_path.relative_to(raw_dir)
            destination = staging_dir / "normalized" / relative
            destination = destination.with_name(destination.name.replace("raw-", "events-", 1))
            destination.parent.mkdir(parents=True, exist_ok=True)

            with raw_path.open("r", encoding="utf-8") as source, destination.open(
                "a", encoding="utf-8"
            ) as target:
                for line_number, line in enumerate(source, 1):
                    try:
                        record = json.loads(line)
                        event_id = record["event_id"]
                        source_id = record["source_id"]
                        raw_bytes = _raw_bytes(record)
                        raw_text = raw_bytes.decode("utf-8", errors="replace").strip()
                        fmt = detect_format(raw_text)
                        parser = PARSERS.get(fmt)
                        mapping = mappings.get(source_id)
                        if not fmt or parser is None:
                            raise ValueError(f"unrecognized format: {fmt}")
                        if mapping is None:
                            raise ValueError(f"mapping not found: {source_id}")
                        parsed = parser(raw_text)
                        if parsed is None:
                            raise ValueError(f"failed to parse as {fmt}")
                        normalized = normalize(parsed, mapping, event_id, source_id, fmt)
                        validate_event(normalized)
                    except Exception as exc:
                        raise RuntimeError(f"{raw_path}:{line_number}: {exc}") from exc
                    target.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                    count += 1
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    return count


def replace_normalized_store(storage_dir: Path, staging_dir: Path) -> None:
    """Atomically swap a validated staging tree into the live storage root."""
    live = storage_dir / "normalized"
    backup = storage_dir / f".normalized-legacy-{time.time_ns()}"
    moved_live = False
    try:
        if live.exists():
            live.replace(backup)
            moved_live = True
        (staging_dir / "normalized").replace(live)
    except Exception:
        if moved_live and not live.exists():
            backup.replace(live)
        raise
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-dir", type=Path, default=None)
    parser.add_argument(
        "--mapping-dir",
        type=Path,
        default=None,
        help="Explicit directory containing mappings for historical source IDs",
    )
    args = parser.parse_args()

    if args.storage_dir is None:
        import config

        storage_dir = Path(config.STORAGE_DIR)
    else:
        storage_dir = args.storage_dir.resolve()
    staging_dir = storage_dir.parent / f".{storage_dir.name}-normalized-rebuild"
    count = rebuild_normalized_store(storage_dir, staging_dir, args.mapping_dir)
    replace_normalized_store(storage_dir, staging_dir)
    print(f"Rebuilt {count} normalized records with OCSF 1.9.0")


if __name__ == "__main__":
    main()
