"""
app/core/model.py

Centralized Gemini (google-genai) client and helpers.

Responsibilities:
- Configure and expose a single client instance.
- Provide helper wrappers for text generation and JSON-only generation.
- Provide safe extraction/parsing utilities for model responses, with
  defensive behavior across SDK versions (1.39+).
"""

from typing import Any, Dict, Optional, Tuple
import os
import json
import logging
from dotenv import load_dotenv

# google-genai SDK
from google import genai
from google.genai import types

load_dotenv()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration via environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# Initialize client once
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    # If no key provided, client may still work in some local testing setups
    client = genai.Client()

def _extract_text_from_response(response: Any) -> str:
    """
    Robust extraction of textual content from a google-genai GenerateContentResponse.

    Returns a plain string. If text can't be found, returns a short fallback string
    that includes part of the stringified response (truncated).
    """
    # 1) Try response.text (most SDK versions)
    try:
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
    except Exception:
        pass

    # 2) Try candidates -> content.parts
    try:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            first = candidates[0]
            content = getattr(first, "content", None)
            parts = getattr(content, "parts", None)
            if parts:
                texts = []
                for p in parts:
                    if hasattr(p, "text") and isinstance(p.text, str):
                        texts.append(p.text)
                if texts:
                    return "\n".join(texts).strip()
    except Exception:
        pass

    # 3) Fallback: try to convert to dict if possible (for debugging)
    try:
        as_dict = getattr(response, "to_dict", None)
        if callable(as_dict):
            dump = json.dumps(response.to_dict(), default=str)
            return f"[raw-response-dump]{dump[:1000]}"
    except Exception:
        pass

    # 4) Last resort: str()
    try:
        s = str(response)
        return f"[raw-str]{s[:1000]}"
    except Exception:
        return "[unreadable-response]"

def generate_text(prompt: str, *, model: Optional[str] = None,
                  max_output_tokens: int = 250, temperature: float = 0.7) -> str:
    """
    Generate free-text output from Gemini.

    Returns extracted string (cleaned). Never raises on API response parsing;
    exceptions are caught and returned as error strings.
    """
    _model = model or MODEL
    try:
        # Build content wrapper (types.Content & parts)
        content = types.Content(parts=[types.Part(text=prompt)])
        response = client.models.generate_content(
            model=_model,
            contents=[content],
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )
        return _extract_text_from_response(response)
    except Exception as e:
        LOGGER.exception("Gemini generate_text failed")
        return f"[Gemini error] {e}"

def generate_json_update(prompt: str, *,
                         model: Optional[str] = None,
                         max_output_tokens: int = 200,
                         temperature: float = 0.3,
                         retry_once: bool = True) -> Tuple[Dict, Optional[str]]:
    """
    Ask the model to return a JSON-only response and parse it.

    Returns (parsed_dict, raw_text). If parsing fails, parsed_dict will be {}.
    raw_text is the string returned by the model (for debugging / logging).
    This function will attempt one retry with a stricter prompt if parsing fails.
    """
    _model = model or MODEL

    def _call_and_parse(prompt_text: str) -> Tuple[Dict, Optional[str]]:
        try:
            content = types.Content(parts=[types.Part(text=prompt_text)])
            response = client.models.generate_content(
                model=_model,
                contents=[content],
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            raw = _extract_text_from_response(response)
            # Try to extract JSON substring first
            if raw and "{" in raw:
                try:
                    first = raw.index("{")
                    last = raw.rindex("}") + 1
                    candidate = raw[first:last]
                    parsed = json.loads(candidate)
                    return parsed, raw
                except Exception:
                    pass
            # If raw is strictly JSON
            try:
                parsed = json.loads(raw)
                return parsed, raw
            except Exception:
                return {}, raw
        except Exception as e:
            LOGGER.exception("Gemini generate_json_update call failed")
            return {}, f"[Gemini error] {e}"

    parsed, raw_text = _call_and_parse(prompt)

    if parsed:
        return parsed, raw_text

    if retry_once:
        # Retry with stricter instruction
        retry_prompt = (
            "You must return ONLY valid JSON (no surrounding text). "
            "Follow the requested JSON schema exactly. If nothing changed, return {}.\n\n"
            + prompt
        )
        parsed2, raw2 = _call_and_parse(retry_prompt)
        return (parsed2 or {}, raw2)

    return ({}, raw_text)

# Small helper for building short system prompts for JSON-only world updates
def make_world_update_prompt(previous_world: Dict, latest_story_segment: str) -> str:
    """
    Returns a prompt instructing the model to emit a JSON object matching the world schema.
    This should be passed to generate_json_update.
    """
    return (
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
