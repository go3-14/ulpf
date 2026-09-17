from __future__ import annotations

from parsers.syslog import parse_syslog


def test_cisco_asa_payloads_extract_endpoints_and_pri():
    parsed = parse_syslog(
        '<164>Dec 27 14:58:25 asa-fw %ASA-4-106023: Deny tcp src outside:10.65.63.155/56166 dst inside:10.5.0.30/8000 by access-group "OUT-IN"'
    )
    assert parsed is not None
    assert parsed["facility"] == 20
    assert parsed["severity"] == 4
    assert parsed["msgid"] == "106023"
    assert parsed["action"] == "Deny"
    assert parsed["src"] == "10.65.63.155"
    assert parsed["spt"] == "56166"
    assert parsed["dst"] == "10.5.0.30"
    assert parsed["dpt"] == "8000"


def test_malformed_syslog_returns_none():
    assert parse_syslog("malformed ASA line") is None
