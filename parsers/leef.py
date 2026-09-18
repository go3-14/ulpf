import re
from parsers.util import unescape_value

LEEF_PREFIX_RE = re.compile(
    r'^(?:<(?P<pri>\d{1,3})>)?\s*'
    r'(?:(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+)?'
    r'(?:(?P<hostname>[\w.\-]+)\s+)?'
    r'LEEF:(?P<leef_body>.*)$'
)

def parse_leef(raw_log: str) -> dict | None:
    s = raw_log.strip()
    if not s or "LEEF:" not in s:
        return None

    res = {}
    m = LEEF_PREFIX_RE.match(s)
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

    leef_body = gd.get("leef_body", "")

    # Split header on unescaped pipe |
    parts = re.split(r'(?<!\\)\|', leef_body)
    if len(parts) < 5:
        return None

    res["leef_version"] = parts[0]
    res["vendor"] = parts[1]
    res["product"] = parts[2]
    res["product_version"] = parts[3]
    res["event_id"] = parts[4]

    res["vendor_hint"] = f"{parts[1]}_{parts[2]}"

    delimiter = None
    extension_part_index = 5

    if parts[0] == "2.0" and len(parts) >= 6:
        raw_delim = parts[5]
        if raw_delim in ("\\t", "x09", "0x09"):
            delimiter = "\t"
            extension_part_index = 6
        elif len(raw_delim) == 1 and "=" not in raw_delim:
            delimiter = raw_delim
            extension_part_index = 6
        elif len(parts) > 6 and all("=" in part for part in parts[5:]):
            # Some devices emit a LEEF 2.0 header but retain the legacy pipe
            # extension delimiter. Infer it only when multiple key/value
            # segments make the intent unambiguous.
            delimiter = "|"
            extension_part_index = 5
        else:
            # LEEF 2.0 requires an explicit delimiter field; do not silently
            # reinterpret the first extension attribute as a delimiter.
            return None
    elif parts[0] == "2.0":
        return None

    extension_str = "|".join(parts[extension_part_index:]) if len(parts) > extension_part_index else ""

    if extension_str:
        # Dynamic delimiter detection if not explicitly specified in header
        if not delimiter:
            if "\t" in extension_str:
                delimiter = "\t"
            elif "^" in extension_str:
                delimiter = "^"
            elif "|" in extension_str:
                delimiter = "|"
            else:
                delimiter = "\t"

        pairs = extension_str.split(delimiter)
        for p in pairs:
            if "=" in p:
                k, v = p.split("=", 1)
                res[k.strip()] = unescape_value(v.strip())

    return res
