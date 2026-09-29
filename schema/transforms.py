import ipaddress
import re
from datetime import datetime, timedelta, timezone
from numbers import Real
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
    folded = spec.get("_folded_values")
    if folded is None:
        folded = compile_enum_values(spec.get("values") or {})
    key = str(v).strip().casefold()
    if key in folded:
        return folded[key]
    if "default" in spec:
        return spec["default"]
    raise TransformError(f"unmapped enum value {v!r} and no default")


def compile_enum_values(values: dict) -> dict:
    folded = {}
    originals = {}
    for original, result in values.items():
        key = str(original).strip().casefold()
        if key in folded:
            raise ValueError(
                f"enum keys collide after case-folding: {originals[key]!r} and {original!r}"
            )
        folded[key] = result
        originals[key] = original
    return folded

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

_MONTHS = {
    name.casefold(): number
    for number, names in enumerate(
        (("January", "Jan"), ("February", "Feb"), ("March", "Mar"),
         ("April", "Apr"), ("May", "May"), ("June", "Jun"),
         ("July", "Jul"), ("August", "Aug"), ("September", "Sep"),
         ("October", "Oct"), ("November", "Nov"), ("December", "Dec")),
        start=1,
    )
    for name in names
}


def _month_safe(value: str, fmt: str) -> tuple[str, str]:
    """Convert English month directives to numeric directives."""
    if "%b" not in fmt and "%B" not in fmt:
        return value, fmt

    def replace(match: re.Match[str]) -> str:
        month = _MONTHS.get(match.group(0).casefold())
        return f"{month:02d}" if month else match.group(0)

    return re.sub(r"[A-Za-z]+", replace, value), fmt.replace("%B", "%m").replace("%b", "%m")


def _timezone(value: str | None):
    if not value or value.upper() == "UTC":
        return timezone.utc
    match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", value)
    if match:
        minutes = int(match.group(2)) * 60 + int(match.group(3))
        if match.group(1) == "-":
            minutes = -minutes
        return timezone(timedelta(minutes=minutes))
    try:
        return ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise TransformError(f"unknown timezone: {value}") from exc


def _to_epoch_ms(number: Real) -> int:
    magnitude = abs(float(number))
    if magnitude < 1e11:
        scale = 1_000
    elif magnitude < 1e14:
        scale = 1
    elif magnitude < 1e17:
        scale = 1e-3
    else:
        scale = 1e-6
    return int(float(number) * scale)


def parse_time_ms(raw_value, time_cfg, reference_ms: int | None = None) -> int:
    """Parse a timestamp deterministically and return epoch milliseconds."""
    if raw_value is None:
        raise TransformError("timestamp is missing")
    if isinstance(raw_value, Real) and not isinstance(raw_value, bool):
        return _to_epoch_ms(raw_value)

    s = str(raw_value).strip()
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", s):
        return _to_epoch_ms(float(s))

    cfg = time_cfg or {}
    local_tz = _timezone(cfg.get("timezone"))
    try:
        iso = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        iso = None
    if iso is not None:
        if iso.tzinfo is None:
            iso = iso.replace(tzinfo=local_tz)
        return int(iso.timestamp() * 1000)

    reference = datetime.fromtimestamp(reference_ms / 1000, tz=timezone.utc) if reference_ms is not None else datetime.fromtimestamp(0, tz=timezone.utc)
    for original_fmt in cfg.get("formats", []):
        value, fmt = _month_safe(s, original_fmt)
        yearless = not any(token in original_fmt for token in ("%Y", "%y", "%G"))
        candidates = range(reference.year, reference.year - 5, -1) if yearless else (None,)
        for year in candidates:
            candidate_value, candidate_fmt = value, fmt
            if year is not None:
                candidate_value = f"{year} {value}"
                candidate_fmt = f"%Y {fmt}"
            try:
                parsed = datetime.strptime(candidate_value, candidate_fmt)
            except ValueError:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=local_tz)
            if year is not None and parsed > reference + timedelta(days=1):
                continue
            return int(parsed.timestamp() * 1000)

    raise TransformError(f"unparseable timestamp: {raw_value!r}")
