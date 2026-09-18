import re
from parsers.util import kv_extract

SYSLOG_PATTERN = re.compile(
    r'^(?:<(?P<pri>\d{1,3})>)?'
    r'(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?\s*'
    r'(?P<hostname>[\w.\-]+)?\s*'
    r'(?P<tag>%?[\w.\-]+:?)?\s*'
    r'(?P<message>.*)$'
)

# ASA idiom patterns e.g. "outside:192.168.1.50/49152" or "from inside:10.0.0.5/80 to outside:192.168.1.50/80"
ASA_CONN_RE = re.compile(
    r'(?:for|from)\s+(?P<src_if>\w+):(?P<src_ip>[\d.]+)/(?P<src_port>\d+)(?:\s*\([\d./]+\))?\s+'
    r'to\s+(?P<dst_if>\w+):(?P<dst_ip>[\d.]+)/(?P<dst_port>\d+)'
)

ASA_DENY_RE = re.compile(
    r'Deny\s+(?P<proto>\w+)\s+src\s+(?P<src_if>\w+):(?P<src_ip>[\d.]+)/(?P<src_port>\d+)\s+'
    r'dst\s+(?P<dst_if>\w+):(?P<dst_ip>[\d.]+)/(?P<dst_port>\d+)'
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

    # ASA message pattern extraction
    conn_m = ASA_CONN_RE.search(msg)
    if conn_m:
        res["src"] = conn_m.group("src_ip")
        res["spt"] = int(conn_m.group("src_port"))
        res["dst"] = conn_m.group("dst_ip")
        res["dpt"] = int(conn_m.group("dst_port"))
        res["ifname"] = conn_m.group("src_if")
    else:
        deny_m = ASA_DENY_RE.search(msg)
        if deny_m:
            res["proto"] = deny_m.group("proto")
            res["src"] = deny_m.group("src_ip")
            res["spt"] = int(deny_m.group("src_port"))
            res["dst"] = deny_m.group("dst_ip")
            res["dpt"] = int(deny_m.group("dst_port"))
            res["ifname"] = deny_m.group("src_if")
            res["action"] = "Deny"

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
