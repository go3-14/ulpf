from __future__ import annotations

import ipaddress
from datetime import datetime, timezone


class TransformError(Exception):
    pass


def to_str(v, spec): return str(v)
def to_int(v, spec): return int(str(v).strip())
def to_float(v, spec): return float(str(v).strip())


def to_bool(v, spec):
    value = str(v).strip().lower()
    if value in ("true", "1", "yes", "y", "allow"):
        return True
    if value in ("false", "0", "no", "n", "deny"):
        return False
    raise TransformError(f"not a boolean: {v!r}")


def to_ip(v, spec):
    return str(ipaddress.ip_address(str(v).strip()))


def to_port(v, spec):
    port = int(str(v).strip())
    if not 0 <= port <= 65535:
        raise TransformError(f"port out of range: {port}")
    return port


def to_enum(v, spec):
    values = spec.get("values") or {}
    key = str(v).strip()
    if key in values:
        return values[key]
    if key.lower() in values:
        return values[key.lower()]
    if "default" not in spec:
        raise TransformError(f"unmapped enum value {v!r} and no default")
    return spec["default"]


TRANSFORMS = {"str": to_str, "int": to_int, "float": to_float, "bool": to_bool, "ip": to_ip, "port": to_port, "enum": to_enum}


def apply_transform(value, spec):
    fn = TRANSFORMS.get(spec.get("type", "str"))
    if fn is None:
        raise TransformError(f"unknown transform type: {spec.get('type')}")
    return fn(value, spec)


def parse_time_ms(raw_value, time_cfg) -> int | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if text.isdigit():
        number = int(text)
        return number if number > 10**11 else number * 1000
    for fmt in time_cfg.get("formats", []):
        try:
            dt = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if dt.year == 1900 and time_cfg.get("assume_year") == "current":
            dt = dt.replace(year=datetime.now(timezone.utc).year)
        return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    try:
        return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None
