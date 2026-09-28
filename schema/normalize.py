from schema.ocsf_base import build_base
from schema.transforms import apply_transform, parse_time_ms, TransformError

def set_nested(d: dict, dotted: str, value) -> None:
    keys = dotted.split(".")
    for k in keys[:-1]:
        nxt = d.get(k)
        if not isinstance(nxt, dict):
            nxt = {}
            d[k] = nxt
        d = nxt
    d[keys[-1]] = value

def deep_merge(base: dict, overlay: dict) -> dict:
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base

def normalize(parsed: dict, config: dict, event_id: str,
              source_id: str, fmt: str) -> dict:
    out = build_base(config, event_id)
    out["mapping_version"] = config.get("mapping_version", "1")
    consumed = set()

    # 1. constants
    for path, value in (config.get("constants") or {}).items():
        set_nested(out, path, value)

    # 2. time
    time_cfg = config.get("time") or {}
    tfield = time_cfg.get("field")
    ms = None
    if tfield and tfield in parsed:
        consumed.add(tfield)
        set_nested(out, "metadata.original_time", str(parsed[tfield]))
        ms = parse_time_ms(parsed[tfield], time_cfg)
    out["time"] = ms if ms is not None else out["metadata"]["logged_time"]

    # 3. field map
    transform_errors = []
    for src_key, spec in (config.get("field_map") or {}).items():
        if src_key not in parsed:
            continue
        consumed.add(src_key)
        value = parsed[src_key]
        if value in (None, ""):
            continue
        try:
            set_nested(out, spec["to"], apply_transform(value, spec))
        except (TransformError, ValueError) as e:
            transform_errors.append(f"{src_key}->{spec['to']}: {e}")
            consumed.discard(src_key)

    # 4. defaults for anything the source didn't supply
    for path, value in (config.get("defaults") or {}).items():
        cur, keys = out, path.split(".")
        for k in keys[:-1]:
            cur = cur.get(k) if isinstance(cur.get(k), dict) else {}
        if keys[-1] not in cur:
            set_nested(out, path, value)

    # 5. derived type_uid — always engine-computed
    out["type_uid"] = out["class_uid"] * 100 + out.get("activity_id", 99)

    # 6. unmapped: everything the config didn't consume (requirement a)
    leftover = {k: v for k, v in parsed.items() if k not in consumed}
    if leftover:
        out["unmapped"] = leftover
    if transform_errors:
        out.setdefault("unmapped", {})["_ulpf_transform_errors"] = transform_errors

    # 7. provenance labels
    out["metadata"]["labels"] = ["ulpf", source_id, fmt]
    return out
