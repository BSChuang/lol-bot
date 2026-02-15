"""State management for SpencerBot."""

from typing import Optional, TypedDict
from dataclasses import dataclass, field
from collections import deque

from config import MAX_MESSAGE_HISTORY


class MessageDict(TypedDict):
    """Structured message data for conversation tracking."""
    message_id: int
    channel_id: int
    reference_id: Optional[int]
    name: str
    text: str


@dataclass
class BotState:
    """
    Manages bot state including message history and TTS users.

    Attributes:
        gpt_messages: Conversation history for GPT chat
        all_messages: All messages for summarization/fact-checking
        tts_users: Set of user IDs with TTS enabled
    """
    gpt_messages: list[dict[str, str]] = field(default_factory=list)
    all_messages: deque[MessageDict] = field(
        default_factory=lambda: deque(maxlen=MAX_MESSAGE_HISTORY)
    )
    tts_users: set[int] = field(default_factory=set)

    def toggle_tts(self, user_id: int) -> bool:
        """
        Toggle TTS for a user.

        Args:
            user_id: Discord user ID

        Returns:
            True if TTS was enabled, False if disabled
        """
        if user_id in self.tts_users:
            self.tts_users.remove(user_id)
            return False
        else:
            self.tts_users.add(user_id)
            return True

    def is_tts_enabled(self, user_id: int) -> bool:
        """
        Check if TTS is enabled for a user.

        Args:
            user_id: Discord user ID

        Returns:
            True if TTS is enabled for this user
        """
        return user_id in self.tts_users

    def has_any_tts_users(self) -> bool:
        """
        Check if any users have TTS enabled.

        Returns:
            True if at least one user has TTS enabled
        """
        return len(self.tts_users) > 0
