import re


KV_KEY_RE = re.compile(r"(?<!\\)([A-Za-z0-9_.:-]+)=")


def unescape(value: str) -> str:
    return (
        value.replace(r"\n", "\n")
        .replace(r"\=", "=")
        .replace(r"\|", "|")
        .replace(r"\\", "\\")
    )


def kv_extract(text: str, pair_sep: str | None = None) -> dict:
    if pair_sep is not None:
        out = {}
        for part in text.split(pair_sep):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            if key:
                out[key] = unescape(value.strip())
        return out

    matches = list(KV_KEY_RE.finditer(text))
    out = {}
    for idx, match in enumerate(matches):
        key = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        value = text[start:end].strip()
        if value:
            out[key] = unescape(value)
    return out


def flatten(value, prefix: str = "") -> dict:
    out = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten(child, child_key))
    elif isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            out[prefix] = ",".join(str(item) for item in value)
        else:
            for idx, child in enumerate(value):
                out.update(flatten(child, f"{prefix}.{idx}"))
    else:
        out[prefix] = value
    return out
