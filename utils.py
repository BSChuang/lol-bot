"""Utility functions for SpencerBot."""

from typing import Optional
from datetime import datetime, timedelta
import discord
from discord.ext import commands

from config import (
    logger,
    DOMINOS_TRACKER_FILE,
    SECONDS_PER_YEAR,
    SECONDS_PER_MONTH,
    SECONDS_PER_DAY,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
)
from state import MessageDict


# ============================================================================
# FILE I/O UTILITIES
# ============================================================================


def read_file(filepath: str, encoding: str = 'utf-8') -> str:
    """
    Read text content from a file.

    Args:
        filepath: Path to file to read
        encoding: Text encoding (default: utf-8)

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    try:
        with open(filepath, 'r', encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise


def write_file(filepath: str, text: str, encoding: str = 'utf-8') -> None:
    """
    Write text content to a file.

    Args:
        filepath: Path to file to write
        text: Text content to write
        encoding: Text encoding (default: utf-8)

    Raises:
        IOError: If file cannot be written
    """
    try:
        with open(filepath, 'w', encoding=encoding) as file:
            file.write(text)
    except IOError as e:
        logger.error(f"Error writing file {filepath}: {e}")
        raise


def read_dominos_timestamp() -> float:
    """
    Read the last Dominos timestamp from file.

    Returns:
        Unix timestamp of last Dominos order, or current time if file invalid
    """
    try:
        return float(read_file(DOMINOS_TRACKER_FILE))
    except (ValueError, FileNotFoundError) as e:
        logger.warning(f"Error reading Dominos timestamp: {e}")
        return datetime.now().timestamp()


def write_dominos_timestamp() -> None:
    """Write current timestamp to Dominos tracker file."""
    try:
        write_file(DOMINOS_TRACKER_FILE, str(datetime.now().timestamp()))
    except IOError as e:
        logger.error(f"Failed to update Dominos timestamp: {e}")

# ============================================================================
# FORMATTING UTILITIES
# ============================================================================


def format_timedelta(td: timedelta) -> str:
    """
    Format a timedelta into human-readable string.

    Args:
        td: Timedelta object to format

    Returns:
        Human-readable time string like "2 days, 3 hours"
    """
    seconds = int(td.total_seconds())
    periods = [
        ('year', SECONDS_PER_YEAR),
        ('month', SECONDS_PER_MONTH),
        ('day', SECONDS_PER_DAY),
        ('hour', SECONDS_PER_HOUR),
        ('minute', SECONDS_PER_MINUTE),
        ('second', 1)
    ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append(f"{period_value} {period_name}{has_s}")

    return ", ".join(strings) if strings else "0 seconds"

# ============================================================================
# MESSAGE HANDLING UTILITIES
# ============================================================================


def get_users(ctx: commands.Context) -> dict[int, str]:
    """
    Get mapping of user IDs to usernames for a guild.

    Args:
        ctx: Discord command context

    Returns:
        Dict mapping user ID to username
    """
    member_list = list(ctx.guild.members)
    return {member.id: member.name for member in member_list}


def find_message_by_id(
    all_messages: list[MessageDict],
    message_id: Optional[int]
) -> tuple[Optional[int], Optional[MessageDict]]:
    """
    Find a message by ID in message history.

    Args:
        all_messages: List of message dictionaries
        message_id: Message ID to find

    Returns:
        Tuple of (index, message) or (None, None) if not found
    """
    if message_id is None:
        return None, None

    for index, message in enumerate(all_messages):
        if message['message_id'] == message_id:
            return index, message
    return None, None


def build_message(
    ctx: commands.Context,
    message: discord.Message,
    text: str
) -> MessageDict:
    """
    Build a structured message dictionary for storage.

    Replaces user ID mentions with human-readable names.

    Args:
        ctx: Discord command context
        message: Original Discord message
        text: Processed message text

    Returns:
        Structured message dictionary with metadata
    """
    try:
        member_map = get_users(ctx)
        for uid, name in member_map.items():
            text = text.replace(str(uid), name)
    except Exception as e:
        logger.warning(f"Error replacing user IDs in message: {e}")

    return MessageDict(
        message_id=message.id,
        channel_id=message.channel.id,
        reference_id=message.reference.message_id if message.reference else None,
        name=message.author.name,
        text=text
    )


