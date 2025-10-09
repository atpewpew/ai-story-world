import os
import json
import random
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------- Config ----------------- #
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(MODEL)

MEMORY_DIR = "./story_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

# Set to True for verbose world-state debugging in CLI (prints updated world each turn)
DEBUG_MODE = False

# ------------------ Session Handling ------------------ #
def load_session(session_id):
    path = os.path.join(MEMORY_DIR, f"story_memory_{session_id}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def save_session(session_id, session_data):
    path = os.path.join(MEMORY_DIR, f"story_memory_{session_id}.json")
    with open(path, "w") as f:
        json.dump(session_data, f, indent=2)

def init_default_world():
    return {
        "location": "",
        "inventory": [],
        "npcs": {},
        "notes": ""
    }

# ------------------ Helper: extract text from Gemini response ------------------ #
def extract_text_from_response(response):
    # Try .text first (older/simple responses)
    if hasattr(response, "text") and response.text:
        return response.text.strip()

    # Try candidates -> content.parts
    if hasattr(response, "candidates") and response.candidates:
        try:
            content_parts = response.candidates[0].content.parts
            if content_parts:
                texts = []
                for p in content_parts:
                    if hasattr(p, "text") and p.text:
                        texts.append(p.text)
                if texts:
                    return "\n".join(texts).strip()
        except Exception:
            pass

    # Fallback to string form
    try:
        return str(response)
    except Exception:
        return ""

# ------------------ AI Story Generation ------------------ #
def generate_story_continuation(prompt, user_input):
    full_prompt = (
        f"{prompt}\n\nPlayer action: {user_input}\n\n"
        "Continue the story in 3-5 sentences, descriptive but concise. "
        "Then suggest 2 next possible actions (A/B) clearly."
    )
    try:
        response = model.generate_content(full_prompt)
        text = extract_text_from_response(response)
        return text or "✨ [No story text received, try again.]"
    except Exception as e:
        return f"⚠️ Error generating story: {str(e)}"

# ------------------ AI World Update (JSON-only) ------------------ #
def request_world_update(previous_world, latest_story_segment, retry_once=True):
    """
    Ask the LLM to provide a JSON-only update to the world state.
    Returns a dict (the update). On failure, returns {}.
    """
    # Build a short prompt asking for strict JSON output matching the schema
    prompt = (
        "You are an assistant that extracts world-state changes from a short story segment.\n\n"
        "Schema (JSON): {\"location\": string, \"inventory\": [strings], \"npcs\": {name: state}, \"notes\": string}\n\n"
        "Rules:\n"
        " - Examine the previous world state and the new story segment.\n"
        " - Produce only a JSON object (no explanation) with keys optionally provided among: "
        "\"location\", \"inventory\", \"npcs\", \"notes\".\n"
        " - If a field did not change, you may omit it. If nothing changed, return an empty JSON object {}.\n"
        " - Keep inventory items as short strings (e.g., \"lantern\").\n"
        " - Keep npc states short (e.g., \"friendly\", \"hostile\", \"neutral\").\n\n"
        "Previous world (for reference):\n"
        f"{json.dumps(previous_world, ensure_ascii=False)}\n\n"
        "Latest story segment:\n"
        f"{latest_story_segment}\n\n"
        "Return only valid JSON now."
    )

    try:
        response = model.generate_content(prompt)
        text = extract_text_from_response(response)
    except Exception:
        text = ""

    # Try to extract JSON substring between first '{' and last '}' in case LLM added extra text
    def parse_json_from_text(txt):
        if not txt or "{" not in txt:
            return None
        try:
            first = txt.index("{")
            last = txt.rindex("}") + 1
            candidate = txt[first:last]
            return json.loads(candidate)
        except Exception:
            # try direct load in case it's clean
            try:
                return json.loads(txt)
            except Exception:
                return None

    parsed = parse_json_from_text(text)
    if parsed is not None:
        return parsed

    # Retry once if requested
    if retry_once:
        try:
            # Shorter retry prompt: stricter and emphasize only JSON
            retry_prompt = (
                "You must return ONLY valid JSON (no surrounding text). "
                "Follow the exact same schema and rules. Return {} if nothing changed.\n\n"
                "Previous world:\n"
                f"{json.dumps(previous_world, ensure_ascii=False)}\n\n"
                "Latest story segment:\n"
                f"{latest_story_segment}\n\n"
                "Return only valid JSON now."
            )
            response2 = model.generate_content(retry_prompt)
            text2 = extract_text_from_response(response2)
            parsed2 = parse_json_from_text(text2)
            if parsed2 is not None:
                return parsed2
        except Exception:
            pass

    # If parsing fails, return empty dict to indicate no update
    return {}

# ------------------ Merge logic ------------------ #
def merge_world(prev, update):
    """
    Merge update into prev and return a new dict.
    Merge rules:
     - location: replace if update provides a non-empty string
     - inventory: union (unique items)
     - npcs: shallow update/merge (update or add keys)
     - notes: append with a separator if both present and update non-empty
    """
    merged = dict(prev)  # shallow copy

    # Location
    loc = update.get("location")
    if isinstance(loc, str) and loc.strip():
        merged["location"] = loc.strip()

    # Inventory
    inv_prev = list(merged.get("inventory", []) or [])
    inv_update = update.get("inventory", [])
    if isinstance(inv_update, list):
        for it in inv_update:
            if isinstance(it, str):
                item = it.strip()
                if item and item not in inv_prev:
                    inv_prev.append(item)
    merged["inventory"] = inv_prev

    # NPCs
    npcs_prev = dict(merged.get("npcs", {}) or {})
    npcs_update = update.get("npcs", {})
    if isinstance(npcs_update, dict):
        for k, v in npcs_update.items():
            if isinstance(k, str):
                npcs_prev[k.strip()] = v
    merged["npcs"] = npcs_prev

    # Notes
    note_prev = (merged.get("notes") or "").strip()
    note_update = (update.get("notes") or "").strip()
    if note_update:
        if note_prev:
            merged["notes"] = note_prev + " " + note_update
        else:
            merged["notes"] = note_update

    return merged

# ------------------ CLI ------------------ #
def main():
    print("=== 🎮 AI Story CLI with Persistent Memory & World State ===\n")

    resume = input("Do you want to resume a previous session? (y/n): ").strip().lower()
    if resume == "y":
        session_id = input("Enter your session ID: ").strip()
        session_data = load_session(session_id)
        if not session_data:
            print("❌ Session not found. Starting a new session.")
            session_id = str(random.randint(10000, 99999))
            session_data = {
                "id": session_id,
                "history": [
                    "You wake up in a misty forest. The air is heavy with fog. In the distance, a flickering lantern glows faintly."
                ],
                "world": init_default_world()
            }
        else:
            # Ensure world exists
            if "world" not in session_data or not isinstance(session_data["world"], dict):
                session_data["world"] = init_default_world()
    else:
        session_id = str(random.randint(10000, 99999))
        session_data = {
            "id": session_id,
            "history": [
                "You wake up in a misty forest. The air is heavy with fog. In the distance, a flickering lantern glows faintly."
            ],
            "world": init_default_world()
        }

    print(f"\nSession ID: {session_id}\n")
    print(session_data["history"][-1])

    while True:
        last_story = "\n".join(session_data["history"][-6:])
        user_input = input("\n👉 Your action (or type 'exit'):\n> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            save_session(session_id, session_data)
            print("👋 Goodbye, adventurer! Your progress is saved.")
            break

        # 1) Generate story continuation
        story_segment = generate_story_continuation(last_story, user_input)
        print(f"\n✨ {story_segment}\n")

        # 2) Save to history (store as "user_action: story" for traceability)
        session_data["history"].append(f"{user_input}: {story_segment}")

        # 3) Ask LLM for a compact world-state update (JSON-only)
        previous_world = session_data.get("world", init_default_world())
        world_update = request_world_update(previous_world, story_segment, retry_once=True)

        # 4) Merge update into previous world
        if world_update:
            merged = merge_world(previous_world, world_update)
            session_data["world"] = merged
        else:
            # no update (keep previous)
            session_data["world"] = previous_world

        # 5) Persist session to disk
        save_session(session_id, session_data)

        # 6) Optionally show suggested A/B actions parsed from AI story text
        if "A)" in story_segment and "B)" in story_segment:
            print("Suggested next actions (from AI):")
            lines = [line for line in story_segment.splitlines() if line.strip().startswith(("A)", "B)"))]
            for line in lines:
                print(line)

        # 7) Debug output for developers (not required; off by default)
        if DEBUG_MODE:
            print("\n📦 [DEBUG] world state (saved):")
            print(json.dumps(session_data["world"], indent=2, ensure_ascii=False))
            print("")

if __name__ == "__main__":
    main()
