from pathlib import Path

def test_runtime_source_has_no_network_client_imports():
    banned = ("requests", "urllib.request", "http.client", "smtplib", "ftplib")
    for path in Path("api").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in banned)
