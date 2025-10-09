from fastapi.testclient import TestClient
from ai_story.main import app


client = TestClient(app)


def test_rag_changes_output():
    sid = client.post("/create_session", json={"session_name": "rag"}).json()["session_id"]
    # First action seeds a vector entry from AI response
    client.post(
        "/take_action",
        json={"session_id": sid, "player_action": "Observe surroundings", "options": {"use_rag": False}},
    )
    # Now use RAG
    r = client.post(
        "/take_action",
        json={"session_id": sid, "player_action": "Search for clues", "options": {"use_rag": True}},
    )
    assert r.status_code == 200
    text = r.json()["ai_response"]
    assert "retrieved clue" in text.lower()

