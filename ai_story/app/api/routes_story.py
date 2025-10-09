from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..core.session_manager import SessionManager
from ..core.model import StoryModel
from ..core.rag_pipeline import build_prompt_with_rag
from ..core.state_updater import StateUpdater
from ..memory.vector import get_vector_store
from ..utils.safety import ensure_safe


router = APIRouter(prefix="", tags=["story"])


class TakeActionRequest(BaseModel):
    session_id: str
    player_action: str
    options: Optional[Dict[str, Any]] = None


@router.post("/take_action")
async def take_action(payload: TakeActionRequest):
    manager = SessionManager()
    session = manager.load_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Safety check
    ensure_safe(payload.player_action)

    use_rag = bool((payload.options or {}).get("use_rag", False))

    if use_rag:
        prompt = build_prompt_with_rag(manager, session, payload.player_action)
    else:
        prompt = StoryModel.build_simple_prompt(session, payload.player_action)

    ai_text = await StoryModel.generate_text(prompt)

    # Append to history and persist
    turn_id = manager.append_turn(session["session_id"], actor="ai", text=ai_text)

    # Upsert vector memory
    store = get_vector_store()
    store.upsert({
        "id": f"{session['session_id']}-{turn_id}",
        "text": ai_text,
        "session_id": session["session_id"],
        "turn_id": turn_id,
        "type": "story",
    })

    # Extract facts and update state
    combined_text = f"{payload.player_action} {ai_text}".strip()
    facts = await StoryModel.extract_facts(combined_text)
    updater = StateUpdater(manager)
    updater.apply_facts(session_id=session["session_id"], facts=facts)

    return {
        "session_id": session["session_id"],
        "turn_id": turn_id,
        "ai_response": ai_text,
        "extracted_facts": facts,
    }


