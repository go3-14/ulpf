from __future__ import annotations

import re


def kv_extract(text: str, delimiter: str | None = None) -> dict[str, str]:
    """Extract key/value extensions from CEF-style or delimiter-separated text."""
    result: dict[str, str] = {}
    if delimiter is not None:
        chunks = text.split(delimiter)
        for chunk in chunks:
            if "=" not in chunk:
                continue
            key, value = chunk.split("=", 1)
            key = key.strip()
            if key:
                result[key] = unescape(value.strip())
        return result

    starts = list(re.finditer(r"(?<!\S)([A-Za-z][\w.-]*)=", text))
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        result[match.group(1)] = unescape(text[match.end() : end].strip())
    return result


def unescape(value: str) -> str:
    return value.replace(r"\n", "\n").replace(r"\=", "=").replace(r"\|", "|").replace(r"\\", "\\")


def flatten(value: object, prefix: str = "") -> dict[str, object]:
    result: dict[str, object] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten(child, path))
    elif isinstance(value, list):
        if all(not isinstance(child, (dict, list)) for child in value):
            result[prefix] = ",".join(str(child) for child in value)
        else:
            for index, child in enumerate(value):
                result.update(flatten(child, f"{prefix}.{index}"))
    else:
        result[prefix] = value
    return result
