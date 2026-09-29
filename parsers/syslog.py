import re
from parsers.util import kv_extract, extract_generic_connection

PRI_PATTERN = re.compile(r"^<(?P<pri>\d{1,3})>")
TIMESTAMP_PATTERN = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|"
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:\d{2})?)\s+"
)
TAG_PATTERN = re.compile(r"^(?P<tag>%?[\w.\-]+)(?:\[(?P<pid>\d+)\])?:\s*")
KEY_VALUE_TOKEN = re.compile(r"^[A-Za-z0-9_.\-]+=")

def parse_syslog(raw_log: str) -> dict | None:
    """Parse a Syslog line into a structured dictionary.

    Parse only the syslog envelope and generic key/value fields.
    """
    s = raw_log.strip()
    if not s:
        return None

    res = {}

    pri_match = PRI_PATTERN.match(s)
    rest = s[pri_match.end():].lstrip() if pri_match else s
    if pri_match:
        pri = int(pri_match.group("pri"))
        res["pri"] = pri
        res["facility"] = pri // 8
        res["severity"] = pri % 8
    else:
        res["severity"] = 6  # default informational

    timestamp_match = TIMESTAMP_PATTERN.match(rest)
    if timestamp_match:
        res["timestamp"] = timestamp_match.group("timestamp")
        rest = rest[timestamp_match.end():]
        token_match = re.match(r"^(\S+)(?:\s+|$)", rest)
        if token_match and not KEY_VALUE_TOKEN.match(token_match.group(1)):
            res["hostname"] = token_match.group(1)
            rest = rest[token_match.end():]
            tag_match = TAG_PATTERN.match(rest)
            if tag_match:
                res["tag"] = tag_match.group("tag")
                if tag_match.group("pid") is not None:
                    res["pid"] = int(tag_match.group("pid"))
                rest = rest[tag_match.end():]
        msg = rest
    elif pri_match:
        # A PRI without a timestamp has no envelope hostname/tag. The entire
        # remaining payload is the message, including a leading key=value.
        msg = rest
    else:
        return None

    res["message"] = msg

    # KV pairs from message
    res.update(kv_extract(msg))
    # Generic network-event envelope; vendor-specific semantics stay in YAML.
    res.update(extract_generic_connection(msg))

    return res
