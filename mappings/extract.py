import csv
import json
import re
import shlex

def _flatten(value, prefix, out):
    if isinstance(value, dict):
        for key, item in value.items():
            if prefix and (prefix.endswith("_") or prefix.endswith(".")):
                name = f"{prefix}{key}"
            else:
                name = f"{prefix}.{key}" if prefix else str(key)
            _flatten(item, name, out)
    elif isinstance(value, list):
        for i, item in enumerate(value): _flatten(item, f"{prefix}[{i}]", out)
    else: out[prefix] = value

def apply_extracts(parsed: dict, rules: list[dict]) -> dict:
    for rule in rules or []:
        guard = rule.get("when")
        if guard:
            from mappings.matcher import condition_matches
            if not condition_matches(guard, parsed): continue
        field = rule.get("field", "message")
        value = parsed.get(field)
        if value is None: continue
        value = str(value)[:int(rule.get("max_len", 8192))]
        kind = rule.get("type", "regex")
        produced = {}
        prefix = rule.get("prefix", "")
        if kind == "regex":
            flags = 0
            for name in rule.get("flags", []): flags |= getattr(re, name, 0)
            match = re.search(rule.get("regex", ""), value, flags)
            if match: produced = {prefix + k: v for k, v in match.groupdict().items() if v is not None}
        elif kind == "kv":
            tokens = shlex.split(value)
            counts = {}
            for token in tokens:
                sep = rule.get("kv_sep", "=")
                if sep not in token: continue
                key, val = token.split(sep, 1)
                if not re.fullmatch(r"[A-Za-z0-9_.-]+", key): continue
                counts[key] = counts.get(key, 0) + 1
                name = key if counts[key] == 1 else f"{key}__{counts[key]}"
                produced[prefix + name] = val
        elif kind == "split":
            params = rule.get("params", rule)
            sep = params.get("sep", ",")
            values = next(csv.reader([value], delimiter=sep), []) if params.get("csv") else value.split(sep)
            names = params.get("names", [])
            for i, item in enumerate(values): produced[prefix + (names[i] if i < len(names) else f"col_{i}")] = item
        elif kind == "json":
            try: _flatten(json.loads(value), prefix, produced)
            except (TypeError, ValueError, json.JSONDecodeError): pass
        for key, item in produced.items():
            if rule.get("on_conflict", "keep") == "overwrite" or key not in parsed: parsed[key] = item
    return parsed
