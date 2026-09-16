import re
from parsers.util import unescape_value

CEF_PREFIX_RE = re.compile(
    r'^(?:<(?P<pri>\d{1,3})>)?\s*'
    r'(?:(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+)?'
    r'(?:(?P<hostname>[\w.\-]+)\s+)?'
    r'CEF:(?P<cef_body>.*)$'
)


def parse_cef(raw_log: str) -> dict | None:
    s = raw_log.strip()
    if not s or "CEF:" not in s:
        return None

    res = {}
    m = CEF_PREFIX_RE.match(s)
    if not m:
        return None

    gd = m.groupdict()
    if gd.get("pri"):
        pri = int(gd["pri"])
        res["pri"] = pri
        res["facility"] = pri // 8
        res["severity"] = pri % 8

    if gd.get("timestamp"):
        res["timestamp"] = gd["timestamp"]
    if gd.get("hostname"):
        res["hostname"] = gd["hostname"]

    cef_body = gd.get("cef_body", "")

    # Split header on unescaped pipe |
    parts = re.split(r'(?<!\\)\|', cef_body)
    if len(parts) < 7:
        return None

    res["cef_version"] = parts[0]
    res["device_vendor"] = parts[1]
    res["device_product"] = parts[2]
    res["device_version"] = parts[3]
    res["signature_id"] = parts[4]
    res["name"] = parts[5]
    res["cef_severity"] = parts[6]

    res["vendor_hint"] = f"{parts[1]}_{parts[2]}"

    extension_str = "|".join(parts[7:]) if len(parts) > 7 else ""
    if extension_str:
        kv_pattern = re.compile(r'(\b[\w.\-]+)=')
        matches = list(kv_pattern.finditer(extension_str))
        for i, match in enumerate(matches):
            k = match.group(1)
            start_val = match.end()
            end_val = matches[i + 1].start() if i + 1 < len(matches) else len(extension_str)
            v = extension_str[start_val:end_val].strip()
            res[k] = unescape_value(v)

    return res
