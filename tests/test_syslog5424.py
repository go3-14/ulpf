from parsers.syslog5424 import parse_syslog5424

def test_rfc5424_header():
    event = parse_syslog5424("<34>1 2003-10-11T22:14:15.003Z host app - ID47 - hello")
    assert event["version"] == "1"
    assert event["message"] == "hello"
