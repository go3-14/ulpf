from parsers.detect import detect_format
from parsers.syslog import parse_syslog
from parsers.cef import parse_cef
from parsers.leef import parse_leef
from parsers.json_log import parse_json

def test_detect_format():
    assert detect_format("<134>Jan 10 10:00:00 fw01 %ASA-6-302013: msg") == "syslog"
    assert detect_format("<134>Jan 10 10:00:00 PA CEF:0|Palo Alto|PAN-OS|1.0|1|name|1|") == "cef"
    assert detect_format("LEEF:1.0|Vendor|Product|1.0|100|src=1.1.1.1") == "leef"
    assert detect_format('{"src_ip": "1.1.1.1", "action": "deny"}') == "json"

def test_parse_syslog():
    line = "<134>Jan 10 10:00:00 fw01 %ASA-6-302013: Built inbound TCP connection for outside:192.168.1.50/49152 to inside:10.0.0.5/80"
    parsed = parse_syslog(line)
    assert parsed is not None
    assert parsed["tag"] == "%ASA-6-302013"
    assert parsed["src"] == "192.168.1.50"
    assert parsed["spt"] == 49152
    assert parsed["dst"] == "10.0.0.5"
    assert parsed["dpt"] == 80

def test_parse_cef():
    line = "<134>Jan 10 10:00:00 PA-FW CEF:0|Palo Alto Networks|PAN-OS|10.1.0|TRAFFIC|end|1|rt=Jan 10 2026 10:00:00 src=192.168.1.100 spt=54321 dst=198.51.100.20 dpt=443 proto=tcp action=allow"
    parsed = parse_cef(line)
    assert parsed is not None
    assert parsed["device_vendor"] == "Palo Alto Networks"
    assert parsed["src"] == "192.168.1.100"
    assert parsed["spt"] == "54321"
    assert parsed["action"] == "allow"

def test_parse_leef():
    line = "LEEF:1.0|VendorName|ProductName|1.0|100|devTime=Jan 10 2026 10:00:00 GMT\tsrc=192.168.1.10\tsrcPort=12345\tdst=10.0.0.1\tdstPort=80\tproto=TCP\taction=Built"
    parsed = parse_leef(line)
    assert parsed is not None
    assert parsed["vendor"] == "VendorName"
    assert parsed["src"] == "192.168.1.10"
    assert parsed["srcPort"] == "12345"

def test_parse_json():
    line = '{"timestamp": "2026-01-10T10:00:00Z", "src_ip": "192.168.1.200", "src_port": 60000}'
    parsed = parse_json(line)
    assert parsed is not None
    assert parsed["src_ip"] == "192.168.1.200"
    assert parsed["src_port"] == 60000
