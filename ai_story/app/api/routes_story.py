import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.model import StoryModel, is_system_echo
from ..core.rag_pipeline import build_prompt_with_rag
from ..core.session_manager import SessionManager
from ..core.state_updater import StateUpdater
from ..memory.graph import upsert_fact
from ..memory.vector import get_vector_store
from ..utils.safety import ensure_safe


router = APIRouter(prefix="", tags=["story"])
logger = logging.getLogger("ai_story.routes_story")


class TakeActionRequest(BaseModel):
    session_id: str
    player_action: str
    options: Optional[Dict[str, Any]] = None


@router.post("/take_action")
async def take_action(payload: TakeActionRequest):
    session_id = payload.session_id
    player_action = payload.player_action
    
    manager = SessionManager()
    session = manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.setdefault("history", [])
    session.setdefault("world", {"characters": {}, "items": {}, "locations": {}})
    
    # Safety check
    ensure_safe(player_action)
    
    # Build prompt with RAG
    use_rag = bool((payload.options or {}).get("use_rag", False))
    if use_rag:
        prompt = build_prompt_with_rag(manager, session, player_action)
    else:
        prompt = StoryModel.build_simple_prompt(session, player_action)
    
    # Generate story with options and facts
    try:
        result = await StoryModel.generate_story_with_options(prompt)
    except Exception:
        logger.exception("Story generation failed; using local fallback")
        result = await StoryModel.generate_story_with_options({"prompt": str(prompt), "__force_local": True})
    
    ai_text = result.get("ai_text", "")
    options = result.get("options", [])
    extracted_facts = result.get("extracted_facts", [])
    
    # Final validation: ensure no system prompts leak through
    if is_system_echo(ai_text):
        logger.error(f"System prompt detected in final output, replacing with safe fallback")
        ai_text = "The story pauses briefly as the AI regains context. The world around you awaits your next move."
        if not options:
            options = ["Look around", "Wait and observe", "Continue forward"]
    
    logger.debug("Extracted %d facts for turn", len(extracted_facts))
    
    # Update session history
    turn_id = len(session["history"])
    session["history"].append({
        "turn_id": turn_id,
        "actor": "player",
        "text": player_action,
        "timestamp": datetime.utcnow().isoformat()
    })
    session["history"].append({
        "turn_id": turn_id + 1,
        "actor": "ai",
        "text": ai_text,
        "options": options,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Apply facts to world state
    updater = StateUpdater(manager)
    updater.apply_facts(session_id=session_id, facts=extracted_facts)
    
    # Upsert facts to knowledge graph
    for fact in extracted_facts:
        try:
            upsert_fact(session_id, fact)
        except Exception:
            logger.exception("Failed to upsert fact into knowledge graph")
    
    logger.debug("World updated: %s", session.get("world"))
    
    # Save session
    try:
        manager.save_session(session_id, session)
    except Exception:
        logger.exception("Failed to save session after take_action")
    
    # Ensure KG directory exists
    kg_dir = os.path.join("data", "sessions", session_id, "kg")
    try:
        os.makedirs(kg_dir, exist_ok=True)
    except Exception:
        logger.exception("Failed to ensure knowledge graph directory", extra={"session_id": session_id})
    
    # Upsert vector memory
    try:
        store = get_vector_store()
        store.upsert({
            "id": f"{session_id}-{turn_id + 1}",
            "text": ai_text,
            "session_id": session_id,
            "turn_id": turn_id + 1,
            "type": "story",
        })
    except Exception:
        logger.exception("Failed to upsert vector memory")
    
    # Reload session to get updated world state
    updated_session = manager.load_session(session_id)
    
    return {
        "turn_id": turn_id + 1,
        "ai_response": ai_text,
        "options": options,
        "extracted_facts": extracted_facts,
        "world": updated_session.get("world", {}) if updated_session else {}
    }


class StartStoryRequest(BaseModel):
    session_id: str
    seed_action: Optional[str] = "Start the story"


@router.post("/start_story")
async def start_story(payload: StartStoryRequest):
    request = TakeActionRequest(
        session_id=payload.session_id,
        player_action=payload.seed_action or "Start the story",
    )
    return await take_action(request)


@router.post("/demo_action")
async def demo_action(payload: dict):
    """Single-turn demo without authentication"""
    player_action = payload.get("player_action", "Look around")
    
    demo_prompt = f"""You are a fantasy adventure game master. 
    The player says: "{player_action}"
    
    Generate a short, engaging response (2-3 sentences) and suggest 2-3 next actions."""
    
    result = await StoryModel.generate_story_with_options(demo_prompt)
    
    return {
        "ai_response": result.get("ai_text", ""),
        "options": result.get("options", []),
        "is_demo": True
    }


