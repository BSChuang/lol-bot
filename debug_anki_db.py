#!/usr/bin/env python3
"""Debug script to inspect Anki database contents."""

import sqlite3
import json
import sys
import os
from pathlib import Path

# Cross-platform Anki database path detection
ANKI_PROFILE = os.getenv('ANKI_PROFILE', 'User 1')
ANKI_DB_PATH = os.getenv('ANKI_DB_PATH')

if ANKI_DB_PATH:
    db_path = ANKI_DB_PATH
else:
    home = Path.home()
    if sys.platform == 'win32':
        # Windows: AppData\Roaming\Anki2
        db_path = str(home / 'AppData' / 'Roaming' / 'Anki2' / ANKI_PROFILE / 'collection.anki2')
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Application Support/Anki2
        db_path = str(home / 'Library' / 'Application Support' / 'Anki2' / ANKI_PROFILE / 'collection.anki2')
    else:
        # Linux and other Unix: ~/.local/share/Anki2
        db_path = str(home / '.local' / 'share' / 'Anki2' / ANKI_PROFILE / 'collection.anki2')

print("=" * 80)
print(f"Examining: {db_path}")
print("=" * 80)

try:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # 1. List all tables
    print("\n[1] TABLES IN DATABASE:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        print(f"  - {table}")

    # 2. Get col table schema
    print("\n[2] COL TABLE SCHEMA:")
    cursor.execute("PRAGMA table_info(col);")
    for row in cursor.fetchall():
        print(f"  {row[1]}: {row[2]}")

    # 3. Get col table contents (just the important fields)
    print("\n[3] COL TABLE CONTENTS:")
    cursor.execute("SELECT * FROM col;")
    col_data = cursor.fetchone()

    if col_data:
        cursor.execute("PRAGMA table_info(col);")
        columns = [row[1] for row in cursor.fetchall()]

        for col_name, value in zip(columns, col_data):
            if col_name == 'decks':
                print(f"\n  DECKS FIELD:")
                print(f"    Type: {type(value).__name__}")
                print(f"    Length: {len(value) if value else 0}")
                print(f"    Empty: {not value}")

                if value:
                    print(f"    First 300 chars: {value[:300]}")
                    print(f"\n    Attempting to parse as JSON...")
                    try:
                        decks_dict = json.loads(value)
                        print(f"    ✓ Valid JSON with {len(decks_dict)} entries")
                        print(f"    Keys: {list(decks_dict.keys())}")

                        # Show first 3 decks
                        print(f"\n    First 3 decks:")
                        for deck_id, deck_info in list(decks_dict.items())[:3]:
                            print(f"      ID {deck_id}: {deck_info.get('name', 'N/A')}")
                    except json.JSONDecodeError as e:
                        print(f"    ✗ JSON parse error: {e}")
                else:
                    print(f"    ✗ DECKS IS EMPTY!")
            else:
                val_str = str(value)[:100] if value else "NULL"
                print(f"  {col_name}: {val_str}")
    else:
        print("  ✗ No data in col table!")

    # 4. Count notes and cards
    print("\n[4] DATA COUNTS:")
    cursor.execute("SELECT COUNT(*) FROM notes;")
    note_count = cursor.fetchone()[0]
    print(f"  Notes: {note_count}")

    cursor.execute("SELECT COUNT(*) FROM cards;")
    card_count = cursor.fetchone()[0]
    print(f"  Cards: {card_count}")

    # 5. Sample notes
    if note_count > 0:
        print(f"\n[5] SAMPLE NOTES (first 3):")
        cursor.execute("SELECT id, mid, flds, tags FROM notes LIMIT 3;")
        for row in cursor.fetchall():
            note_id, mid, flds, tags = row
            fields = flds.split('\x1f')
            print(f"\n  Note {note_id}:")
            print(f"    Model ID: {mid}")
            print(f"    Fields: {fields}")
            print(f"    Tags: {tags}")
    else:
        print(f"\n[5] No notes in database!")

    # 6. Sample cards
    if card_count > 0:
        print(f"\n[6] SAMPLE CARDS (first 3):")
        cursor.execute("""
            SELECT c.id, c.nid, c.did, c.type, c.queue
            FROM cards c
            LIMIT 3;
        """)
        for row in cursor.fetchall():
            card_id, nid, did, card_type, queue = row
            print(f"  Card {card_id}: Note {nid}, Deck {did}, Type {card_type}, Queue {queue}")
    else:
        print(f"\n[6] No cards in database!")

    # 7. Check if there's a decks TABLE (newer Anki versions)
    print("\n[7] DECKS TABLE (if exists):")
    try:
        cursor.execute("PRAGMA table_info(decks);")
        decks_table_schema = cursor.fetchall()
        if decks_table_schema:
            print("  Schema:")
            for row in decks_table_schema:
                print(f"    {row[1]}: {row[2]}")

            print("\n  Contents (first 5):")
            cursor.execute("SELECT * FROM decks LIMIT 5;")
            for row in cursor.fetchall():
                print(f"    {row}")
        else:
            print("  No decks table found")
    except Exception as e:
        print(f"  Error querying decks table: {e}")

    conn.close()

    # 8. Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    if note_count == 0:
        print("✗ Database appears to be EMPTY (no notes)")
    elif col_data and not col_data[columns.index('decks')]:
        print("⚠ Database has notes but col.decks JSON column is EMPTY")
        print("  This is a NEWER Anki version that uses a separate 'decks' table")
        print("  The anki_db.py code needs to be updated to read from the decks table!")
    else:
        print(f"✓ Database appears healthy with {note_count} notes and {len(decks_dict) if decks_dict else 0} decks")

except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
