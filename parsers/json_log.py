import json
from parsers.util import flatten

def parse_json(raw_log: str) -> dict | None:
    s = raw_log.strip()
    if not s or not (s.startswith("{") or s.startswith("[")):
        return None
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return flatten(parsed)
        return None
    except json.JSONDecodeError:
        return None
