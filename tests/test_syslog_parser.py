from parsers.syslog import parse_syslog


def test_cisco_asa_payloads_extract_endpoints_and_pri():
    parsed = parse_syslog(
        '<164>Dec 27 14:58:25 asa-fw %ASA-4-106023: Deny tcp src outside:10.65.63.155/56166 dst inside:10.5.0.30/8000 by access-group "OUT-IN"'
    )
    assert parsed is not None
    assert parsed["facility"] == 20
    assert parsed["severity"] == 4
    assert parsed["action"] == "Deny"
    assert parsed["src"] == "10.65.63.155"
    assert int(parsed["spt"]) == 56166
    assert parsed["dst"] == "10.5.0.30"
    assert int(parsed["dpt"]) == 8000


def test_malformed_syslog_returns_none():
    assert parse_syslog("malformed ASA line") is None


def test_pri_only_key_value_line_has_no_hostname_or_tag():
    parsed = parse_syslog(
        "<189>date=2026-01-10 time=10:00:00 devname=FG100D action=allow"
    )
    assert parsed is not None
    assert parsed.get("hostname") is None
    assert parsed.get("tag") is None
    assert parsed["message"].startswith("date=2026-01-10")


def test_iso_timestamp_envelope_preserves_hostname_and_tag():
    parsed = parse_syslog(
        "<134>2026-01-10T10:00:00Z fw01 app[42]: hello"
    )
    assert parsed["timestamp"] == "2026-01-10T10:00:00Z"
    assert parsed["hostname"] == "fw01"
    assert parsed["tag"] == "app"
    assert parsed["pid"] == 42
    assert parsed["message"] == "hello"
