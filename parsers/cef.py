from __future__ import annotations

import re

from parsers.util import kv_extract, unescape

SYSLOG_PREFIX_RE = re.compile(
    r"^(?:<(?P<pri>\d{1,3})>)?(?P<timestamp>[A-Z][a-z]{2}\s{1,2}\d{1,2}\s\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+(?P<payload>CEF:.*)$"
)


def _strip_header(raw: str) -> tuple[str, dict]:
    match = SYSLOG_PREFIX_RE.match(raw.strip())
    if not match:
        return raw.strip(), {}
    header = {key: value for key, value in match.groupdict().items() if key != "payload"}
    if header.get("pri") is not None:
        pri = int(header["pri"])
        header["pri"], header["facility"], header["severity"] = pri, pri // 8, pri % 8
    return match.group("payload"), header


def parse_cef(raw: str) -> dict | None:
    payload, header = _strip_header(raw)
    if not payload.startswith("CEF:"):
        return None
    fields = re.split(r"(?<!\\)\|", payload, maxsplit=7)
    if len(fields) < 8:
        return None
    if not fields[0].startswith("CEF:"):
        return None
    result = {
        **header,
        "cef_version": unescape(fields[0][4:]),
        "device_vendor": unescape(fields[1]),
        "device_product": unescape(fields[2]),
        "device_version": unescape(fields[3]),
        "signature_id": unescape(fields[4]),
        "name": unescape(fields[5]),
        "cef_severity": unescape(fields[6]),
    }
    result.update(kv_extract(fields[7]))
    result["vendor_hint"] = f"{result['device_vendor']}_{result['device_product']}"
    return result
