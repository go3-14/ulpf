from __future__ import annotations

import re


def identify_source(parsed: dict, fmt: str, registry: dict) -> str | None:
    candidates = [config for config in registry.values() if config.get("format") == fmt]
    candidates.sort(key=lambda config: config.get("priority", 0), reverse=True)
    for config in candidates:
        match = config.get("match")
        if not match:
            return config["source"]
        conditions = match.get("all", [])
        if conditions and all(_matches(condition, parsed) for condition in conditions):
            return config["source"]
    return None


def _matches(condition: dict, parsed: dict) -> bool:
    value = parsed.get(condition["field"])
    if value is None:
        return False
    text = str(value)
    if "regex" in condition:
        return re.search(condition["regex"], text) is not None
    if "equals" in condition:
        return text == str(condition["equals"])
    if "contains" in condition:
        return str(condition["contains"]) in text
    return False
