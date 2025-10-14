import asyncio
import logging
import os
import random
from typing import Any, Dict, List

from .key_manager import get_key_manager


STORY_GENERATION_SCHEMA = {
    "name": "generate_story_turn",
    "description": "Generate the next story turn with narrative text, player choices, and extracted world facts",
    "parameters": {
        "type": "object",
        "properties": {
            "ai_text": {
                "type": "string",
                "description": "The narrative continuation for the next story turn (2-4 sentences)"
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 3,
                "description": "2-3 specific action choices the player can take next"
            },
            "extracted_facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["possession", "location", "relationship", "action", "property"],
                            "description": "Type of fact: possession (has/acquires item), location (is at/moves to), relationship (meets/talks to character), action (performs action), property (has characteristic)"
                        },
                        "subject": {
                            "type": "string",
                            "description": "The entity performing or possessing (e.g., 'Player', 'Alice', character name)"
                        },
                        "predicate": {
                            "type": "string",
                            "description": "The relationship or action (e.g., 'acquires', 'is at', 'meets', 'owns')"
                        },
                        "object": {
                            "type": "string",
                            "description": "The target entity (e.g., item name, location name, character name)"
                        },
                        "certainty": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Confidence in this fact (0.0 to 1.0)"
                        }
                    },
                    "required": ["type", "subject", "predicate", "object", "certainty"]
                },
                "description": "Extracted world facts from this story turn that update the knowledge graph"
            }
        },
        "required": ["ai_text", "options", "extracted_facts"]
    }
}

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


logger = logging.getLogger("ai_story.core.model")


def is_system_echo(text: str) -> bool:
    """
    Check if the text contains system prompt or instruction content that should not be shown to users.
    Returns True if the text appears to be a system message rather than story content.
    """
    if not text or not isinstance(text, str):
        return True
    
    text_lower = text.lower().strip()
    
    # Check for obvious system/meta content signals
    bad_signals = [
        "you are an interactive storytelling ai",
        "remain consistent with",
        "avoid violence",
        "avoid explicit",
        "system:",
        "instruction:",
        "(local)",
        "(system)",
        "must remain consistent",
        "provided world facts",
        "you are a storytelling",
        "you must",
    ]
    
    return any(signal in text_lower for signal in bad_signals)


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
            f"Player action: \"{player_action}\"\n\n"
            "Respond with a narrative continuation of the story, then provide 2-3 action choices for the player.\n"
            "Format your response as:\n"
            "[Your narrative response]\n\n"
            "A) [First action option]\n"
            "B) [Second action option]\n"
            "C) [Third action option]\n\nAI:"
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
        
        # Enhanced heuristic fallback
        facts: List[Dict[str, Any]] = []
        lower = text.lower()
        
        # Possession facts - enhanced patterns
        if ("picks up" in lower or "pick up" in lower or "picks" in lower or "pick it" in lower or "lift" in lower or "lift it" in lower or 
            "retrieve" in lower or "retrieves" in lower or "closing around" in lower or "close around" in lower or
            "grab" in lower or "grabs" in lower or "take" in lower or "takes" in lower or
            "close" in lower or "closes" in lower or "pocket" in lower or "pockets" in lower):
            
            subject = "Alice" if "alice" in lower else "Player"
            
            # Extract object from different patterns
            obj = "item"  # default
            
            # Pattern 1: "picks up X" or "pick up X" or "picks X" or "pick it"
            if "picks up" in lower:
                after = lower.split("picks up", 1)[1].strip().strip(". ")
            elif "pick up" in lower:
                after = lower.split("pick up", 1)[1].strip().strip(". ")
            elif "picks" in lower:
                after = lower.split("picks", 1)[1].strip().strip(". ")
            elif "pick it" in lower:
                after = lower.split("pick it", 1)[1].strip().strip(". ")
            # Pattern 2: "lift it" or "lift X"
            elif "lift it" in lower:
                after = lower.split("lift it", 1)[1].strip().strip(". ")
            elif "lift" in lower:
                after = lower.split("lift", 1)[1].strip().strip(". ")
            # Pattern 3: "retrieve X"
            elif "retrieve" in lower:
                after = lower.split("retrieve", 1)[1].strip().strip(". ")
            # Pattern 4: "closing around X" or "close around X"
            elif "closing around" in lower:
                after = lower.split("closing around", 1)[1].strip().strip(". ")
            elif "close around" in lower:
                after = lower.split("close around", 1)[1].strip().strip(". ")
            # Pattern 5: "grab X" or "take X"
            elif "grab" in lower:
                after = lower.split("grab", 1)[1].strip().strip(". ")
            elif "take" in lower:
                after = lower.split("take", 1)[1].strip().strip(". ")
            # Pattern 6: "pocket X"
            elif "pocket" in lower:
                after = lower.split("pocket", 1)[1].strip().strip(". ")
            else:
                after = ""
            
            # Extract object from context
            if after:
                # Look for specific items in the text
                if "lantern" in lower:
                    obj = "lantern"
                elif "compass" in lower:
                    obj = "compass"
                elif "key" in lower:
                    obj = "key"
                elif "sword" in lower:
                    obj = "sword"
                elif "book" in lower:
                    obj = "book"
                elif "coin" in lower:
                    obj = "coin"
                elif "object" in lower:
                    obj = "object"
                elif "item" in lower:
                    obj = "item"
                else:
                    # Try to extract from the after text
                    words = after.split()
                    if words:
                        obj = words[0]
            
            facts.append({
                "type": "possession",
                "subject": subject,
                "predicate": "acquires",
                "object": obj,
                "certainty": 0.6,
            })
        
        # Item discovery facts (when items are found but not yet acquired)
        # Only trigger if the discovery is about a physical object, not abstract concepts
        if ("reveal " in lower or "reveals " in lower or "find" in lower or "finds" in lower or 
            "discover" in lower or "discovers" in lower or "uncover" in lower or "uncovers" in lower):
            
            subject = "Alice" if "alice" in lower else "Player"
            
            # Extract the discovered item more precisely
            obj = "item"  # default
            
            # Look for discovery patterns
            if "reveal " in lower:  # Add space to avoid partial matches
                after_reveal = lower.split("reveal ", 1)[1].strip().strip(". ")
            elif "reveals " in lower:  # Add space to avoid partial matches
                after_reveal = lower.split("reveals ", 1)[1].strip().strip(". ")
            elif "find" in lower:
                after_reveal = lower.split("find", 1)[1].strip().strip(". ")
            elif "finds" in lower:
                after_reveal = lower.split("finds", 1)[1].strip().strip(". ")
            elif "discover" in lower:
                after_reveal = lower.split("discover", 1)[1].strip().strip(". ")
            elif "discovers" in lower:
                after_reveal = lower.split("discovers", 1)[1].strip().strip(". ")
            else:
                after_reveal = ""
            
            # Skip if the discovery is about environmental elements, not items
            # Only skip if the environmental word is the first word or main object
            if after_reveal:
                first_words = after_reveal.split()[:3]  # Check first 3 words
                if any(env_word in first_words for env_word in ["roots", "ground", "floor", "earth", "path", "way", "direction", "route", "trail"]):
                    after_reveal = ""
            
            # Look for specific items in the discovery context
            if after_reveal:
                if "compass" in after_reveal:
                    obj = "compass"
                elif "lantern" in after_reveal:
                    obj = "lantern"
                elif "key" in after_reveal:
                    obj = "key"
                elif "sword" in after_reveal:
                    obj = "sword"
                elif "book" in after_reveal:
                    obj = "book"
                elif "coin" in after_reveal:
                    obj = "coin"
                else:
                    # Try to extract from the after text, but only if it's a valid item
                    words = after_reveal.split()
                    if words and len(words[0]) > 2:  # Avoid single letters or very short words
                        obj = words[0]
            
            facts.append({
                "type": "possession",
                "subject": subject,
                "predicate": "discovers",
                "object": obj,
                "certainty": 0.5,
            })
        
        # Location facts
        if "goes to" in lower or "enters" in lower or "walks to" in lower:
            subject = "Alice" if "alice" in lower else "Player"
            if "enters" in lower:
                location = lower.split("enters", 1)[1].strip().strip(". ")
            elif "goes to" in lower:
                location = lower.split("goes to", 1)[1].strip().strip(". ")
            elif "walks to" in lower:
                location = lower.split("walks to", 1)[1].strip().strip(". ")
            else:
                location = "somewhere"
            
            facts.append({
                "type": "location",
                "subject": subject,
                "predicate": "is at",
                "object": location,
                "certainty": 0.7,
            })
        
        # Character introduction facts - enhanced patterns
        if ("meets" in lower or "encounters" in lower or "sees" in lower or 
            "it's an" in lower or "it is an" in lower or "they are" in lower or
            "standing" in lower and ("figure" in lower or "person" in lower)):
            
            subject = "Alice" if "alice" in lower else "Player"
            
            # Direct action patterns
            if "meets" in lower:
                character = lower.split("meets", 1)[1].strip().strip(". ")
            elif "encounters" in lower:
                character = lower.split("encounters", 1)[1].strip().strip(". ")
            elif "sees" in lower:
                character = lower.split("sees", 1)[1].strip().strip(". ")
            # Character description patterns
            elif "it's an" in lower:
                character = lower.split("it's an", 1)[1].strip().strip(". ").split(",")[0].strip()
            elif "it is an" in lower:
                character = lower.split("it is an", 1)[1].strip().strip(". ").split(",")[0].strip()
            elif "they are" in lower:
                character = lower.split("they are", 1)[1].strip().strip(". ").split(",")[0].strip()
            # Standing figure patterns
            elif "standing" in lower and ("figure" in lower or "person" in lower):
                if "figure" in lower:
                    character = "mysterious figure"
                else:
                    character = "person"
            else:
                character = "someone"
            
            facts.append({
                "type": "relationship",
                "subject": subject,
                "predicate": "meets",
                "object": character,
                "certainty": 0.8,
            })
        
        # Character speaking facts
        if ("speaks" in lower or "speak" in lower or "says" in lower or "say" in lower or 
            "tells" in lower or "tell" in lower or "talks" in lower or "talk" in lower or
            "words" in lower or "voice" in lower or "speech" in lower):
            subject = "Alice" if "alice" in lower else "Player"
            speaker = "someone"
            
            facts.append({
                "type": "relationship",
                "subject": subject,
                "predicate": "talks to",
                "object": speaker,
                "certainty": 0.7,
            })
        
        # Character presence facts (when characters are mentioned in context)
        # Only trigger if there's a clear interaction pattern
        if (("elf" in lower or "wizard" in lower or "person" in lower or "figure" in lower) and 
            ("you" in lower or "player" in lower) and
            ("see" in lower or "meet" in lower or "encounter" in lower or "approach" in lower or "emerge" in lower)):
            
            subject = "Alice" if "alice" in lower else "Player"
            if "elf" in lower:
                character = "elf"
            elif "wizard" in lower:
                character = "wizard"
            elif "person" in lower:
                character = "person"
            elif "figure" in lower:
                character = "figure"
            else:
                character = "someone"
            
            facts.append({
                "type": "relationship",
                "subject": subject,
                "predicate": "interacts with",
                "object": character,
                "certainty": 0.6,
            })
        
        return facts

    @staticmethod
    async def _local_fallback(prompt_or_payload: Any) -> Dict[str, Any]:
        """Local deterministic fallback used when remote generation is unavailable."""
        # Generate a generic but appropriate story continuation
        fallback_stories = [
            "The scene shifts around you, and time seems to pause for a moment. As clarity returns, you find yourself considering your next move.",
            "A gentle breeze carries whispers of possibility. The path ahead remains yours to choose.",
            "The world around you settles into a moment of quiet anticipation, waiting for your decision.",
            "Time flows like water, and you find yourself at a crossroads, each path offering its own mysteries.",
        ]
        
        base_options = [
            "Investigate the area",
            "Move forward cautiously",
            "Consider your options",
        ]
        
        try:
            import random
            ai_text = random.choice(fallback_stories)
            options = random.sample(base_options, k=min(len(base_options), 3))
        except Exception:
            ai_text = fallback_stories[0]
            options = base_options

        await asyncio.sleep(0.05)
        return {"ai_text": ai_text, "options": options, "extracted_facts": []}

    @classmethod
    async def generate_story_with_options(cls, prompt_or_payload: Any, retry_count: int = 0) -> Dict[str, Any]:
        """Generate story text with options using Gemini structured output, with minimal fallbacks."""
        force_local = isinstance(prompt_or_payload, dict) and prompt_or_payload.get("__force_local")

        if isinstance(prompt_or_payload, str):
            prompt = prompt_or_payload
        elif isinstance(prompt_or_payload, dict):
            prompt = str(prompt_or_payload.get("prompt") or prompt_or_payload.get("player_action") or "")
        else:
            prompt = str(prompt_or_payload)

        # Skip straight to local fallback if forced
        if force_local:
            return await cls._local_fallback({"prompt": prompt})

        # Try custom LLM integration first (if available)
        try:
            from ai_story.app.core import llm_integration  # type: ignore
        except Exception:
            llm_integration = None  # type: ignore

        if llm_integration and hasattr(llm_integration, "generate_from_llm"):
            try:
                maybe_result = llm_integration.generate_from_llm(prompt_or_payload)
                if asyncio.iscoroutine(maybe_result):
                    maybe_result = await maybe_result
                if maybe_result:
                    # Validate the result before returning
                    ai_text = maybe_result.get("ai_text", "")
                    if not is_system_echo(ai_text):
                        return maybe_result
                    else:
                        logger.warning("LLM integration returned system prompt text, skipping")
            except Exception:
                logger.exception("LLM integration generate_from_llm failed")

        # PRIMARY PATH: Use Gemini function calling for structured output
        key_manager = get_key_manager()
        if key_manager.keys:
            try:
                result = await key_manager.generate_with_function_calling(
                    prompt, cls._model_name, STORY_GENERATION_SCHEMA
                )
                # Validate and return structured result
                if result and isinstance(result, dict):
                    if "ai_text" in result and "options" in result:
                        ai_text = result.get("ai_text", "")
                        
                        # Check if the response contains system prompt text
                        if is_system_echo(ai_text):
                            logger.warning(f"Detected system prompt in Gemini output: {ai_text[:100]}...")
                            
                            # Retry once if this is the first attempt
                            if retry_count < 1:
                                logger.info("Retrying Gemini API call due to invalid output...")
                                await asyncio.sleep(0.5)  # Brief delay before retry
                                return await cls.generate_story_with_options(prompt_or_payload, retry_count + 1)
                            else:
                                logger.warning("Retry also returned invalid output, using fallback")
                                return await cls._local_fallback({"prompt": prompt})
                        
                        logger.info(f"Gemini function calling succeeded: {len(result.get('options', []))} choices, {len(result.get('extracted_facts', []))} facts")
                        return result
                    else:
                        logger.warning(f"Gemini function calling returned incomplete result: {result}")
            except Exception:
                logger.exception("Gemini function calling failed, falling back")

        # FALLBACK: Only if all API keys are unavailable
        logger.warning("All Gemini API attempts failed, using local fallback")
        return await cls._local_fallback({"prompt": prompt})

    @staticmethod
    def _generate_fallback_options(context: str) -> List[str]:
        """Generate heuristic fallback options"""
        return [
            "Explore further",
            "Talk to someone nearby",
            "Examine the surroundings"
        ]


