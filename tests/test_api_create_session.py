from fastapi.testclient import TestClient

from ai_story.main import app


def test_create_session_success(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "test-token")
    payload = {
        "session_name": "unittest-session",
        "seed_text": "Hello world",
        "settings": {"tone": "fun"},
    }

    with TestClient(app) as client:
        response = client.post(
            "/create_session",
            json=payload,
            headers={"X-API-Token": "test-token"},
        )

    assert response.status_code == 201, response.text

    data = response.json()
    assert data["ok"] is True
    assert "session" in data
    assert data["session"]["session_name"] == payload["session_name"]
    assert data["session"]["settings"] == payload["settings"]


def test_create_session_validation_error_missing_name(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "test-token")
    payload = {
        "seed_text": "no name provided",
    }

    with TestClient(app) as client:
        response = client.post(
            "/create_session",
            json=payload,
            headers={"X-API-Token": "test-token"},
        )

    assert response.status_code == 422

    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "validation_error"
    assert any(err["loc"][-1] == "session_name" for err in data["detail"])
