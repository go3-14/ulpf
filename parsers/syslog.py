import re
from parsers.util import kv_extract, extract_generic_connection

SYSLOG_PATTERN = re.compile(
    r'^(?:<(?P<pri>\d{1,3})>)?'
    r'(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?\s*'
    r'(?P<hostname>[\w.\-]+)?\s*'
    r'(?P<tag>%?[\w.\-]+:?)?\s*'
    r'(?P<message>.*)$'
)

def parse_syslog(raw_log: str) -> dict | None:
    """Parse a Syslog line into a structured dictionary.

    Example input:
        <134>Jan 10 10:00:00 fw01 %ASA-6-302013: Built inbound TCP connection 12345 for outside:192.168.1.50/49152 to inside:10.0.0.5/80

    Example output:
        {
            "pri": 134, "facility": 16, "severity": 6,
            "timestamp": "Jan 10 10:00:00", "hostname": "fw01",
            "tag": "%ASA-6-302013:", "message": "...", "action": "Built",
            "proto": "TCP", "src": "192.168.1.50", "spt": 49152,
            "dst": "10.0.0.5", "dpt": 80, "ifname": "outside"
        }
    """
    s = raw_log.strip()
    if not s:
        return None

    m = SYSLOG_PATTERN.match(s)
    if not m:
        return None

    gd = m.groupdict()
    # A syslog record must carry at least its PRI or timestamp envelope. This
    # prevents arbitrary prose such as a malformed sample line from being
    # misclassified as a generic syslog event.
    if not gd.get("pri") and not gd.get("timestamp"):
        return None
    res = {}

    if gd.get("pri"):
        pri = int(gd["pri"])
        res["pri"] = pri
        res["facility"] = pri // 8
        res["severity"] = pri % 8
    else:
        res["severity"] = 6  # default informational

    if gd.get("timestamp"):
        res["timestamp"] = gd["timestamp"]
    if gd.get("hostname"):
        res["hostname"] = gd["hostname"]
    if gd.get("tag"):
        res["tag"] = gd["tag"].rstrip(":")

    msg = gd.get("message", "")
    res["message"] = msg

    # KV pairs from message
    res.update(kv_extract(msg))
    # Generic network-event envelope; vendor-specific semantics stay in YAML.
    res.update(extract_generic_connection(msg))

    # Action detection heuristic if action not explicitly parsed
    if "action" not in res:
        first_word = msg.split()[0] if msg.split() else ""
        if first_word in ("Built", "Teardown", "Reset", "Deny", "Denied"):
            res["action"] = first_word

    if "proto" not in res:
        for p in ("TCP", "UDP", "ICMP", "IP"):
            if f" {p} " in msg or f" {p.lower()} " in msg:
                res["proto"] = p
                break

    return res
