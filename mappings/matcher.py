import re


def _cond_matches(cond: dict, parsed: dict) -> bool:
    value = parsed.get(cond["field"])
    if value is None:
        return False
    s = str(value)
    if "regex" in cond:
        return re.search(cond["regex"], s) is not None
    if "equals" in cond:
        return s == str(cond["equals"])
    if "contains" in cond:
        return str(cond["contains"]) in s
    return False


def identify_source(parsed: dict, fmt: str, registry: dict) -> str | None:
    candidates = [c for c in registry.values() if c.get("format") == fmt]
    candidates.sort(key=lambda c: c.get("priority", 0), reverse=True)
    for cfg in candidates:
        match = cfg.get("match")
        if not match:
            return cfg["source"]
        conds = match.get("all", [])
        if conds and all(_cond_matches(c, parsed) for c in conds):
            return cfg["source"]
    return None
