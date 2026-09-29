from pathlib import Path


def test_detection_has_no_vendor_strings_or_checks():
    for path in (Path("parsers/detect.py"), Path("parsers/syslog.py")):
        text = path.read_text(encoding="utf-8").lower()
        for name in ("cisco", "asa", "fortigate", "paloalto", "sshd", "nginx"):
            assert name not in text
