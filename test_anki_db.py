#!/usr/bin/env python3
"""Test script to verify anki_db functions work with new Anki schema."""

import sys
sys.path.insert(0, '.')

from korean_config import logger
import anki_db
import logging

# Enable DEBUG logging to see what's happening
logger.setLevel(logging.DEBUG)
for handler in logger.handlers:
    handler.setLevel(logging.DEBUG)

print("=" * 80)
print("Testing anki_db functions with new Anki schema")
print("=" * 80)

# Test 1: get_db_path
print("\n[1] Testing get_db_path():")
try:
    path = anki_db.get_db_path()
    print(f"  ✓ Database path: {path}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# Test 2: get_all_decks
print("\n[2] Testing get_all_decks():")
try:
    decks = anki_db.get_all_decks()
    print(f"  ✓ Found {len(decks)} decks:")
    for deck in decks:
        print(f"    - {deck['name']} (ID: {deck['id']})")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: get_deck_names
print("\n[3] Testing get_deck_names():")
try:
    names = anki_db.get_deck_names()
    print(f"  ✓ Deck names: {names}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 4: resolve_deck_name
if decks:
    first_deck = decks[0]['name']
    print(f"\n[4] Testing resolve_deck_name() with '{first_deck}':")
    try:
        resolved = anki_db.resolve_deck_name(first_deck)
        print(f"  ✓ Resolved to: {resolved}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test 5: get_words_in_deck
    print(f"\n[5] Testing get_words_in_deck('{first_deck}'):")
    try:
        words = anki_db.get_words_in_deck(first_deck)
        print(f"  ✓ Found {len(words)} words:")
        for word in words[:3]:
            print(f"    - {word['korean']} = {word['english']}")
        if len(words) > 3:
            print(f"    ... and {len(words) - 3} more")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("Test complete!")
print("=" * 80)
