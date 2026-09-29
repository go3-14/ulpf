from fastapi.testclient import TestClient


def test_mutating_api_requires_configured_key(monkeypatch):
    import api.main as main
    import config
    monkeypatch.setattr(config, "ULPF_API_KEY", "secret", raising=False)
    client = TestClient(main.app)
    assert client.post("/ingest", json={"logs": "hello"}).status_code == 401
    assert client.post("/ingest", headers={"X-API-Key": "secret"}, json={"logs": "hello"}).status_code == 200
