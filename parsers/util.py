import re


def unescape_value(s: str) -> str:
    """Alias kept for backward compatibility."""
    return unescape(s)


def unescape(value: str) -> str:
    return value.replace(r"\n", "\n").replace(r"\=", "=").replace(r"\|", "|").replace(r"\\", "\\")


def kv_extract(text: str, kv_delim: str = "=", item_delim: str | None = None) -> dict:
    """Extract key=value pairs from text.

    If item_delim is given (e.g., LEEF tab-delimited): splits on item_delim first.
    Otherwise uses finditer with a lookbehind to correctly detect key boundaries,
    handling CEF extension values that contain spaces or special characters.
    """
    res: dict[str, str] = {}
    if not text:
        return res

    if item_delim is not None:
        parts = text.split(item_delim)
        for part in parts:
            if kv_delim in part:
                k, v = part.split(kv_delim, 1)
                res[k.strip()] = unescape(v.strip())
        return res

    # finditer-based scan: each match is the start of a key=
    # The value extends from after '=' up to the start of the next key=
    # (?<!\S) ensures we only match keys at word boundaries (not mid-value)
    starts = list(re.finditer(r"(?<!\S)([A-Za-z][\w.\-]*)=", text))
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        res[match.group(1)] = unescape(text[match.end():end].strip())
    return res


def flatten(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Scalar-only lists are joined as CSV for cleaner OCSF output
            if all(not isinstance(elem, (dict, list)) for elem in v):
                items.append((new_key, ",".join(str(elem) for elem in v)))
            else:
                for i, elem in enumerate(v):
                    if isinstance(elem, dict):
                        items.extend(flatten(elem, f"{new_key}{sep}{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}{sep}{i}", str(elem)))
        else:
            items.append((new_key, v))
    return dict(items)
