import re

HEADER = re.compile(r"^<(?P<pri>\d{1,3})>(?P<version>\d{1,3}) (?P<timestamp>\S+) (?P<hostname>\S+) (?P<tag>\S+) (?P<pid>\S+) (?P<msgid>\S+) (?P<sd>-|(?:\[[^\]]*\])+)(?: (?P<message>.*))?$")

def parse_syslog5424(raw_log: str) -> dict | None:
    match = HEADER.match(raw_log.strip())
    if not match: return None
    result = match.groupdict()
    pri = int(result.pop("pri")); result["pri"] = pri; result["facility"] = pri // 8; result["severity"] = pri % 8
    if result.get("pid") == "-": result.pop("pid")
    if result.get("tag") == "-": result.pop("tag")
    if result.get("sd") == "-": result.pop("sd")
    return {key: value for key, value in result.items() if value is not None}
