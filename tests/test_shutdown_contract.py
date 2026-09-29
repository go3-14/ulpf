from pathlib import Path

def test_shutdown_contract_is_documented():
    assert "SIGTERM" in Path("Dockerfile").read_text(encoding="utf-8")
