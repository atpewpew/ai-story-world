from typing import Any, Dict
from .model import StoryModel
from ..memory.vector import get_vector_store


SHORT_TERM_N = 8


def build_prompt_with_rag(manager, session: Dict[str, Any], player_action: str, k: int = 6) -> str:
    recent = "\n".join([h["text"] for h in session.get("history", [])][-SHORT_TERM_N:])
    world = session.get("world", {})
    world_summary = (
        f"Characters: {list(world.get('characters', {}).keys())}; "
        f"Items: {list(world.get('items', {}).keys())}; "
        f"Locations: {list(world.get('locations', {}).keys())}"
    )
    store = get_vector_store()
    retrieved = store.query(session_id=session["session_id"], text=player_action, k=k)
    retrieved_text = "\n".join(f"- {t}" for t in retrieved)
    return (
        "You are an interactive storytelling AI that must remain consistent with the provided world facts. Avoid violence/explicit content.\n\n"
        f"World summary: {world_summary}\n\n"
        f"Retrieved facts:\n{retrieved_text}\n\n"
        f"Recent history:\n{recent}\n\n"
        f"Player action: \"{player_action}\"\n\n"
        "Respond with a narrative continuation of the story, then provide 2-3 action choices for the player.\n"
        "Format your response as:\n"
        "[Your narrative response]\n\n"
        "A) [First action option]\n"
        "B) [Second action option]\n"
        "C) [Third action option]\n\nAI:"
    )


