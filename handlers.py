"""Command handlers for SpencerBot."""

import random
import discord
from discord.ext import commands
from openai import AsyncOpenAI

import oai
from dapi import disconnect, speak

from config import (
    logger,
    SPENCER_EMOTES,
    MAX_CONTEXT_MESSAGES,
    OPENAI_API_KEY,
)
from state import BotState, MessageDict
from utils import (
    read_dominos_timestamp,
    write_dominos_timestamp,
    format_timedelta,
    find_message_by_id,
)
from datetime import datetime

# Initialize OpenAI client for TTS
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ============================================================================
# DOMINOS COMMANDS
# ============================================================================


async def cmd_dominos() -> str:
    """
    Report time since last Dominos order.

    Returns:
        Human-readable time string or error message
    """
    try:
        last_time = read_dominos_timestamp()
        elapsed = datetime.now() - datetime.fromtimestamp(last_time)
        return f"Last Dominos was {format_timedelta(elapsed)} ago"
    except Exception as e:
        logger.exception(f"Error in dominos command: {e}")
        return "Sorry, couldn't check Dominos history."


async def cmd_relapse() -> str:
    """
    Reset Dominos timer and return a Spencer emote.

    Returns:
        Random Spencer emote
    """
    try:
        write_dominos_timestamp()
        emote = random.choice(SPENCER_EMOTES)
        logger.info("Dominos timer reset")
        return emote
    except Exception as e:
        logger.exception(f"Error in relapse command: {e}")
        return "Sorry, couldn't record relapse."


# ============================================================================
# VOICE COMMANDS
# ============================================================================


async def cmd_toggle_speak(
    user_id: int,
    state: BotState,
    ctx: commands.Context,
    bot: commands.Bot
) -> str:
    """
    Toggle text-to-speech for the requesting user.

    When TTS is disabled, disconnects from voice if no other users have it enabled.

    Args:
        user_id: Discord user ID
        state: Bot state containing TTS user tracking
        ctx: Discord command context
        bot: Discord bot instance

    Returns:
        Status message indicating TTS state
    """
    try:
        enabled = state.toggle_tts(user_id)

        if not enabled and not state.has_any_tts_users():
            await disconnect(ctx, bot)
            logger.info(f"User {user_id} disabled TTS, disconnecting from voice")

        status = "activated" if enabled else "deactivated"
        logger.info(f"User {user_id} {status} TTS")
        return f"TTS {status}!"
    except Exception as e:
        logger.exception(f"Error toggling TTS: {e}")
        return "Sorry, couldn't toggle TTS."


async def generate_tts_file(text: str, voice: str = "onyx") -> str:
    """
    Generate TTS audio using OpenAI and save to file.

    Args:
        text: Text to convert to speech
        voice: OpenAI voice to use (alloy, echo, fable, onyx, nova, shimmer)

    Returns:
        Path to generated audio file

    Raises:
        RuntimeError: If TTS generation fails
    """
    try:
        response = await openai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
        )

        # Save to file
        output_path = "speech.mp3"
        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path

    except Exception as e:
        logger.exception(f"Error generating TTS: {e}")
        raise RuntimeError(f"Failed to generate audio: {e}")


async def cmd_speak(
    message: discord.Message,
    ctx: commands.Context,
    bot: commands.Bot,
    text: str
) -> None:
    """
    Generate and play TTS audio for a message.

    Uses OpenAI TTS with voice selection based on user preferences.

    Args:
        message: Discord message
        ctx: Discord command context
        bot: Discord bot instance
        text: Text to synthesize
    """
    try:
        # Map old Google Cloud voice config to OpenAI voices
        # For now, use "onyx" as default (can customize per user later)
        openai_voice = "onyx"

        if message.author != bot.user:
            path = await generate_tts_file(text, openai_voice)
            await speak(ctx, bot, path)
    except Exception as e:
        logger.exception(f"Error in TTS playback: {e}")


async def cmd_leave(ctx: commands.Context, bot: commands.Bot) -> None:
    """
    Leave voice channel.

    Args:
        ctx: Discord command context
        bot: Discord bot instance
    """
    try:
        await disconnect(ctx, bot)
    except Exception as e:
        logger.exception(f"Error leaving voice channel: {e}")


# ============================================================================
# CONVERSATION COMMANDS
# ============================================================================


async def cmd_summarize(new_message: MessageDict, state: BotState) -> str:
    """
    Summarize message thread starting from a referenced message.

    Args:
        new_message: Current message with reference
        state: Bot state containing message history

    Returns:
        Summarized message thread or error message
    """
    try:
        all_messages_list = list(state.all_messages)
        channel_messages = [
            msg for msg in all_messages_list
            if msg['channel_id'] == new_message['channel_id']
        ]
        index, referenced_message = find_message_by_id(
            channel_messages,
            new_message['reference_id']
        )

        if not referenced_message:
            return 'Message could not be found!'

        all_text = 'Summarize the following exchange of messages:\n\n'
        for message in channel_messages[index:]:
            all_text += f'{message["name"]}: {message["text"]}\n\n'

        return oai.call_gpt_single(all_text)
    except Exception as e:
        logger.exception(f"Error summarizing messages: {e}")
        return "Sorry, couldn't summarize messages."


async def cmd_fact_check(new_message: MessageDict, state: BotState) -> str:
    """
    Fact-check a referenced message with context.

    Args:
        new_message: Current message with reference
        state: Bot state containing message history

    Returns:
        Fact-check result or error message
    """
    try:
        all_messages_list = list(state.all_messages)
        channel_messages = [
            msg for msg in all_messages_list
            if msg['channel_id'] == new_message['channel_id']
        ]
        index, referenced_message = find_message_by_id(
            channel_messages,
            new_message['reference_id']
        )

        if not referenced_message:
            return 'Message could not be found!'

        prompt = (
            f'Fact check the following message, put an emphasis on recent '
            f'relevancy: {referenced_message["text"]}\n\n'
            f'Here are the previous {MAX_CONTEXT_MESSAGES} messages for context:\n'
        )

        start_idx = max(0, index - MAX_CONTEXT_MESSAGES)
        for message in channel_messages[start_idx:index]:
            prompt += f'{message["name"]}: {message["text"]}\n\n'

        return oai.call_gpt_single(prompt, 'gpt-4o-search-preview')
    except Exception as e:
        logger.exception(f"Error fact-checking message: {e}")
        return "Sorry, couldn't fact-check that message."


async def cmd_gpt_chat(state: BotState, text: str) -> str:
    """
    Chat with GPT using conversation history.

    Args:
        state: Bot state containing message history
        text: User message text

    Returns:
        GPT response or error message
    """
    try:
        oai.append_user_message(state.gpt_messages, text)
        answer = oai.call_gpt(state.gpt_messages, text)
        oai.append_assistant_message(state.gpt_messages, answer)
        logger.debug(f"GPT response generated for: {text[:50]}...")
        return answer
    except Exception as e:
        logger.exception(f"Error in GPT chat: {e}")
        return "Sorry, I couldn't process that request."
