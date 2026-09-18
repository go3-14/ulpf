from parsers.leef import parse_leef


def test_leef_10_defaults_to_tab_delimiter():
    parsed = parse_leef("LEEF:1.0|Acme|Edge|1.0|1001|src=192.0.2.30\tspt=51000\tdst=198.51.100.30")
    assert parsed is not None
    assert parsed["src"] == "192.0.2.30"
    assert parsed["spt"] == "51000"


def test_leef_20_custom_literal_and_hex_delimiters():
    literal = parse_leef("LEEF:2.0|Acme|Edge|2.0|1003|^|src=192.0.2.32^dpt=53")
    hexadecimal = parse_leef("LEEF:2.0|Acme|Edge|2.0|1004|x09|src=192.0.2.33\tdpt=443")
    assert literal is not None and literal["dpt"] == "53"
    assert hexadecimal is not None and hexadecimal["dpt"] == "443"


def test_leef_20_missing_delimiter_is_rejected():
    assert parse_leef("LEEF:2.0|Acme|Edge|2.0|1005|src=192.0.2.34") is None
