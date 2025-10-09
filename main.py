# main.py
"""
AI-Driven Interactive Story World — with persistent world state tracking (disk-backed sessions)
"""

import os
import random
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Dict, List
from google import genai
from google.genai import types

# Load env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# Setup client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = genai.Client()

app = FastAPI(title="AI Story World")

# ------------------ Data Models ------------------ #
class Session(BaseModel):
    id: str
    history: List[str]
    world: Dict = {}

class ActionInput(BaseModel):
    session_id: str
    action: str

# In-memory store
SESSIONS: Dict[str, Session] = {}

# Sessions folder (disk persistence)
SESSIONS_DIR = "./sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

# ------------------ Helpers ------------------ #
def init_default_world():
    return {
        "location": "",
        "inventory": [],
        "npcs": {},
        "notes": ""
    }

def session_file_path(session_id: str) -> str:
    # Keep CLI naming style but store in ./sessions/
    return os.path.join(SESSIONS_DIR, f"story_memory_{session_id}.json")

def save_session_to_disk(session: Session) -> None:
    path = session_file_path(session.id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.dict(), f, indent=2, ensure_ascii=False)
    except Exception as e:
        # Log or raise depending on needs; keep it simple here.
        print(f"[WARN] Failed to save session {session.id} to disk: {e}")

def load_session_from_disk(session_id: str) -> Session:
    path = session_file_path(session_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure world exists
        if "world" not in data or not isinstance(data["world"], dict):
            data["world"] = init_default_world()
        session = Session(**data)
        return session
    except Exception as e:
        print(f"[WARN] Failed to load session {session_id} from disk: {e}")
        return None

def ensure_session_loaded(session_id: str) -> Session:
    """
    Returns a Session object. Checks in-memory first, then attempts to load from disk.
    If loaded from disk, also puts it into in-memory store.
    """
    session = SESSIONS.get(session_id)
    if session:
        return session
    session = load_session_from_disk(session_id)
    if session:
        SESSIONS[session_id] = session
    return session

# ------------------ Gemini helpers (same as before) ------------------ #
def extract_text_from_response(response):
    """Safely extract plain text from a google-genai GenerateContentResponse."""
    # Try direct text field first (most reliable)
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    # Try to read parts (if text wasn't populated automatically)
    try:
        candidates = getattr(response, "candidates", [])
        if candidates:
            first = candidates[0]
            if hasattr(first, "content") and getattr(first.content, "parts", None):
                parts = first.content.parts
                texts = []
                for p in parts:
                    # New SDK uses Part(text=...) or Part(function_call=...) etc.
                    if hasattr(p, "text") and isinstance(p.text, str):
                        texts.append(p.text)
                if texts:
                    return "\n".join(texts).strip()
    except Exception:
        pass

    # Fallback: try stringify if nothing else worked
    return f"[Unexpected Gemini response format] {str(response)[:500]}"


def generate_with_gemini(prompt: str, max_output_tokens=250, temperature=0.9) -> str:
    """Generate text using Gemini model."""
    try:
        content = types.Content(parts=[types.Part(text=prompt)])
        response = client.models.generate_content(
            model=MODEL,
            contents=[content],
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            ),
        )
        return extract_text_from_response(response)
    except Exception as e:
        return f"[Gemini error] {e}"

# ------------------ World Update Logic (same approach) ------------------ #
def request_world_update(previous_world: dict, latest_story_segment: str, retry_once=True) -> dict:
    """Ask LLM to provide a compact JSON world-state update."""
    prompt = (
        "You are an assistant that extracts world-state changes from a short story segment.\n\n"
        "Schema (JSON): {\"location\": string, \"inventory\": [strings], \"npcs\": {name: state}, \"notes\": string}\n\n"
        "Rules:\n"
        " - Examine the previous world state and the new story segment.\n"
        " - Produce only a JSON object (no explanation) with keys optionally provided among: "
        "\"location\", \"inventory\", \"npcs\", \"notes\".\n"
        " - If a field did not change, you may omit it. If nothing changed, return {}.\n"
        " - Keep inventory items as short strings (e.g., \"lantern\").\n"
        " - Keep npc states short (e.g., \"friendly\", \"hostile\", \"neutral\").\n\n"
        f"Previous world:\n{json.dumps(previous_world, ensure_ascii=False)}\n\n"
        f"Latest story segment:\n{latest_story_segment}\n\n"
        "Return only valid JSON now."
    )

    try:
        response = generate_with_gemini(prompt, max_output_tokens=200, temperature=0.3)
        parsed = parse_json_from_text(response)
        if parsed is not None:
            return parsed
    except Exception:
        pass

    if retry_once:
        retry_prompt = (
            "You must return ONLY valid JSON (no text). "
            "Follow the same schema strictly. Return {} if nothing changed.\n\n"
            f"Previous world:\n{json.dumps(previous_world, ensure_ascii=False)}\n\n"
            f"Latest story segment:\n{latest_story_segment}\n\n"
            "Return only valid JSON now."
        )
        try:
            response2 = generate_with_gemini(retry_prompt, max_output_tokens=150, temperature=0.2)
            parsed2 = parse_json_from_text(response2)
            if parsed2 is not None:
                return parsed2
        except Exception:
            pass

    return {}

def parse_json_from_text(text: str):
    """Try to extract valid JSON from LLM output."""
    if not text or "{" not in text:
        return None
    try:
        first, last = text.index("{"), text.rindex("}") + 1
        candidate = text[first:last]
        return json.loads(candidate)
    except Exception:
        try:
            return json.loads(text)
        except Exception:
            return None

def merge_world(prev: dict, update: dict) -> dict:
    """Merge update into prev (non-destructive)."""
    merged = dict(prev)

    # location
    loc = update.get("location")
    if isinstance(loc, str) and loc.strip():
        merged["location"] = loc.strip()

    # inventory
    inv_prev = list(merged.get("inventory", []) or [])
    inv_update = update.get("inventory", [])
    if isinstance(inv_update, list):
        for it in inv_update:
            if isinstance(it, str):
                item = it.strip()
                if item and item not in inv_prev:
                    inv_prev.append(item)
    merged["inventory"] = inv_prev

    # npcs
    npcs_prev = dict(merged.get("npcs", {}) or {})
    npcs_update = update.get("npcs", {})
    if isinstance(npcs_update, dict):
        for k, v in npcs_update.items():
            if isinstance(k, str):
                npcs_prev[k.strip()] = v
    merged["npcs"] = npcs_prev

    # notes
    note_prev = (merged.get("notes") or "").strip()
    note_update = (update.get("notes") or "").strip()
    if note_update:
        if note_prev:
            merged["notes"] = note_prev + " " + note_update
        else:
            merged["notes"] = note_update

    return merged

# ------------------ Story Generation ------------------ #
def build_prompt(session: Session, player_action: str) -> str:
    recent = "\n".join(session.history[-6:])
    world_summary = summarize_world(session.world)
    return (
        f"You are an AI storyteller continuing an interactive story.\n"
        f"Current world state:\n{world_summary}\n\n"
        f"Recent story:\n{recent}\n\n"
        f"The player just chose: \"{player_action}\".\n\n"
        "Continue the story in 2-3 paragraphs and offer 2 clear next actions (A/B)."
    )

def summarize_world(world: dict) -> str:
    """Convert world dict into short textual summary for context."""
    try:
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
    except Exception:
        return "(empty)"

def generate_story_segment(session: Session, action: str) -> str:
    prompt = build_prompt(session, action)
    return generate_with_gemini(prompt)

# ------------------ API Routes (disk-backed) ------------------ #
@app.post("/create_session")
def create_session():
    session_id = str(random.randint(10000, 99999))
    seed = (
        "You wake up in a misty forest. The air is heavy with fog. "
        "In the distance, a flickering lantern glows faintly."
    )
    session = Session(id=session_id, history=[seed], world=init_default_world())
    SESSIONS[session_id] = session
    # persist immediately
    save_session_to_disk(session)
    return {"session_id": session_id, "text": seed, "world": session.world}

@app.post("/take_action")
def take_action(input: ActionInput):
    # Ensure session is loaded (in-memory or from disk)
    session = ensure_session_loaded(input.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1) Generate story continuation
    next_text = generate_story_segment(session, input.action)
    session.history.append(next_text)

    # 2) Generate world update
    previous_world = session.world or init_default_world()
    world_update = request_world_update(previous_world, next_text, retry_once=True)
    if world_update:
        merged_world = merge_world(previous_world, world_update)
        session.world = merged_world

    # 3) Save back to memory and disk
    SESSIONS[session.id] = session
    save_session_to_disk(session)

    # 4) Return both story and updated world
    return {
        "session_id": input.session_id,
        "text": next_text,
        "world": session.world,
    }

@app.get("/session/{session_id}")
def get_session(session_id: str):
    session = ensure_session_loaded(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# ------------------ Entry ------------------ #
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)
