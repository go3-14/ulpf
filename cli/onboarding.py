import json
from pathlib import Path
from parsers.detect import detect_format
from ingest.pipeline import PARSERS

def build_draft(sample: str, source_id: str = "new_source") -> dict:
    line = next((x for x in sample.splitlines() if x.strip()), "")
    fmt = detect_format(line) or "text"
    parsed = PARSERS[fmt](line) or {"message": line}
    field_map = {key: {"to": key, "type": "str"} for key in parsed}
    return {"source": source_id, "format": fmt, "field_map": field_map,
            "tests": [{"name": "review me", "raw": line, "expect": {}}]}

def write_draft(sample_path, source_id, output):
    import yaml
    draft = build_draft(Path(sample_path).read_text(encoding="utf-8"), source_id)
    Path(output).write_text(yaml.safe_dump(draft, sort_keys=False), encoding="utf-8")
    return draft
