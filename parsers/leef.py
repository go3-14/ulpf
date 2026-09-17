from __future__ import annotations

from parsers.util import kv_extract


def _decode_delimiter(value: str) -> str | None:
    if value == r"\t":
        return "\t"
    if len(value) == 1:
        return value
    if len(value) == 3 and value[0].lower() == "x":
        try:
            return chr(int(value[1:], 16))
        except ValueError:
            return None
    return None


def parse_leef(raw: str) -> dict | None:
    text = raw.strip()
    if not text.startswith("LEEF:"):
        return None
    header_parts = text.split("|", 5)
    if len(header_parts) < 6:
        return None
    version = header_parts[0][5:]
    result = {
        "leef_version": version,
        "vendor": header_parts[1],
        "product": header_parts[2],
        "product_version": header_parts[3],
        "event_id": header_parts[4],
    }
    remainder = header_parts[5]
    if version.startswith("2."):
        if "|" not in remainder:
            return None
        delimiter_value, body = remainder.split("|", 1)
        delimiter = _decode_delimiter(delimiter_value)
        if delimiter is None:
            return None
    else:
        delimiter, body = "\t", remainder
    result.update(kv_extract(body, delimiter))
    return result
