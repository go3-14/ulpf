import re
from parsers.util import kv_extract, unescape

# Matches optional syslog envelope before the CEF: payload
_SYSLOG_PREFIX_RE = re.compile(
    r'^(?:<(?P<pri>\d{1,3})>)?\s*'
    r'(?:(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+)?'
    r'(?:(?P<hostname>[\w.\-]+)\s+)?'
    r'CEF:(?P<cef_body>.*)$'
)


def _strip_header(raw: str) -> tuple[dict, str] | None:
    """Strip syslog envelope and return (header_fields, cef_body_string).

    header_fields contains: pri, facility, severity, timestamp, hostname (when present).
    Returns None if the string doesn't contain a CEF: marker.
    """
    s = raw.strip()
    if "CEF:" not in s:
        return None
    m = _SYSLOG_PREFIX_RE.match(s)
    if not m:
        return None

    gd = m.groupdict()
    header: dict = {}
    if gd.get("pri"):
        pri = int(gd["pri"])
        header["pri"] = pri
        header["facility"] = pri // 8
        header["severity"] = pri % 8
    if gd.get("timestamp"):
        header["timestamp"] = gd["timestamp"]
    if gd.get("hostname"):
        header["hostname"] = gd["hostname"]

    return header, gd.get("cef_body", "")


def parse_cef(raw_log: str) -> dict | None:
    result = _strip_header(raw_log)
    if result is None:
        return None

    header, cef_body = result

    # Split the CEF header (7 fixed fields) from the extension block.
    # maxsplit=7 is critical: the extension block (fields[7]) can legitimately
    # contain unescaped pipe characters in values — we must NOT split on those.
    fields = re.split(r'(?<!\\)\|', cef_body, maxsplit=7)
    if len(fields) < 7:
        return None

    res = dict(header)  # start with syslog envelope fields
    res["cef_version"]    = unescape(fields[0])
    res["device_vendor"]  = unescape(fields[1])
    res["device_product"] = unescape(fields[2])
    res["device_version"] = unescape(fields[3])
    res["signature_id"]   = unescape(fields[4])
    res["name"]           = unescape(fields[5])
    res["cef_severity"]   = unescape(fields[6])
    res["vendor_hint"]    = f"{fields[1]}_{fields[2]}"

    if len(fields) > 7 and fields[7].strip():
        # fields[7] is the raw extension block — parse KV pairs from it
        extension = fields[7]
        res.update(kv_extract(extension))

    return res
