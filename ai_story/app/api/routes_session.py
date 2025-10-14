import logging

from fastapi import APIRouter, Body, HTTPException, Query, status

from ai_story.app.core.session_manager import SessionManager
from ai_story.app.schemas.session import CreateSessionRequest


router = APIRouter(prefix="", tags=["session"])
logger = logging.getLogger("ai_story.api.sessions")
_CREATE_SESSION_EXAMPLE = getattr(CreateSessionRequest.Config, "schema_extra", {}).get("example", {})


@router.post("/create_session", status_code=status.HTTP_201_CREATED)
def create_session(
    payload: CreateSessionRequest = Body(..., example=_CREATE_SESSION_EXAMPLE),
):
    logger.debug("Received create_session request: %s", payload.json())

    manager = SessionManager()
    try:
        result = manager.create_session(payload.session_name, payload.seed_text, payload.settings)
    except Exception:
        logger.exception("Error creating session")
        raise HTTPException(status_code=500, detail="Internal server error when creating session")

    logger.info("Session created successfully: %s", result)
    return {"ok": True, "session": result}


@router.get("/get_session")
def get_session(session_id: str = Query(..., description="Session UUID/ID")):
    manager = SessionManager()
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.setdefault("history", [])
    session.setdefault("world", {"characters": {}, "items": {}, "locations": {}})
    session.setdefault("settings", {})
    logger.debug("Loaded session %s with %d turns", session_id, len(session["history"]))
    return {"ok": True, "session": session}


@router.get("/list_sessions")
def list_sessions():
    manager = SessionManager()
    sessions = manager.list_sessions()
    return {"sessions": sessions}


@router.delete("/delete_session")
def delete_session(session_id: str = Query(..., description="Session UUID/ID")):
    manager = SessionManager()
    ok = manager.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True, "deleted": True, "session_id": session_id}


