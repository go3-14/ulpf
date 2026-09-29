from pathlib import Path

def test_ui_has_no_external_resources_or_innerhtml():
    text = Path("ui/index.html").read_text(encoding="utf-8").lower()
    assert "http://" not in text and "https://" not in text and "innerhtml" not in text
