"""Event handlers for SpencerBot and Korean Language Learning Bot."""

import asyncio
import discord
from discord.ext import commands

from config import (
    logger,
    BOT_MENTION_ID,
    REACTION_PIZZA,
    REACTION_CRY,
    REACTION_SPEAKER,
    REACTION_CLIPBOARD,
    REACTION_CHECKMARK,
    REACTION_THINKING,
)
from state import BotState
from utils import build_message
from handlers import (
    cmd_dominos,
    cmd_relapse,
    cmd_toggle_speak,
    cmd_speak,
    cmd_leave,
    cmd_summarize,
    cmd_fact_check,
    cmd_gpt_chat,
)
from dapi import command

# Korean bot imports
from korean_config import (
    ALLOWED_GUILD_ID,
    CHANNEL_VOCAB,
    CHANNEL_TRANSLATE,
    CHANNEL_AUDIO,
    CHANNEL_DICTATION,
    CHANNEL_CLOZE,
    CHANNEL_READING,
    CHANNEL_WRITE,
    CHANNEL_BUILD,
    ANKIWEB_USER,
    ANKIWEB_PASS,
    ANKI_PROFILE,
)
import anki_manager
from cogs.korean import (
    vocab,
    translate,
    audio_cog,
    dictation,
    cloze,
    reading,
    write,
    build,
)


def setup_events(bot: commands.Bot, bot_state: BotState) -> None:
    """
    Register event handlers for SpencerBot and Korean Language Learning Bot.

    Args:
        bot: Discord bot instance
        bot_state: Bot state manager
    """
    # Korean bot channel routing map
    korean_channel_map = {
        CHANNEL_VOCAB: vocab.handle,
        CHANNEL_TRANSLATE: translate.handle,
        CHANNEL_AUDIO: audio_cog.handle,
        CHANNEL_DICTATION: dictation.handle,
        CHANNEL_CLOZE: cloze.handle,
        CHANNEL_READING: reading.handle,
        CHANNEL_WRITE: write.handle,
        CHANNEL_BUILD: build.handle,
    }

    @bot.event
    async def on_ready() -> None:
        """Log bot readiness."""
        logger.info('Korean Language Learning Bot active')
        logger.info(f'Korean bot restricted to guild ID: {ALLOWED_GUILD_ID}')

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """
        Main message handler for both SpencerBot and Korean Language Learning Bot.

        Args:
            message: Discord message object
        """
        # Ignore own messages
        if message.author == bot.user:
            return

        # ============================================================================
        # SPENCERBOT MESSAGE HANDLING
        # ============================================================================
        try:
            ctx = await bot.get_context(message)
            text = message.content.replace(BOT_MENTION_ID, '').strip()

            # Build and store message
            new_message = build_message(ctx, message, text)
            bot_state.all_messages.append(new_message)

            # Parse command
            if ' ' in text:
                input_cmd, input_text = text.split(' ', 1)
            else:
                input_cmd, input_text = text, None

            # Handle TTS for enabled users
            if bot_state.is_tts_enabled(message.author.id):
                await cmd_speak(message, ctx, bot, text)

            # Process SpencerBot commands if mentioned
            if message.content.startswith(BOT_MENTION_ID):
                # Helper for command routing
                async def send_command(
                    cmd_name: str,
                    reaction: str,
                    fn
                ) -> bool:
                    """Route command to handler with reaction."""
                    return await command(message, input_cmd, cmd_name, reaction, fn)

                # Command routing
                command_list = [
                    await send_command('dominos', REACTION_PIZZA, cmd_dominos),
                    await send_command('relapse', REACTION_CRY, cmd_relapse),
                    await send_command(
                        'st',
                        REACTION_SPEAKER,
                        lambda: cmd_toggle_speak(
                            message.author.id,
                            bot_state,
                            ctx,
                            bot
                        )
                    ),
                    await send_command(
                        'l',
                        REACTION_SPEAKER,
                        lambda: cmd_leave(ctx, bot)
                    ),
                    await send_command(
                        'stop',
                        REACTION_SPEAKER,
                        lambda: cmd_leave(ctx, bot)
                    ),
                    await send_command(
                        'summarize',
                        REACTION_CLIPBOARD,
                        lambda: cmd_summarize(new_message, bot_state)
                    ),
                    await send_command(
                        'check',
                        REACTION_CHECKMARK,
                        lambda: cmd_fact_check(new_message, bot_state)
                    ),
                ]

                # Default to GPT chat if no command matched
                if not any(command_list):
                    await command(
                        message,
                        text,
                        None,
                        REACTION_THINKING,
                        lambda: cmd_gpt_chat(bot_state, text)
                    )

        except discord.DiscordException as e:
            logger.error(f"Discord API error in on_message: {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error processing message {message.id}: {e}"
            )

        # ============================================================================
        # KOREAN BOT MESSAGE HANDLING
        # ============================================================================
        # Only process Korean bot in allowed guild
        if message.guild is None or message.guild.id != ALLOWED_GUILD_ID:
            return

        try:
            # Check for !sync command
            if message.content.strip().lower() == '!sync':
                logger.info(f'Processing !sync command from user {message.author.id}')
                await message.channel.send('⏳ Syncing... Make sure Anki is closed.')

                # Run sync in executor to avoid blocking
                loop = asyncio.get_event_loop()
                success, sync_message = await loop.run_in_executor(
                    None,
                    anki_manager.sync_to_ankiweb,
                    ANKI_PROFILE,
                    ANKIWEB_USER,
                    ANKIWEB_PASS
                )

                if success:
                    await message.channel.send(f'✅ {sync_message}')
                    logger.info(f'User {message.author.id} completed AnkiWeb sync')
                else:
                    await message.channel.send(f'❌ {sync_message}')
                    logger.error(f'AnkiWeb sync failed for user {message.author.id}: {sync_message}')
                return

            # Route to Korean learning channel handlers
            handler = korean_channel_map.get(message.channel.id)
            if handler:
                await handler(message)

        except discord.DiscordException as e:
            logger.error(f'Discord API error in Korean bot: {e}')
            try:
                await message.channel.send(
                    embed=discord.Embed(
                        title='❌ Discord Error',
                        description='A Discord API error occurred. Try again.',
                        color=discord.Color.red()
                    )
                )
            except Exception:
                pass

        except Exception as e:
            logger.exception(f'Error in Korean bot handler: {e}')
            try:
                await message.channel.send(
                    embed=discord.Embed(
                        title='❌ Error',
                        description='Something went wrong. Check the bot logs.',
                        color=discord.Color.red()
                    )
                )
            except Exception:
                pass

    @bot.tree.command(
        name='sync',
        description='Sync your local Anki collection to AnkiWeb.'
    )
    async def sync_command(interaction: discord.Interaction) -> None:
        """Slash command to trigger AnkiWeb sync."""
        # Guild restriction check
        if interaction.guild_id != ALLOWED_GUILD_ID:
            await interaction.response.send_message(
                'This bot is not available in this server.',
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            'Syncing... Make sure Anki is closed.',
            ephemeral=True
        )

        try:
            # Run sync in executor to avoid blocking
            loop = asyncio.get_event_loop()
            success, sync_message = await loop.run_in_executor(
                None,
                anki_manager.sync_to_ankiweb,
                ANKI_PROFILE,
                ANKIWEB_USER,
                ANKIWEB_PASS
            )

            if success:
                await interaction.followup.send(
                    f'✓ {sync_message}',
                    ephemeral=True
                )
                logger.info(f'User {interaction.user.id} completed AnkiWeb sync')
            else:
                await interaction.followup.send(
                    f'✗ {sync_message}',
                    ephemeral=True
                )
                logger.error(f'AnkiWeb sync failed for user {interaction.user.id}: {sync_message}')

        except Exception as e:
            logger.exception(f'Error in /sync command: {e}')
            await interaction.followup.send(
                '❌ Sync failed. Check bot logs.',
                ephemeral=True
            )
