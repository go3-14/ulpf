from __future__ import annotations

from schema.ocsf_base import build_base
from schema.transforms import TransformError, apply_transform, parse_time_ms


def set_nested(target: dict, dotted: str, value) -> None:
    keys = dotted.split(".")
    current = target
    for key in keys[:-1]:
        if not isinstance(current.get(key), dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def normalize(parsed: dict, config: dict, event_id: str, source_id: str, fmt: str) -> dict:
    output = build_base(config, event_id)
    consumed: set[str] = set()
    for path, value in (config.get("constants") or {}).items():
        set_nested(output, path, value)

    time_cfg = config.get("time") or {}
    time_field = time_cfg.get("field")
    if time_field and time_field in parsed:
        consumed.add(time_field)
        set_nested(output, "metadata.original_time", str(parsed[time_field]))
        output["time"] = parse_time_ms(parsed[time_field], time_cfg) or output["metadata"]["logged_time"]
    else:
        output["time"] = output["metadata"]["logged_time"]

    errors: list[str] = []
    for source_key, spec in (config.get("field_map") or {}).items():
        if source_key not in parsed or parsed[source_key] in (None, ""):
            continue
        try:
            set_nested(output, spec["to"], apply_transform(parsed[source_key], spec))
            consumed.add(source_key)
        except (TransformError, ValueError, TypeError) as exc:
            errors.append(f"{source_key}->{spec['to']}: {exc}")

    for path, value in (config.get("defaults") or {}).items():
        current = output
        keys = path.split(".")
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        if keys[-1] not in current:
            current[keys[-1]] = value
    output["type_uid"] = output["class_uid"] * 100 + output.get("activity_id", 99)
    leftover = {key: value for key, value in parsed.items() if key not in consumed}
    if errors:
        leftover["_ulpf_transform_errors"] = errors
    if leftover:
        output["unmapped"] = leftover
    output["metadata"]["labels"] = ["ulpf", source_id, fmt]
    return output
