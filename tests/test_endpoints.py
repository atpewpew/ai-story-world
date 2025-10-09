from fastapi.testclient import TestClient
from ai_story.main import app


client = TestClient(app)


def test_create_and_get_session():
    resp = client.post("/create_session", json={"session_name": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    sid = data["session_id"]

    resp2 = client.get(f"/get_session", params={"session_id": sid})
    assert resp2.status_code == 200
    sess = resp2.json()
    assert sess["session_id"] == sid


def test_take_action_flow():
    created = client.post("/create_session", json={"session_name": "flow"}).json()
    sid = created["session_id"]
    resp = client.post(
        "/take_action",
        json={
            "session_id": sid,
            "player_action": "Alice picks up a small key.",
            "options": {"use_rag": False},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert "ai_response" in data
    facts = data.get("extracted_facts", [])
    assert any("picks up" in f.get("predicate", "") for f in facts)


