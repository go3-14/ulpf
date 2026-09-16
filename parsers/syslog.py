import re

from parsers.util import kv_extract


SYSLOG_RE = re.compile(
    r"^<(?P<pri>\d{1,3})>(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+(?P<tag>[^:]+):\s*(?P<message>.*)$"
)
ASA_ENDPOINT_RE = re.compile(
    r"\bsrc\s+(?P<src_if>[\w.-]+):(?P<src>[0-9a-fA-F:.]+)/(?P<spt>\d+)\s+"
    r"dst\s+(?P<dst_if>[\w.-]+):(?P<dst>[0-9a-fA-F:.]+)/(?P<dpt>\d+)",
    re.IGNORECASE,
)
ACTION_RE = re.compile(r"^(?P<action>[A-Za-z]+)")
PROTO_RE = re.compile(r"\b(?P<proto>tcp|udp|icmp)\b", re.IGNORECASE)
ASA_TAG_RE = re.compile(r"%ASA-(?P<asa_severity>\d)-(?P<msgid>\d+)")


def parse_syslog(raw_log: str) -> dict | None:
    """Parse RFC3164-style syslog.

    Example:
        <166>Jan 10 10:00:00 asa %ASA-6-302013: Built outbound TCP connection 1 for outside:1.2.3.4/12345 dst inside:5.6.7.8/443
    Expected key fields:
        {"severity": "6", "tag": "%ASA-6-302013", "src": "1.2.3.4", "spt": "12345", "dst": "5.6.7.8", "dpt": "443"}
    """
    match = SYSLOG_RE.match(raw_log.strip())
    if not match:
        return None

    pri = int(match.group("pri"))
    out = match.groupdict()
    out["pri"] = pri
    out["facility"] = pri // 8
    out["severity"] = pri % 8

    tag_match = ASA_TAG_RE.search(out["tag"])
    if tag_match:
        out.update(tag_match.groupdict())
        out["severity"] = tag_match.group("asa_severity")

    message = out["message"]
    out.update(kv_extract(message))

    endpoint_match = ASA_ENDPOINT_RE.search(message)
    if endpoint_match:
        out.update(endpoint_match.groupdict())
        out["ifname"] = endpoint_match.group("src_if")

    action_match = ACTION_RE.search(message)
    if action_match and "action" not in out:
        out["action"] = action_match.group("action")

    proto_match = PROTO_RE.search(message)
    if proto_match:
        out["proto"] = proto_match.group("proto").lower()

    return out
