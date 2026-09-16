from mappings.loader import load_mappings
from mappings.matcher import identify_source


def test_identify_cisco_asa():
    registry = load_mappings()
    source = identify_source({"tag": "%ASA-6-302013"}, "syslog", registry)
    assert source == "cisco_asa"
