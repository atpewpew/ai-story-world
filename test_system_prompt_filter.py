#!/usr/bin/env python3
"""
Test script to verify system prompt filtering works correctly.
Ensures that system/instruction text never leaks to the user.
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_story.app.core.model import is_system_echo


def test_system_echo_detection():
    """Test that is_system_echo correctly identifies system prompts"""
    print("Testing system prompt detection...\n")
    
    # Test cases that SHOULD be detected (return True)
    bad_texts = [
        "(Local) The story continues: You are an interactive storytelling AI",
        "You are an interactive storytelling AI that must remain consistent with the provided world facts.",
        "System: Generate a story continuation",
        "Instruction: Avoid violence/explicit content",
        "Remain consistent with world facts and avoid...",
        "(System) Processing request...",
        "You must remain consistent with the provided world facts",
        "",  # Empty text
        None,  # None value
    ]
    
    print("✓ Testing BAD texts (should be filtered):")
    for text in bad_texts:
        result = is_system_echo(text)
        status = "✓ PASS" if result else "✗ FAIL"
        display_text = repr(text)[:60] if text else repr(text)
        print(f"  {status}: {display_text} -> {result}")
        if not result:
            print(f"    ERROR: Should have been detected as system text!")
    
    # Test cases that SHOULD NOT be detected (return False)
    good_texts = [
        "The crystal glows softly in your hand as you examine it closely.",
        "Alice picks up the ancient tome and opens it carefully. The pages are filled with strange symbols.",
        "You find yourself standing at a crossroads. Three paths stretch out before you.",
        "The elf nods knowingly and gestures toward the forest entrance.",
        "A gentle breeze rustles through the trees as you contemplate your next move.",
        "The tavern is warm and inviting, filled with the sounds of laughter and clinking glasses.",
    ]
    
    print("\n✓ Testing GOOD texts (should NOT be filtered):")
    for text in good_texts:
        result = is_system_echo(text)
        status = "✓ PASS" if not result else "✗ FAIL"
        display_text = text[:60]
        print(f"  {status}: {display_text}... -> {result}")
        if result:
            print(f"    ERROR: Valid story text was incorrectly flagged!")
    
    print("\n" + "=" * 60)
    print("✅ System prompt filter test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_system_echo_detection()
