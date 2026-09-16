from parsers.util import kv_extract


def _decode_delim(raw: str | None) -> str:
    if not raw:
        return "\t"
    if raw == r"\t":
        return "\t"
    if raw.lower().startswith("x"):
        try:
            return chr(int(raw[1:], 16))
        except ValueError:
            return raw
    return raw


def parse_leef(raw_log: str) -> dict | None:
    s = raw_log.strip()
    if not s.startswith("LEEF:"):
        return None
    pieces = s.split("|", 5)
    if len(pieces) < 5:
        return None

    out = {
        "leef_version": pieces[0].split(":", 1)[1],
        "device_vendor": pieces[1],
        "device_product": pieces[2],
        "device_version": pieces[3],
        "event_id": pieces[4],
    }

    if len(pieces) == 5:
        if "\t" not in out["event_id"]:
            return None
        delimiter = "\t"
        out["event_id"], body = out["event_id"].split("\t", 1)
    else:
        rest = pieces[5]
        if "|" in rest:
            raw_delim, body = rest.split("|", 1)
            delimiter = _decode_delim(raw_delim)
        else:
            delimiter = "\t"
            body = rest

    out.update(kv_extract(body, delimiter))
    return out
