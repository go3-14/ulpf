import ipaddress
from datetime import datetime, timezone

class TransformError(Exception):
    pass

def to_str(v, spec):
    return str(v)

def to_int(v, spec):
    return int(str(v).strip())

def to_float(v, spec):
    return float(str(v).strip())

def to_bool(v, spec):
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "y", "allow", "built"):
        return True
    if s in ("false", "0", "no", "n", "deny", "denied", "teardown", "reset"):
        return False
    raise TransformError(f"not a boolean: {v!r}")

def to_ip(v, spec):
    return str(ipaddress.ip_address(str(v).strip()))

def to_port(v, spec):
    p = int(str(v).strip())
    if not 0 <= p <= 65535:
        raise TransformError(f"port out of range: {p}")
    return p

def to_enum(v, spec):
    values = spec.get("values") or {}
    key = str(v).strip()
    if key in values:
        return values[key]
    if key.lower() in values:
        return values[key.lower()]
    if "default" in spec:
        return spec["default"]
    raise TransformError(f"unmapped enum value {v!r} and no default")

TRANSFORMS = {
    "str": to_str,
    "int": to_int,
    "float": to_float,
    "bool": to_bool,
    "ip": to_ip,
    "port": to_port,
    "enum": to_enum,
}

def apply_transform(value, spec):
    t = spec.get("type", "str")
    fn = TRANSFORMS.get(t)
    if fn is None:
        raise TransformError(f"unknown transform type: {t}")
    return fn(value, spec)

def parse_time_ms(raw_value, time_cfg) -> int | None:
    """Return epoch milliseconds, or None if unparseable."""
    if raw_value is None:
        return None
    s = str(raw_value).strip()
    if s.isdigit():
        n = int(s)
        return n if n > 10**11 else n * 1000
    for fmt in time_cfg.get("formats", []):
        try:
            dt = datetime.strptime(s, fmt)
        except ValueError:
            continue
        if dt.year == 1900 and time_cfg.get("assume_year") == "current":
            dt = dt.replace(year=datetime.now(timezone.utc).year)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    try:
        return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None
