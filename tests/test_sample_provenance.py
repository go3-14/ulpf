from pathlib import Path

def test_sample_sources_are_explicitly_labelled():
    assert "synthetic" in Path("samples/SOURCES.md").read_text(encoding="utf-8").lower()
