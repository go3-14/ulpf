from __future__ import annotations

import json

from parsers.util import flatten


def parse_json(raw: str) -> dict | None:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    return flatten(value)
