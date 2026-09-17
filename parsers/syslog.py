from __future__ import annotations

import re

from parsers.util import kv_extract


SYSLOG_RE = re.compile(
    r"^(?:<(?P<pri>\d{1,3})>)?"
    r"(?P<timestamp>[A-Z][a-z]{2}\s{1,2}\d{1,2}\s\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<tag>[^\s:]+):\s*"
    r"(?P<message>.*)$"
)
ASA_TAG_RE = re.compile(r"^%ASA(?:-[\w]+)?-(?P<asa_severity>[0-7])-(?P<msgid>\d{6})$")

DENY_RE = re.compile(
    r"^(?P<action>Deny)\s+(?P<proto>\S+)\s+src\s+"
    r"(?P<ifname>[^:]+):(?P<src>[^/\s]+)/(?P<spt>\d+)\s+dst\s+"
    r"(?P<dst_ifname>[^:]+):(?P<dst>[^/\s]+)/(?P<dpt>\d+)\b",
    re.IGNORECASE,
)
CONNECTION_RE = re.compile(
    r"^(?P<action>Built|Teardown)\s+"
    r"(?:(?:inbound|outbound)(?:Probe)?\s+|(?:Probe)?\s*)"
    r"(?P<proto>TCP|UDP)\s+connection\s+\d+\s+for\s+"
    r"(?P<ifname>[^:]+):(?P<src>[^/\s]+)/(?P<spt>\d+)"
    r"(?:\s+\([^)]*\))?\s+to\s+"
    r"(?P<dst_ifname>[^:]+):(?P<dst>[^/\s]+)/(?P<dpt>\d+)\b",
    re.IGNORECASE,
)


def parse_syslog(raw_log: str) -> dict | None:
    """Parse ASA syslog, e.g. ``<166>Apr 27 11:31:23 asa-fw %ASA-6-302013: Built outbound TCP ...``."""
    match = SYSLOG_RE.match(raw_log.strip())
    if not match:
        return None
    parsed = match.groupdict()
    asa_tag = ASA_TAG_RE.match(parsed["tag"])
    if asa_tag:
        parsed.update(asa_tag.groupdict())
    pri = int(parsed["pri"]) if parsed.get("pri") else None
    if pri is not None:
        parsed["facility"], parsed["severity"] = pri // 8, pri % 8
    elif parsed.get("asa_severity"):
        parsed["severity"] = int(parsed["asa_severity"])
    message = parsed.get("message", "")
    parsed.update(kv_extract(message))
    detail = DENY_RE.search(message) or CONNECTION_RE.search(message)
    if detail:
        parsed.update({key: value for key, value in detail.groupdict().items() if value is not None})
    return parsed
