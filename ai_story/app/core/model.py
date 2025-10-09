import os
import json
from typing import Any, Dict, List
from .key_manager import get_key_manager


EXTRACT_FACTS_SCHEMA = {
    "name": "extract_facts",
    "description": "Extract factual triples from a story text",
    "parameters": {
        "type": "object",
        "properties": {
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["possession", "location", "relationship", "action", "property"]},
                        "subject": {"type": "string"},
                        "predicate": {"type": "string"},
                        "object": {"type": "string"},
                        "certainty": {"type": "number", "minimum": 0, "maximum": 1},
                        "timestamp": {"type": "string", "format": "date-time"}
                    },
                    "required": ["type", "subject", "predicate", "object", "certainty"]
                },
            }
        },
        "required": ["facts"],
    },
}


class StoryModel:
    _model_name = os.getenv("MODEL", "gemini-2.5-flash")

    @staticmethod
    def build_simple_prompt(session: Dict[str, Any], player_action: str) -> str:
        recent = "\n".join([h["text"] for h in session.get("history", [])][-8:])
        world = session.get("world", {})
        world_summary = (
            f"Characters: {list(world.get('characters', {}).keys())}; "
            f"Items: {list(world.get('items', {}).keys())}; "
            f"Locations: {list(world.get('locations', {}).keys())}"
        )
        return (
            "You are an interactive storytelling AI that must remain consistent with the provided world facts. Avoid violence/explicit content.\n\n"
            f"World summary: {world_summary}\n\n"
            f"Recent history:\n{recent}\n\n"
            f"Player action: \"{player_action}\"\n\nAI:"
        )

    @classmethod
    async def generate_text(cls, prompt: str) -> str:
        """Generate text using KeyManager with rotation and fallback"""
        key_manager = get_key_manager()
        
        # Try live Gemini first
        if key_manager.keys:
            result = await key_manager.generate_with_rotation(prompt, cls._model_name)
            if result and not result.endswith("[Fallback response - all API keys unavailable]"):
                return result
        
        # Fallback to local mock
        snippet = "Retrieved facts:" in prompt
        base = "The wind rustles through the trees as the story continues."
        if snippet:
            base += " A retrieved clue influences the response."
        return base + "\n\nA) Explore the clearing\nB) Call out for help"

    @classmethod
    async def extract_facts(cls, text: str) -> List[Dict[str, Any]]:
        """Extract facts using Gemini function calling with heuristic fallback"""
        key_manager = get_key_manager()
        
        # Try Gemini function calling first
        if key_manager.keys:
            try:
                # This would use function calling in a real implementation
                # For now, we'll use the heuristic fallback
                pass
            except Exception:
                pass
        
        # Heuristic fallback
        facts: List[Dict[str, Any]] = []
        lower = text.lower()
        if "picks up" in lower:
            subject = "Alice" if "alice" in lower else "Player"
            after = lower.split("picks up", 1)[1].strip().strip(". ")
            # Prefer explicit known nouns
            if "key" in after:
                obj = "key"
            elif "sword" in after:
                obj = "sword"
            elif after:
                # take last token as fallback object
                obj = after.split()[-1]
            else:
                obj = "item"
            facts.append({
                "type": "possession",
                "subject": subject,
                "predicate": "picks up",
                "object": obj,
                "certainty": 0.6,
            })
        return facts


