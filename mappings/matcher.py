import re

def condition_matches(cond: dict, parsed: dict) -> bool:
    if not cond:
        return True
    if "all" in cond:
        return all(condition_matches(item, parsed) for item in cond["all"])
    if "any" in cond:
        return any(condition_matches(item, parsed) for item in cond["any"])
    if "not" in cond:
        return not condition_matches(cond["not"], parsed)
    field = cond.get("field")
    value = parsed.get(field) if field is not None else None
    if "exists" in cond:
        return (field in parsed and value is not None) == bool(cond["exists"])
    if value is None:
        return False
    s = str(value)
    if "regex" in cond:
        compiled = cond.get("_compiled_regex")
        return (compiled or re.compile(cond["regex"])).search(s) is not None
    if "equals" in cond:
        return value == cond["equals"] or s.casefold() == str(cond["equals"]).casefold()
    if "startswith" in cond:
        return s.startswith(str(cond["startswith"]))
    if "contains" in cond:
        return str(cond["contains"]) in s
    if "in" in cond:
        return value in cond["in"] or s in {str(item) for item in cond["in"]}
    return False

_cond_matches = condition_matches

def identify_source(parsed: dict, fmt: str, registry: dict) -> str | None:
    """Highest-priority config whose format matches and whose conditions hold."""
    candidates = [c for c in registry.values() if c.get("format") == fmt]
    candidates.sort(key=lambda c: (-c.get("priority", 0), c.get("source", "")))
    for cfg in candidates:
        match = cfg.get("match")
        if not match:
            return cfg["source"]
        conds = match.get("all", [])
        if condition_matches(match, parsed) if match else True:
            return cfg["source"]
    return None
