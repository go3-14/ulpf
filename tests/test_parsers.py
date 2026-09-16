from parsers.cef import parse_cef
from parsers.detect import detect_format
from parsers.json_log import parse_json
from parsers.leef import parse_leef
from parsers.syslog import parse_syslog


def test_detect_wrapped_cef_before_syslog():
    raw = "<134>Jan 10 10:00:00 fw CEF:0|Palo Alto Networks|PAN-OS|1|id|name|3|src=1.1.1.1"
    assert detect_format(raw) == "cef"


def test_parse_syslog_asa_endpoint():
    raw = "<166>Jan 10 10:00:00 asa %ASA-6-302013: Built tcp src outside:192.0.2.10/1 dst inside:198.51.100.20/443"
    parsed = parse_syslog(raw)
    assert parsed["src"] == "192.0.2.10"
    assert parsed["dpt"] == "443"
    assert parsed["msgid"] == "302013"


def test_parse_cef_wrapped():
    parsed = parse_cef("<134>Jan 10 10:00:00 fw CEF:0|Palo Alto Networks|PAN-OS|1|id|name|3|src=192.0.2.1 dst=198.51.100.1 dpt=443")
    assert parsed["device_vendor"] == "Palo Alto Networks"
    assert parsed["timestamp"] == "Jan 10 10:00:00"
    assert parsed["dpt"] == "443"


def test_parse_leef_custom_delimiter():
    parsed = parse_leef("LEEF:2.0|Vendor|Product|1|event|^|src=192.0.2.1^dst=198.51.100.1^dstPort=443")
    assert parsed["dstPort"] == "443"


def test_parse_json_flatten():
    parsed = parse_json('{"event":{"code":"x"},"tags":["a","b"]}')
    assert parsed["event.code"] == "x"
    assert parsed["tags"] == "a,b"
