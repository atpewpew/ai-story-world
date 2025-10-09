# app/core/session.py
import os
import json
import random
from typing import Dict, Optional
from app.core.model import Session

MEMORY_DIR = "./story_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)


class SessionManager:
    """Handles story sessions with both in-memory and disk persistence."""

    def __init__(self):
        self.active_sessions: Dict[str, Session] = {}

    # ---------- Session Lifecycle ---------- #
    def create_session(self) -> Session:
        """Create a new story session with a default seed."""
        session_id = str(random.randint(10000, 99999))
        seed_text = (
            "You wake up in a misty forest. The air is heavy with fog. "
            "In the distance, a flickering lantern glows faintly."
        )
        session = Session(
            id=session_id,
            history=[seed_text],
            world={
                "location": "Misty forest",
                "inventory": ["lantern"],
                "npcs": {},
                "notes": "A faint glow cuts through the mist. You hold a cold lantern."
            },
        )
        self.active_sessions[session_id] = session
        self.save_to_disk(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session from memory or disk."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        path = self._session_path(session_id)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            session = Session(**data)
            self.active_sessions[session_id] = session
            return session
        return None

    def save_to_disk(self, session: Session):
        """Persist session to disk as JSON."""
        path = self._session_path(session.id)
        with open(path, "w") as f:
            json.dump(session.dict(), f, indent=2)

    def update_session(self, session_id: str, new_data: dict):
        """Update session attributes (history/world) and persist."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if "history" in new_data:
            session.history = new_data["history"]
        if "world" in new_data:
            session.world = new_data["world"]

        self.active_sessions[session_id] = session
        self.save_to_disk(session)
        return session

    def delete_session(self, session_id: str):
        """Remove session from memory and disk."""
        self.active_sessions.pop(session_id, None)
        path = self._session_path(session_id)
        if os.path.exists(path):
            os.remove(path)

    # ---------- Utilities ---------- #
    @staticmethod
    def _session_path(session_id: str) -> str:
        return os.path.join(MEMORY_DIR, f"story_memory_{session_id}.json")

