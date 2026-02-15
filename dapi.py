"""Discord API utility functions for SpencerBot."""

import asyncio
import os
from pathlib import Path
from typing import Optional, Callable, Union

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Constants
FFMPEG_PATH: Optional[str] = os.getenv('FFMPEG_PATH')
MAX_MESSAGE_LENGTH: int = 2000
CHUNK_SIZE: int = 1999  # Leave room for safety margin
VOICE_CONNECTION_DELAY: float = 0.5  # Seconds to wait after connecting


# ============================================================================
# MESSAGE UTILITIES
# ============================================================================

async def reply(message: discord.Message, content: Union[str, discord.File]) -> None:
    """
    Reply to a message, chunking text if necessary.

    Args:
        message: Discord message to reply to
        content: Text string or file to send. Long strings are automatically chunked.
    """
    if isinstance(content, str):
        # Split long messages into chunks
        for i in range(0, len(content), CHUNK_SIZE):
            await message.channel.send(content[i:i + CHUNK_SIZE])
    else:
        await message.channel.send(file=content)


async def react(message: discord.Message, emoji: str) -> None:
    """
    Add a reaction to a message.

    Args:
        message: Discord message to react to
        emoji: Emoji string to add as reaction
    """
    await message.add_reaction(emoji)


# ============================================================================
# VOICE UTILITIES
# ============================================================================

async def speak(ctx: commands.Context, bot: commands.Bot, audio_path: str) -> None:
    """
    Join voice channel and play audio file.

    Automatically connects to the user's voice channel, switches channels if needed,
    and plays the specified audio file using FFmpeg.

    Args:
        ctx: Command context containing author and guild info
        bot: Bot instance with voice client access
        audio_path: Path to audio file to play

    Returns:
        None if user is not in a voice channel
    """
    if ctx.author.voice is None:
        return

    voice_channel = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # Handle existing connection
    if voice_client:
        if voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        if voice_client.is_playing():
            voice_client.stop()
    else:
        # Clean up any stale connections
        stale_clients = [vc for vc in bot.voice_clients if vc.guild == ctx.guild]
        for vc in stale_clients:
            await vc.disconnect(force=True)

        # Connect to voice channel
        voice_client = await voice_channel.connect(self_deaf=True, timeout=30.0)
        await asyncio.sleep(VOICE_CONNECTION_DELAY)

    # Play audio file
    audio_source = discord.FFmpegPCMAudio(
        source=audio_path,
        executable=FFMPEG_PATH
    )
    voice_client.play(audio_source)


async def disconnect(ctx: commands.Context, bot: commands.Bot) -> None:
    """
    Disconnect from voice channel in the current guild.

    Args:
        ctx: Command context containing guild info
        bot: Bot instance with voice client access
    """
    if not bot.voice_clients:
        await ctx.send("The bot is not connected to any voice channel.")
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("The bot is not connected to any voice channel in this server.")


# ============================================================================
# COMMAND ROUTING
# ============================================================================

async def command(
    message: discord.Message,
    input_cmd: str,
    cmd: Optional[str],
    reaction: str,
    fn: Callable
) -> bool:
    """
    Route and execute a command with reaction feedback.

    Args:
        message: Discord message that triggered the command
        input_cmd: Actual command string from user input
        cmd: Expected command name (without !)
        reaction: Emoji to react with
        fn: Async function to execute for this command

    Returns:
        True if command was matched and executed, False otherwise
    """
    # Check if command matches
    if cmd is not None and input_cmd != f'!{cmd}':
        return False

    # Add reaction to acknowledge command
    await react(message, reaction)

    # Execute command function
    output = await fn()

    # Handle command output
    if output is None:
        return True

    # Send output, chunking if necessary
    if isinstance(output, str) and len(output) > CHUNK_SIZE:
        while len(output) > CHUNK_SIZE:
            await reply(message, output[:CHUNK_SIZE])
            output = output[CHUNK_SIZE:]

    await reply(message, output)
    return True
