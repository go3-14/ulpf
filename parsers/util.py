import re

def unescape_value(s: str) -> str:
    if not s:
        return ""
    return s.replace("\\=", "=").replace("\\|", "|").replace("\\\\", "\\").replace("\\n", "\n")

def kv_extract(text: str, kv_delim="=", item_delim=None) -> dict:
    res = {}
    if not text:
        return res
    
    if item_delim:
        parts = text.split(item_delim)
        for part in parts:
            if kv_delim in part:
                k, v = part.split(kv_delim, 1)
                res[k.strip()] = unescape_value(v.strip())
        return res

    pattern = re.compile(r'(\b[\w.\-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+))')
    for match in pattern.finditer(text):
        k = match.group(1)
        v = match.group(2) if match.group(2) is not None else (
            match.group(3) if match.group(3) is not None else match.group(4)
        )
        res[k] = unescape_value(v)
    return res

def flatten(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, elem in enumerate(v):
                if isinstance(elem, dict):
                    items.extend(flatten(elem, f"{new_key}{sep}{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", str(elem)))
        else:
            items.append((new_key, v))
    return dict(items)
