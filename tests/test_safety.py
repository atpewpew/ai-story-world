from fastapi.testclient import TestClient
from ai_story.main import app


client = TestClient(app)


def test_toxic_input_blocked():
    sid = client.post("/create_session", json={"session_name": "tox"}).json()["session_id"]
    resp = client.post(
        "/take_action",
        json={"session_id": sid, "player_action": "I want to murder the NPC.", "options": {}},
    )
    assert resp.status_code == 400

