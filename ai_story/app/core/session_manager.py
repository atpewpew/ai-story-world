import os
import json
import time
import threading
import uuid
import shutil
from pathlib import Path
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

    def create_session(
        self,
        session_name: str,
        seed_text: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        seed = seed_text or (
            "You wake up in a misty forest. The air is heavy with fog. In the distance, a flickering lantern glows faintly."
        )
        settings = settings or {}
        session = {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": created_at,
            "settings": settings,
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
        return {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": created_at,
            "settings": settings,
        }

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if session_id in self._cache:
                cached = self._cache[session_id]
                cached.setdefault("history", [])
                cached.setdefault("world", {"characters": {}, "items": {}, "locations": {}})
                return cached
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("history", [])
            data.setdefault("world", {"characters": {}, "items": {}, "locations": {}})
            data.setdefault("branches", {})
            data.setdefault("settings", {})
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

    def list_sessions(self) -> list:
        """List all available sessions with metadata"""
        sessions = []
        try:
            for filename in os.listdir(SESSIONS_DIR):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json extension
                    try:
                        session = self.load_session(session_id)
                        if session:
                            sessions.append({
                                "session_id": session_id,
                                "session_name": session.get("session_name", "Unnamed Session"),
                                "created_at": session.get("created_at", "Unknown"),
                                "history_count": len(session.get("history", [])),
                                "last_modified": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(self._path(session_id))))
                            })
                    except Exception:
                        continue
        except Exception:
            pass
        return sorted(sessions, key=lambda x: x.get("created_at", ""), reverse=True)

    def _atomic_write(self, session_id: str, data: Dict[str, Any]) -> None:
        path = self._path(session_id)
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    def save_session(self, session_id: str, session: Dict[str, Any]) -> None:
        session.setdefault("history", [])
        session.setdefault("world", {"characters": {}, "items": {}, "locations": {}})
        session.setdefault("branches", {})
        session.setdefault("settings", {})
        with self._lock:
            self._cache[session_id] = session
            self._atomic_write(session_id, session)

    @staticmethod
    def cleanup_empty_kg_dirs() -> int:
        """
        Remove empty 'kg' directories from session folders.
        These were created by older code but are no longer needed 
        since KG data is stored centrally in data/kg/.
        
        Returns the number of directories removed.
        """
        removed_count = 0
        base = Path(SESSIONS_DIR)
        if not base.exists():
            return 0
        
        for session_dir in base.iterdir():
            if not session_dir.is_dir():
                continue
            kg_dir = session_dir / "kg"
            if kg_dir.exists() and kg_dir.is_dir():
                # Check if directory is empty
                if not any(kg_dir.iterdir()):
                    try:
                        shutil.rmtree(kg_dir)
                        removed_count += 1
                    except Exception:
                        pass  # Silently skip if we can't remove
        return removed_count

