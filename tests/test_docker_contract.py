from pathlib import Path

def test_docker_runtime_contract():
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert "USER ulpf" in text and "STOPSIGNAL SIGTERM" in text
    assert "/data/storage" in text and "5514/tcp" in text
