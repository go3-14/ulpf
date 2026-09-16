import json

from parsers.util import flatten


def parse_json(raw_log: str) -> dict | None:
    try:
        parsed = json.loads(raw_log)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return flatten(parsed)
