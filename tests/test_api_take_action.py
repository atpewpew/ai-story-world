from fastapi.testclient import TestClient

from ai_story.main import app


def _create_session(client, token: str) -> str:
    payload = {
        "session_name": "api-take-action",
        "seed_text": "The forest is quiet tonight.",
        "settings": {},
    }
    response = client.post("/create_session", json=payload, headers={"X-API-Token": token})
    data = response.json()
    return data["session"]["session_id"]


def test_take_action_fallback(monkeypatch):
    token = "test-token"
    monkeypatch.setenv("API_TOKEN", token)
    monkeypatch.setenv("VECTOR_BACKEND", "memory")

    with TestClient(app) as client:
        session_id = _create_session(client, token)

        response = client.post(
            "/take_action",
            json={"session_id": session_id, "player_action": "Look around"},
            headers={"X-API-Token": token},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "ai_response" in data
    assert isinstance(data.get("options"), list)
    assert data.get("world") is not None