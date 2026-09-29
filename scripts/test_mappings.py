"""Run declarative mapping golden tests without network access."""
import argparse
import pathlib
from mappings.loader import load_mappings
from ingest.pipeline import PARSERS
from parsers.detect import detect_format
from schema.normalize import normalize
from schema.validate import validate_event

def _get_path(value, path):
    for part in path.split("."):
        value = value[part]
    return value

def run(directory=None, mapping_id=None):
    results = []
    for source, mapping in load_mappings(directory).items():
        if mapping_id and source != mapping_id:
            continue
        for case in mapping.get("tests", []):
            raw = case["raw"]
            fmt = mapping.get("format") or detect_format(raw)
            parsed = PARSERS[fmt](raw)
            event = normalize(parsed, mapping, "mapping-test", source, fmt)
            validate_event(event)
            for path, expected in (case.get("expect") or {}).items():
                actual = _get_path(event, path)
                if actual != expected:
                    raise AssertionError(f"{source}/{case.get('name')}: {path}: {actual!r} != {expected!r}")
            for path in case.get("expect_absent", []):
                try: _get_path(event, path)
                except (KeyError, TypeError): continue
                raise AssertionError(f"{source}/{case.get('name')}: {path} unexpectedly present")
            results.append((source, case.get("name", "unnamed")))
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping")
    parser.add_argument("--directory")
    args = parser.parse_args()
    results = run(args.directory, args.mapping)
    print(f"passed {len(results)} mapping golden tests")

if __name__ == "__main__":
    main()
