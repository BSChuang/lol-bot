"""Anki SQLite database reader for Korean bot."""

import sqlite3
import json
from pathlib import Path
from typing import Optional

from korean_config import logger, ANKI_PROFILE, ANKI_DB_PATH


def _connect() -> sqlite3.Connection:
    """
    Open a new SQLite connection to Anki database.

    Returns:
        sqlite3 database connection

    Raises:
        RuntimeError: If database is locked or not found
    """
    try:
        conn = sqlite3.connect(get_db_path(), check_same_thread=False)
        return conn
    except sqlite3.OperationalError as e:
        if 'locked' in str(e).lower():
            raise RuntimeError('Anki appears to be open. Please close Anki and try again.')
        raise RuntimeError(f'Failed to open Anki database: {e}')


def get_db_path() -> str:
    """
    Get the path to the Anki collection database.

    If ANKI_DB_PATH is set, use it. Otherwise, construct the default path
    from ANKI_PROFILE.

    Returns:
        Path to collection.anki2 file

    Raises:
        RuntimeError: If database file not found
    """
    if ANKI_DB_PATH:
        path = Path(ANKI_DB_PATH)
    else:
        # Default Anki database location
        home = Path.home()
        path = home / '.local' / 'share' / 'Anki2' / ANKI_PROFILE / 'collection.anki2'

    if not path.exists():
        raise RuntimeError(
            f'Anki database not found at {path}. Check ANKI_PROFILE in .env.'
        )

    return str(path)


def get_all_decks() -> list[dict]:
    """
    Get all deck names and IDs from the collection.

    Supports both old (JSON column) and new (decks table) Anki schema.
    Excludes the default deck (id "1").

    Returns:
        List of dicts with 'id' and 'name' keys, sorted by name
    """
    try:
        conn = _connect()
        cursor = conn.cursor()

        # Try new schema first (Anki 2.1.45+)
        try:
            # Don't use ORDER BY name due to unicase collation issues
            cursor.execute('SELECT id, name FROM decks WHERE id != 1')
            rows = cursor.fetchall()
            logger.debug(f'Query returned {len(rows)} rows from decks table')

            if rows:
                decks = [
                    {'id': str(row[0]), 'name': row[1]}
                    for row in rows
                ]
                # Sort in Python instead of SQL to avoid collation issues
                decks.sort(key=lambda x: x['name'].lower())
                logger.info(f'Loaded {len(decks)} decks from decks table')
                conn.close()
                return decks
            else:
                logger.warning('decks table exists but no rows match WHERE id != 1')
        except sqlite3.OperationalError as e:
            # decks table doesn't exist or query failed, try old schema
            logger.debug(f'decks table query failed ({e}), trying old JSON schema')

        # Fall back to old schema (JSON column in col table)
        cursor.execute('SELECT decks FROM col LIMIT 1')
        result = cursor.fetchone()

        if not result:
            conn.close()
            return []

        decks_json = result[0]

        # Check if decks_json is empty or None
        if not decks_json:
            logger.debug('No decks found in col.decks column')
            conn.close()
            return []

        logger.debug(f'Decks JSON (first 200 chars): {decks_json[:200]}')
        decks_dict = json.loads(decks_json)

        # Convert to list, exclude default deck (id "1")
        decks = []
        for deck_id, deck_obj in decks_dict.items():
            if deck_id != '1':  # Skip default deck
                decks.append({
                    'id': deck_id,
                    'name': deck_obj.get('name', '')
                })

        # Sort by name
        decks.sort(key=lambda x: x['name'].lower())
        conn.close()
        return decks

    except RuntimeError:
        raise
    except Exception as e:
        logger.exception(f'Error reading decks: {e}')
        raise RuntimeError(f'Failed to read decks: {e}')


def get_deck_names() -> list[str]:
    """
    Get sorted list of all deck names.

    Returns:
        List of deck names
    """
    decks = get_all_decks()
    return [d['name'] for d in decks]


def get_words_in_deck(deck_name: str) -> list[dict]:
    """
    Get all words in a specific deck.

    Joins cards and notes tables, splits fields on \x1f separator.
    Field order: 0=Korean, 1=English

    Args:
        deck_name: Exact deck name (case-sensitive)

    Returns:
        List of dicts with 'korean', 'english', 'tags' keys
    """
    try:
        conn = _connect()
        cursor = conn.cursor()

        # Find deck ID by name - try new schema first
        deck_id = None

        try:
            # Get all decks and search in Python to avoid collation issues
            cursor.execute('SELECT id, name FROM decks')
            all_decks = cursor.fetchall()

            for deck_row in all_decks:
                if deck_row[1] == deck_name:
                    deck_id = deck_row[0]
                    logger.debug(f'Found deck {deck_name} with ID {deck_id} in decks table')
                    break
        except sqlite3.OperationalError:
            # decks table doesn't exist, try old schema
            logger.debug('decks table not found, trying old JSON schema')

        # Fall back to old schema if not found
        if deck_id is None:
            try:
                cursor.execute('SELECT decks FROM col LIMIT 1')
                result = cursor.fetchone()
                if result and result[0]:
                    decks_json = json.loads(result[0])
                    for did, dobj in decks_json.items():
                        if dobj.get('name') == deck_name:
                            deck_id = int(did)
                            logger.debug(f'Found deck {deck_name} with ID {deck_id} in col.decks JSON')
                            break
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        if deck_id is None:
            conn.close()
            return []

        # Get words for this deck
        cursor.execute('''
            SELECT n.id, n.flds, n.tags
            FROM cards c
            JOIN notes n ON c.nid = n.id
            WHERE c.did = ?
        ''', (deck_id,))

        words = []
        for nid, flds, tags in cursor.fetchall():
            # Split fields on unit separator (0x1f)
            fields = flds.split('\x1f')

            if len(fields) >= 2:
                korean = fields[0].strip()
                english = fields[1].strip()

                # Parse tags
                tag_list = tags.split() if tags.strip() else []

                words.append({
                    'korean': korean,
                    'english': english,
                    'tags': tag_list
                })

        conn.close()
        return words

    except RuntimeError:
        raise
    except Exception as e:
        logger.exception(f'Error reading words from deck {deck_name}: {e}')
        raise RuntimeError(f'Failed to read deck: {e}')


def get_all_words() -> list[dict]:
    """
    Get all words from all decks, deduplicated by Korean field.

    Returns:
        List of word dicts
    """
    try:
        all_decks = get_all_decks()
        all_words = []
        seen_korean = set()

        for deck in all_decks:
            deck_words = get_words_in_deck(deck['name'])
            for word in deck_words:
                korean = word['korean']
                if korean not in seen_korean:
                    all_words.append(word)
                    seen_korean.add(korean)

        return all_words

    except Exception as e:
        logger.exception(f'Error getting all words: {e}')
        raise RuntimeError(f'Failed to get all words: {e}')


def deck_exists(deck_name: str) -> bool:
    """
    Check if a deck exists (case-insensitive).

    Also matches on the final component of hierarchical names.
    e.g., "Week3" matches "Korean::Week3"

    Args:
        deck_name: Deck name to search for

    Returns:
        True if deck exists, False otherwise
    """
    try:
        all_decks = get_all_decks()
        deck_name_lower = deck_name.lower()

        for deck in all_decks:
            full_name = deck['name'].lower()

            # Check full match
            if full_name == deck_name_lower:
                return True

            # Check final component match
            final_component = full_name.split('::')[-1]
            if final_component == deck_name_lower:
                return True

        return False

    except Exception as e:
        logger.exception(f'Error checking deck existence: {e}')
        return False


def resolve_deck_name(input_text: str) -> str | None:
    """
    Resolve user input to canonical full deck name.

    Case-insensitive. Matches on full name or final component.

    Args:
        input_text: User input string

    Returns:
        Canonical deck name or None if not found
    """
    try:
        all_decks = get_all_decks()
        input_lower = input_text.lower().strip()

        if not input_lower:
            return None

        for deck in all_decks:
            full_name = deck['name']
            full_name_lower = full_name.lower()

            # Check full match
            if full_name_lower == input_lower:
                return full_name

            # Check final component match
            final_component = full_name_lower.split('::')[-1]
            if final_component == input_lower:
                return full_name

        return None

    except Exception as e:
        logger.exception(f'Error resolving deck name: {e}')
        return None
