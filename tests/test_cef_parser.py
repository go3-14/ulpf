from parsers.cef import parse_cef


def test_wrapped_cef_header_and_space_containing_extension_value():
    parsed = parse_cef(
        r"<134>Jan 10 10:00:00 pa-fw CEF:0|Palo Alto Networks|PAN-OS|10.2|TRAFFIC|allow|3|src=192.0.2.10 spt=51514 dst=198.51.100.20 dpt=443 proto=tcp msg=allowed traffic"
    )
    assert parsed is not None
    assert parsed["hostname"] == "pa-fw"
    assert parsed["facility"] == 16
    assert parsed["severity"] == 6
    assert parsed["msg"] == "allowed traffic"
    assert parsed["vendor_hint"] == "Palo Alto Networks_PAN-OS"


def test_cef_escaped_header_and_extension_delimiters():
    parsed = parse_cef(r"CEF:0|Vendor|Product|1|sig|Name|3|msg=DNS\|allowed reason=policy\=deny")
    assert parsed is not None
    assert parsed["msg"] == "DNS|allowed"
    assert parsed["reason"] == "policy=deny"
