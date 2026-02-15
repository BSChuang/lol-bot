"""Per-user session state management for Korean bot."""

# Module-level state storage
_state: dict[int, dict] = {}
# Key: user_id
# Value: {
#     "active_deck": str | None,
#     "exercise": dict | None,
# }


def get_active_deck(user_id: int) -> str | None:
    """
    Get the active deck for a user.

    Args:
        user_id: Discord user ID

    Returns:
        Active deck name or None if not set
    """
    if user_id not in _state:
        return None
    return _state[user_id].get('active_deck')


def set_active_deck(user_id: int, deck_name: str) -> None:
    """
    Set the active deck for a user.

    Args:
        user_id: Discord user ID
        deck_name: Canonical deck name
    """
    if user_id not in _state:
        _state[user_id] = {'active_deck': None, 'exercise': None}
    _state[user_id]['active_deck'] = deck_name


def get_exercise(user_id: int) -> dict | None:
    """
    Get the pending exercise for a user.

    Args:
        user_id: Discord user ID

    Returns:
        Exercise dict or None if no exercise pending
    """
    if user_id not in _state:
        return None
    return _state[user_id].get('exercise')


def set_exercise(user_id: int, exercise: dict) -> None:
    """
    Set a pending exercise for a user.

    Args:
        user_id: Discord user ID
        exercise: Exercise dict with type, deck, and exercise-specific fields
    """
    if user_id not in _state:
        _state[user_id] = {'active_deck': None, 'exercise': None}
    _state[user_id]['exercise'] = exercise


def clear_exercise(user_id: int) -> None:
    """
    Clear the pending exercise for a user.

    Args:
        user_id: Discord user ID
    """
    if user_id not in _state:
        _state[user_id] = {'active_deck': None, 'exercise': None}
    _state[user_id]['exercise'] = None


def clear_active_deck(user_id: int) -> None:
    """
    Clear the active deck for a user.

    Args:
        user_id: Discord user ID
    """
    if user_id not in _state:
        _state[user_id] = {'active_deck': None, 'exercise': None}
    _state[user_id]['active_deck'] = None
