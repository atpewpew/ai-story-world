# Gemini Structured Output Implementation

## Summary
Replaced heuristic/regex-based fact extraction and static story choices with **Gemini function calling** for structured output. The AI now dynamically generates story choices and accurately extracts world facts using the model's structured generation capabilities.

## Changes Made

### 1. Fixed `key_manager.py` - Function Calling Implementation
**File:** `ai_story/app/core/key_manager.py`

**Problem:** 
- `generate_with_function_calling()` was calling non-existent `_select_best_key()` method
- Would crash when attempting structured output

**Solution:**
- Replaced with proper key rotation pattern (mirroring `generate_with_rotation()`)
- Properly extracts structured response from `response.candidates[0].content.parts[0].function_call.args`
- Includes circuit breaker and error handling
- Uses `types.Tool(function_declarations=[schema])` for Gemini function calling

```python
async def generate_with_function_calling(self, prompt: str, model: str, function_schema: dict) -> dict:
    """Generate with function calling using key rotation"""
    # Loops through available keys
    # Calls genai.Client().models.generate_content() with tools parameter
    # Extracts structured result from function_call.args
    # Returns dict with {ai_text, options, extracted_facts}
```

### 2. Updated `model.py` - Story Generation Schema
**File:** `ai_story/app/core/model.py`

**Changes:**
- Enhanced `STORY_GENERATION_SCHEMA` with detailed descriptions
- Requires `extracted_facts` in response (was optional)
- Added `minItems`/`maxItems` constraints for options (2-3 choices)
- Schema now enforces fact structure: `{type, subject, predicate, object, certainty}`

**Updated `generate_story_with_options()`:**
- Removed intermediate heuristic fallbacks
- **Primary path:** Gemini function calling with structured schema
- **Fallback only:** When ALL API keys are unavailable (returns local mock)
- Validates structured response before returning
- Logs success with choice/fact counts for debugging

**Before (Heuristic):**
```python
# Generated static choices
["Explore further", "Talk to someone nearby", "Examine the surroundings"]

# Regex extraction created nonsense
{"type": "possession", "subject": "Player", "object": "ings", ...}  # Bad!
```

**After (Structured):**
```python
# Model-generated dynamic choices
["Ask the elf about the glowing crystal", "Search the ancient ruins", "Follow the mysterious footprints"]

# Model-extracted facts
{"type": "location", "subject": "Alice", "predicate": "is at", "object": "Crystal Cavern", "certainty": 0.9}
```

### 3. API Response Format
**File:** `ai_story/app/api/routes_story.py`

Already properly structured - no changes needed:
```json
{
  "turn_id": 5,
  "ai_response": "Story text from Gemini...",
  "options": ["Choice A", "Choice B", "Choice C"],
  "extracted_facts": [
    {
      "type": "possession",
      "subject": "Alice", 
      "predicate": "acquires",
      "object": "Magic Crystal",
      "certainty": 0.95
    }
  ],
  "world": {...}
}
```

### 4. Frontend Dynamic Rendering
**File:** `web/src/components/StoryView.jsx`

Already properly maps dynamic options - no changes needed:
```jsx
{entry.options && entry.options.length > 0 && (
  <div className="storyview-options">
    {entry.options.map((option, idx) => (
      <button key={idx} onClick={() => handleOptionClick(option)}>
        {option}
      </button>
    ))}
  </div>
)}
```

## How It Works

### Request Flow
1. **Player action** → Frontend sends to `/api/take_action`
2. **Backend** builds prompt with session context + RAG retrieval
3. **Key Manager** calls Gemini with function calling schema
4. **Gemini returns** structured JSON: `{ai_text, options, extracted_facts}`
5. **Backend** applies facts to world state, saves session
6. **Frontend** receives response, renders dynamic option buttons

### Gemini Function Calling
```python
# Schema defines structure
STORY_GENERATION_SCHEMA = {
    "name": "generate_story_turn",
    "parameters": {
        "type": "object",
        "properties": {
            "ai_text": {"type": "string", "description": "Story continuation"},
            "options": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3},
            "extracted_facts": {"type": "array", "items": {...fact schema...}}
        },
        "required": ["ai_text", "options", "extracted_facts"]
    }
}

# Gemini generates structured output matching schema
response = await client.models.generate_content(
    model=model_name,
    contents=prompt,
    config=types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[function_schema])]
    )
)

# Extract structured result
result = response.candidates[0].content.parts[0].function_call.args
# Returns: {"ai_text": "...", "options": [...], "extracted_facts": [...]}
```

## Testing

### Prerequisites
1. Set API key: `export GOOGLE_API_KEY="your-gemini-api-key"`
2. Start backend: `cd ai_story && uvicorn main:app --reload --port 8000`
3. Start frontend: `cd web && npm run dev`

### Test Cases

#### 1. Create Session
- Open http://localhost:5173
- Click "New Session" 
- Enter character name (e.g., "Alice")
- Select genre and tone
- Click "Create Session"
- **Expected:** Session appears in list

#### 2. Start Story with Dynamic Choices
- Click on the session
- See opening story text
- **Verify:** 2-3 action buttons appear (NOT static "Explore further" defaults)
- **Expected choices:** Contextual options like "Ask about the crystal" or "Examine the door"

#### 3. Take Action with Fact Extraction
- Click one of the option buttons (e.g., "Pick up the sword")
- **Verify:** 
  - Story continues logically
  - New 2-3 options appear (different from previous)
  - World State panel updates (Items: Sword, Location: Tavern, etc.)
  - **NOT nonsense:** No "ings" or "elf" appearing as items

#### 4. Check Logs
```bash
# Backend terminal should show:
INFO: Gemini function calling succeeded: 3 choices, 2 facts
DEBUG: Extracted 2 facts for turn
DEBUG: World updated: {'items': {'sword': {...}}, 'locations': {...}}
```

#### 5. Inspect World State
- After 3-4 actions, click "Knowledge Graph" tab
- **Expected:** 
  - Characters: [actual names from story]
  - Items: [actual items player acquired]
  - Locations: [actual places visited]
  - **NOT:** Generic "elf", "ings", "person" entries

### What Success Looks Like

✅ **Dynamic Choices:** Each turn has unique contextual options generated by Gemini  
✅ **Accurate Facts:** World state reflects actual story events (not regex artifacts)  
✅ **No Static Defaults:** Never see ["Explore further", "Talk to someone nearby", "Examine the surroundings"]  
✅ **Consistent State:** Items/characters mentioned in story appear in knowledge graph  

### Debugging

If choices are still static:
1. Check backend logs for "Gemini function calling failed"
2. Verify API key is valid: `echo $GOOGLE_API_KEY`
3. Check key manager status: Should show available keys, not all circuit-broken
4. Look for fallback message: "All Gemini API attempts failed, using local fallback"

If facts are wrong:
1. Check logs: "Extracted X facts for turn" 
2. Inspect `/api/take_action` response JSON (browser DevTools Network tab)
3. Verify `extracted_facts` array has proper structure with type/subject/predicate/object
4. Check World State panel - should match story events

## Rollback (If Needed)

If issues arise, the system gracefully falls back:
- If API keys fail → returns local mock with generic options
- Frontend always works even with fallback data
- No breaking changes to API contract

## Next Steps

1. **Test with real API key** to verify end-to-end
2. **Monitor fact quality** - adjust schema descriptions if extraction is inaccurate
3. **Tune prompts** - add more context about world state if choices lack variety
4. **Add validation** - reject facts with certainty < 0.5 threshold

## Files Modified

- ✏️ `ai_story/app/core/key_manager.py` - Fixed function calling implementation
- ✏️ `ai_story/app/core/model.py` - Updated schema, removed heuristic fallbacks  
- ℹ️ `ai_story/app/api/routes_story.py` - No changes (already correct)
- ℹ️ `web/src/components/StoryView.jsx` - No changes (already handles dynamic options)

## Architecture

```
┌─────────────┐
│  Frontend   │ User clicks "Pick up sword"
└──────┬──────┘
       │ POST /api/take_action
       ▼
┌─────────────────────────────────────────────┐
│  routes_story.py                            │
│  • Build prompt with session context        │
│  • Call StoryModel.generate_story_with_options()
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  model.py                                   │
│  • Call key_manager.generate_with_function_calling()
│  • Pass STORY_GENERATION_SCHEMA             │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  key_manager.py                             │
│  • Rotate through available API keys        │
│  • Call Gemini with function calling schema │
│  • Extract structured response              │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  Gemini API                                 │
│  Returns: {                                 │
│    ai_text: "Alice picks up the sword...",  │
│    options: ["Swing at enemy", "Inspect blade", "Sheathe it"],
│    extracted_facts: [                       │
│      {type:"possession", subject:"Alice",   │
│       predicate:"acquires", object:"sword", │
│       certainty:0.95}                       │
│    ]                                        │
│  }                                          │
└─────────────────────────────────────────────┘
```
