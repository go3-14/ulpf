from cli.onboarding import build_draft

def test_onboarding_is_deterministic():
    draft = build_draft('{"src":"1.2.3.4"}\n', "demo")
    assert draft["source"] == "demo"
    assert draft["format"] == "json"
