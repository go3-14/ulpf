import re

from parsers.util import kv_extract


SYSLOG_PREFIX_RE = re.compile(
    r"^<(?P<pri>\d{1,3})>(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+(?P<body>CEF:.*)$"
)


def _split_unescaped_pipe(text: str, maxsplit: int) -> list[str]:
    parts = []
    current = []
    escaped = False
    for ch in text:
        if ch == "\\" and not escaped:
            escaped = True
            current.append(ch)
            continue
        if ch == "|" and not escaped and len(parts) < maxsplit:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        escaped = False
    parts.append("".join(current))
    return parts


def parse_cef(raw_log: str) -> dict | None:
    s = raw_log.strip()
    out = {}
    prefix = SYSLOG_PREFIX_RE.match(s)
    if prefix:
        out.update({k: v for k, v in prefix.groupdict().items() if k != "body"})
        pri = int(out["pri"])
        out["facility"] = pri // 8
        out["severity"] = pri % 8
        s = prefix.group("body")

    if not s.startswith("CEF:"):
        return None

    parts = _split_unescaped_pipe(s, 7)
    if len(parts) < 8:
        return None

    out.update(
        {
            "cef_version": parts[0].split(":", 1)[1],
            "device_vendor": parts[1],
            "device_product": parts[2],
            "device_version": parts[3],
            "signature_id": parts[4],
            "name": parts[5],
            "cef_severity": parts[6],
            "vendor_hint": f"{parts[1]}_{parts[2]}",
        }
    )
    out.update(kv_extract(parts[7]))
    return out
