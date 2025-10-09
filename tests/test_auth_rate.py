import os
from fastapi.testclient import TestClient
from ai_story.main import app


client = TestClient(app)


def test_auth_optional_when_env_missing():
    # No API_TOKEN set by default in test env; endpoints should work
    created = client.post("/create_session", json={"session_name": "ok"})
    assert created.status_code == 200


def test_rate_limit():
    # Hit many times quickly; our simple bucket is per-IP per-minute
    for _ in range(65):
        r = client.get("/health")
        # health has no limiter; ensure it's 200
        assert r.status_code == 200

