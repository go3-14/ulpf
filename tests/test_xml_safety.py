from parsers.xml_log import parse_xml

def test_xml_rejects_doctype():
    assert parse_xml("<!DOCTYPE x [<!ENTITY y 'z'>]><x>&y;</x>") is None
