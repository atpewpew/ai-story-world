import os
import json
import time
import threading
import uuid
from typing import Any, Dict, Optional


SESSIONS_DIR = os.path.join("data", "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


class SessionManager:
    """Manages JSON-backed sessions with simple in-memory cache and atomic writes."""

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _path(self, session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, f"{session_id}.json")

    def create_session(self, session_name: str, seed_text: Optional[str] = None) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        seed = seed_text or (
            "You wake up in a misty forest. The air is heavy with fog. In the distance, a flickering lantern glows faintly."
        )
        session = {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": created_at,
            "history": [
                {"turn_id": 0, "actor": "ai", "text": seed, "timestamp": created_at}
            ],
            "world": {"characters": {}, "items": {}, "locations": {}},
            "branches": {},
            "vector_meta": [],
            "kg_sync_ts": created_at,
        }
        with self._lock:
            self._cache[session_id] = session
            self._atomic_write(session_id, session)
        return {"session_id": session_id, "created_at": created_at}

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if session_id in self._cache:
                return self._cache[session_id]
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with self._lock:
                self._cache[session_id] = data
            return data
        except Exception:
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.load_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        path = self._path(session_id)
        with self._lock:
            self._cache.pop(session_id, None)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception:
                return False
        return False

    def append_turn(self, session_id: str, actor: str, text: str) -> int:
        session = self.load_session(session_id)
        if not session:
            raise ValueError("Session not found")
        turn_id = (session["history"][-1]["turn_id"] + 1) if session["history"] else 1
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        session["history"].append({"turn_id": turn_id, "actor": actor, "text": text, "timestamp": ts})
        with self._lock:
            self._cache[session_id] = session
            self._atomic_write(session_id, session)
        return turn_id

    def update_world(self, session_id: str, world_update: Dict[str, Any]) -> None:
        session = self.load_session(session_id)
        if not session:
            raise ValueError("Session not found")
        world = session.get("world", {"characters": {}, "items": {}, "locations": {}})
        # Shallow merge for top-level keys
        for k, v in world_update.items():
            world[k] = v
        session["world"] = world
        with self._lock:
            self._cache[session_id] = session
            self._atomic_write(session_id, session)

    def add_vector_meta(self, session_id: str, meta: Dict[str, Any]) -> None:
        session = self.load_session(session_id)
        if not session:
            raise ValueError("Session not found")
        session.setdefault("vector_meta", []).append(meta)
        with self._lock:
            self._cache[session_id] = session
            self._atomic_write(session_id, session)

    def _atomic_write(self, session_id: str, data: Dict[str, Any]) -> None:
        path = self._path(session_id)
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


