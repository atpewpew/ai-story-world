"""
app/main.py

FastAPI entry for the AI Story World application.

Responsibilities:
- Expose API endpoints for creating sessions, taking actions, and retrieving sessions.
- Orchestrate story generation and world-state updates using app.core.model (Gemini helpers)
  and the SessionManager (app.core.session).
- Provide defensive fallbacks for core utilities so the app remains runnable while we
  incrementally add modules (world.py, story.py).
"""

import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

# App core modules (model and session are expected to exist)
from app.core.model import generate_text, generate_json_update, make_world_update_prompt
from app.core.session import SessionManager, Session  # Session is a Pydantic model in session.py

# Try to import world/story helpers; provide local fallbacks if missing
try:
    from app.core.world import merge_world, init_default_world, summarize_world
except Exception:
    # Fallback implementations (kept consistent with earlier behavior)
    def init_default_world() -> Dict[str, Any]:
        return {"location": "", "inventory": [], "npcs": {}, "notes": ""}

    def merge_world(prev: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(prev)

        # location
        loc = update.get("location")
        if isinstance(loc, str) and loc.strip():
            merged["location"] = loc.strip()

        # inventory (union)
        inv_prev = list(merged.get("inventory", []) or [])
        inv_update = update.get("inventory", [])
        if isinstance(inv_update, list):
            for it in inv_update:
                if isinstance(it, str):
                    item = it.strip()
                    if item and item not in inv_prev:
                        inv_prev.append(item)
        merged["inventory"] = inv_prev

        # npcs (shallow merge)
        npcs_prev = dict(merged.get("npcs", {}) or {})
        npcs_update = update.get("npcs", {})
        if isinstance(npcs_update, dict):
            for k, v in npcs_update.items():
                if isinstance(k, str):
                    npcs_prev[k.strip()] = v
        merged["npcs"] = npcs_prev

        # notes (append)
        note_prev = (merged.get("notes") or "").strip()
        note_update = (update.get("notes") or "").strip()
        if note_update:
            if note_prev:
                merged["notes"] = note_prev + " " + note_update
            else:
                merged["notes"] = note_update

        return merged

    def summarize_world(world: Dict[str, Any]) -> str:
        parts = []
        if world.get("location"):
            parts.append(f"Location: {world['location']}")
        if world.get("inventory"):
            parts.append(f"Inventory: {', '.join(world['inventory'])}")
        if world.get("npcs"):
            npcs_summary = ", ".join(f"{k} ({v})" for k, v in world["npcs"].items())
            parts.append(f"NPCs: {npcs_summary}")
        if world.get("notes"):
            parts.append(f"Notes: {world['notes']}")
        return " | ".join(parts) if parts else "(empty)"

try:
    from app.core.story import build_prompt  # preferred prompt builder
except Exception:
    # fallback prompt builder
    def build_prompt(session: Session, player_action: str) -> str:
        recent = "\n".join(session.history[-6:])
        world_summary = summarize_world(session.world if isinstance(session.world, dict) else {})
        return (
            f"You are an AI storyteller continuing an interactive story.\n"
            f"Current world state:\n{world_summary}\n\n"
            f"Recent story:\n{recent}\n\n"
            f"The player just chose: \"{player_action}\".\n\n"
            "Continue the story in 2-3 paragraphs and offer 2 clear next actions (A/B)."
        )

# ----------------- Logging -----------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("ai_story.app")

# ----------------- FastAPI app -----------------
app = FastAPI(title="AI Story World (modular)")

# Initialize the SessionManager (disk-backed)
session_manager = SessionManager()

# ----------------- Request / Response models -----------------
class ActionInput(BaseModel):
    session_id: str
    action: str


# ----------------- Routes -----------------
@app.post("/create_session")
def create_session():
    """
    Create a new session; persist immediately and return seed text + world.
    """
    session = session_manager.create_session()
    logger.info("Created session %s", session.id)
    return {"session_id": session.id, "text": session.history[0], "world": session.world}


@app.post("/take_action")
def take_action(input: ActionInput):
    """
    Take an action for a given session:
    1) load session on-demand
    2) generate story continuation via LLM
    3) request JSON-only world update via LLM
    4) merge world update and persist session
    """
    # 1) Ensure session loaded (from memory or disk)
    session = session_manager.get_session(input.session_id)
    if session is None:
        logger.warning("Session not found: %s", input.session_id)
        raise HTTPException(status_code=404, detail="Session not found")

    # 2) Build prompt and generate story text
    try:
        prompt = build_prompt(session, input.action)
        story_text = generate_text(prompt)
    except Exception as e:
        logger.exception("Error generating story text")
        raise HTTPException(status_code=500, detail=f"Story generation failed: {e}")

    # Append to history (we keep "user_action: story" for traceability)
    session.history.append(f"{input.action}: {story_text}")

    # 3) Generate compact JSON world update (separate shorter call)
    try:
        world_prompt = make_world_update_prompt(session.world or init_default_world(), story_text)
        parsed_update, raw = generate_json_update(world_prompt, retry_once=True)
    except Exception as e:
        logger.exception("World update generation failed")
        parsed_update = {}
        raw = None

    # 4) Merge update if any and save
    try:
        if parsed_update:
            merged = merge_world(session.world or init_default_world(), parsed_update)
            session.world = merged
            logger.info("Session %s world updated: %s", session.id, parsed_update)
        else:
            # no update – keep as is
            session.world = session.world or init_default_world()
            logger.debug("Session %s world unchanged", session.id)
    except Exception:
        logger.exception("Merging world update failed; keeping previous world state")

    # 5) Save to memory & disk
    try:
        session_manager.update_session(session.id, {"history": session.history, "world": session.world})
        logger.info("Session %s saved (history length=%d)", session.id, len(session.history))
    except Exception:
        logger.exception("Failed to persist session %s", session.id)

    # 6) Return story text and updated world
    return {"session_id": session.id, "text": story_text, "world": session.world}


@app.get("/session/{session_id}")
def get_session(session_id: str):
    """
    Retrieve a session (loads from disk if needed).
    """
    session = session_manager.get_session(session_id)
    if session is None:
        logger.warning("Session not found for GET: %s", session_id)
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ----------------- Health check -----------------
@app.get("/health")
def health():
    return {"status": "ok"}
