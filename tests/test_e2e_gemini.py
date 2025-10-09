"""E2E tests with real Gemini API key for function calling validation."""

import os
import pytest
from fastapi.testclient import TestClient
from ai_story.main import app


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"),
    reason="No Gemini API key provided"
)
class TestE2EGemini:
    """End-to-end tests using real Gemini API."""
    
    def setup_method(self):
        self.client = TestClient(app)
        self.session_id = None
    
    def test_create_session_e2e(self):
        """Test session creation with real API."""
        response = self.client.post("/create_session", json={"session_name": "e2e_test"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        self.session_id = data["session_id"]
    
    def test_take_action_with_fact_extraction_e2e(self):
        """Test action with real Gemini fact extraction."""
        if not self.session_id:
            self.test_create_session_e2e()
        
        response = self.client.post(
            "/take_action",
            json={
                "session_id": self.session_id,
                "player_action": "Alice picks up a golden key from the ancient chest.",
                "options": {"use_rag": True}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "ai_response" in data
        assert "extracted_facts" in data
        
        # Verify AI response is not fallback
        ai_response = data["ai_response"]
        assert not ai_response.endswith("[Fallback response - all API keys unavailable]")
        assert len(ai_response) > 50  # Should be substantial response
        
        # Verify fact extraction
        facts = data["extracted_facts"]
        assert len(facts) > 0
        
        # Look for possession fact
        possession_facts = [f for f in facts if f.get("type") == "possession"]
        assert len(possession_facts) > 0
        
        key_fact = next((f for f in possession_facts if "key" in f.get("object", "").lower()), None)
        assert key_fact is not None
        assert key_fact["subject"] == "Alice"
        assert "key" in key_fact["object"].lower()
    
    def test_get_session_with_kg_snapshot_e2e(self):
        """Test session retrieval includes KG snapshot."""
        if not self.session_id:
            self.test_take_action_with_fact_extraction_e2e()
        
        response = self.client.get(f"/get_session?session_id={self.session_id}")
        assert response.status_code == 200
        
        session = response.json()
        assert "session_id" in session
        assert "world" in session
        assert "history" in session
        
        # Verify world state was updated
        world = session["world"]
        assert "characters" in world
        assert "items" in world
        assert "locations" in world
        
        # Check that Alice has the key
        characters = world.get("characters", {})
        if "Alice" in characters:
            alice = characters["Alice"]
            assert "items" in alice
            assert "key" in alice["items"] or any("key" in item.lower() for item in alice["items"])
    
    def test_rag_efficacy_e2e(self):
        """Test that RAG actually influences the response."""
        if not self.session_id:
            self.test_take_action_with_fact_extraction_e2e()
        
        # Take another action that should reference the key
        response = self.client.post(
            "/take_action",
            json={
                "session_id": self.session_id,
                "player_action": "I try to use the key on the locked door.",
                "options": {"use_rag": True}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        ai_response = data["ai_response"]
        
        # The response should reference the key or door
        response_lower = ai_response.lower()
        assert any(word in response_lower for word in ["key", "door", "unlock", "open"])
    
    def test_circuit_breaker_e2e(self):
        """Test circuit breaker with multiple rapid requests."""
        if not self.session_id:
            self.test_create_session_e2e()
        
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(5):
            response = self.client.post(
                "/take_action",
                json={
                    "session_id": self.session_id,
                    "player_action": f"Action {i}",
                    "options": {"use_rag": False}
                }
            )
            responses.append(response)
        
        # At least some should succeed
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) > 0
        
        # Check that we're not getting all fallback responses
        non_fallback = [r for r in successful_responses 
                       if not r.json().get("ai_response", "").endswith("[Fallback response - all API keys unavailable]")]
        assert len(non_fallback) > 0
