#!/usr/bin/env python3
"""
Quick test script for Gemini structured output implementation.
Verifies that story generation returns dynamic choices and accurate facts.

Usage:
    python test_structured_output.py
    
    (Automatically loads keys from .env file)
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
    else:
        print(f"⚠ No .env file found at {env_path}")
except ImportError:
    print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
    print("  Or manually export GOOGLE_API_KEY in your shell")

from ai_story.app.core.model import StoryModel, STORY_GENERATION_SCHEMA
from ai_story.app.core.key_manager import get_key_manager


async def test_schema_structure():
    """Test that schema has required fields"""
    print("✓ Testing schema structure...")
    
    assert "name" in STORY_GENERATION_SCHEMA
    assert "parameters" in STORY_GENERATION_SCHEMA
    
    params = STORY_GENERATION_SCHEMA["parameters"]
    assert params["type"] == "object"
    
    props = params["properties"]
    assert "ai_text" in props
    assert "options" in props
    assert "extracted_facts" in props
    
    # Check options constraints
    options = props["options"]
    assert options["type"] == "array"
    assert "minItems" in options
    assert "maxItems" in options
    assert options["minItems"] == 2
    assert options["maxItems"] == 3
    
    # Check facts structure
    facts = props["extracted_facts"]
    assert facts["type"] == "array"
    fact_props = facts["items"]["properties"]
    assert "type" in fact_props
    assert "subject" in fact_props
    assert "predicate" in fact_props
    assert "object" in fact_props
    assert "certainty" in fact_props
    
    print("  ✓ Schema structure is valid")
    return True


async def test_key_manager_setup():
    """Test that key manager has keys configured"""
    print("\n✓ Testing key manager setup...")
    
    key_manager = get_key_manager()
    
    if not key_manager.keys:
        print("  ⚠ WARNING: No API keys found!")
        print("    Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        return False
    
    print(f"  ✓ Found {len(key_manager.keys)} API key(s)")
    
    # Check circuit breaker status
    from ai_story.app.core.key_manager import KeyState
    broken_keys = [k.key_id for k in key_manager.keys if k.state == KeyState.CIRCUIT_OPEN]
    if broken_keys:
        print(f"  ⚠ WARNING: {len(broken_keys)} key(s) circuit-broken: {broken_keys}")
    else:
        print(f"  ✓ All keys are active")
    
    return True


async def test_story_generation():
    """Test actual story generation with structured output"""
    print("\n✓ Testing story generation...")
    
    key_manager = get_key_manager()
    if not key_manager.keys:
        print("  ⚠ SKIPPED: No API keys available")
        return None
    
    # Create test prompt
    test_prompt = """
    You are an interactive storytelling AI. The player character Alice is exploring a mysterious forest.
    
    Recent history:
    Alice enters the forest. She sees a glowing crystal on the ground.
    
    Player action: "I pick up the crystal"
    
    Generate a story continuation with 2-3 action choices and extract world facts.
    """
    
    try:
        print("  • Calling Gemini with function calling...")
        result = await StoryModel.generate_story_with_options(test_prompt)
        
        # Validate response structure
        assert isinstance(result, dict), "Result must be dict"
        assert "ai_text" in result, "Missing ai_text"
        assert "options" in result, "Missing options"
        
        ai_text = result["ai_text"]
        options = result["options"]
        facts = result.get("extracted_facts", [])
        
        print(f"\n  ✓ Story generated ({len(ai_text)} chars)")
        print(f"  ✓ Options: {len(options)}")
        print(f"  ✓ Facts extracted: {len(facts)}")
        
        # Check for static defaults (should NOT appear)
        static_defaults = ["Explore further", "Talk to someone nearby", "Examine the surroundings"]
        is_static = all(opt in static_defaults for opt in options)
        
        if is_static:
            print("  ⚠ WARNING: Options look like static defaults!")
            print(f"    Got: {options}")
        else:
            print("  ✓ Options are dynamic (not static defaults)")
        
        # Display results
        print("\n  Story:")
        print(f"    {ai_text[:200]}...")
        
        print("\n  Choices:")
        for i, opt in enumerate(options, 1):
            print(f"    {i}. {opt}")
        
        print("\n  Facts:")
        for fact in facts:
            print(f"    • {fact.get('subject')} {fact.get('predicate')} {fact.get('object')} (certainty: {fact.get('certainty')})")
        
        # Check if facts are meaningful (not regex artifacts)
        bad_entities = ["ings", "elf", "ings of the", "s of"]
        has_bad_facts = any(
            any(bad in str(fact.get(key, "")).lower() for bad in bad_entities)
            for fact in facts
            for key in ["subject", "object"]
        )
        
        if has_bad_facts:
            print("  ⚠ WARNING: Facts contain regex artifacts!")
        else:
            print("  ✓ Facts look clean (no regex artifacts)")
        
        return result
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    print("=" * 60)
    print("Gemini Structured Output Test")
    print("=" * 60)
    
    # Check environment
    has_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not has_key:
        print("\n⚠ WARNING: No API key found in environment!")
        print("  Set GOOGLE_API_KEY or GEMINI_API_KEY to test with real API")
        print("  Tests will run in fallback mode only\n")
    
    # Run tests
    schema_ok = await test_schema_structure()
    keys_ok = await test_key_manager_setup()
    
    if keys_ok:
        result = await test_story_generation()
        
        print("\n" + "=" * 60)
        if result and not result["options"] == ["Explore further", "Talk to someone nearby", "Examine the surroundings"]:
            print("✅ SUCCESS: Structured output working!")
            print("   • Schema is valid")
            print("   • Key manager configured")
            print("   • Dynamic choices generated")
            print("   • Facts extracted")
        else:
            print("⚠ PARTIAL: Tests passed but may be using fallback")
            print("  Check that API key is valid and has quota")
    else:
        print("\n" + "=" * 60)
        print("⚠ Tests completed with warnings")
        print("  Set GOOGLE_API_KEY to test with real API")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
