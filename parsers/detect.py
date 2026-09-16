import re

SYSLOG_HEADER_RE = re.compile(r'^(?:<\d{1,3}>|(?:[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}))')

def detect_format(raw: str) -> str | None:
    s = raw.strip()
    if not s:
        return None
    if s.startswith("{") or s.startswith("["):
        return "json"
    if "CEF:" in s[:200]:
        return "cef"
    if "LEEF:" in s[:200]:
        return "leef"
    if SYSLOG_HEADER_RE.match(s) or "%ASA-" in s:
        return "syslog"
    return None

