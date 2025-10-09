from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..core.session_manager import SessionManager


router = APIRouter(prefix="", tags=["session"])


class CreateSessionRequest(BaseModel):
    session_name: str
    seed_text: Optional[str] = None


@router.post("/create_session")
def create_session(payload: CreateSessionRequest):
    manager = SessionManager()
    result = manager.create_session(payload.session_name, payload.seed_text)
    return result


@router.get("/get_session")
def get_session(session_id: str = Query(..., description="Session UUID/ID")):
    manager = SessionManager()
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/list_sessions")
def list_sessions():
    manager = SessionManager()
    sessions = manager.list_sessions()
    return {"sessions": sessions}


@router.post("/delete_session")
def delete_session(session_id: str):
    manager = SessionManager()
    ok = manager.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}


