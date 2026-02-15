"""Event handlers for Korean Language Learning Bot."""

import asyncio
import discord
from discord.ext import commands

from korean_config import (
    logger,
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


def setup_korean_events(bot: commands.Bot) -> None:
    """
    Register event handlers for Korean Language Learning Bot.

    Args:
        bot: Discord bot instance
    """
    # Channel routing map
    channel_map = {
        CHANNEL_VOCAB: vocab.handle,
        CHANNEL_TRANSLATE: translate.handle,
        CHANNEL_AUDIO: audio_cog.handle,
        CHANNEL_DICTATION: dictation.handle,
        CHANNEL_CLOZE: cloze.handle,
        CHANNEL_READING: reading.handle,
        CHANNEL_WRITE: write.handle,
        CHANNEL_BUILD: build.handle,
    }

    # Save the original on_message handler (SpencerBot's)
    original_on_message = None
    for listener in bot._listeners:
        if listener[0] == 'message' and listener[1].__name__ == 'on_message':
            original_on_message = listener[1]
            break

    @bot.event
    async def on_ready() -> None:
        """Log Korean bot readiness."""
        logger.info('Korean Language Learning Bot active')
        logger.info(f'Korean bot restricted to guild ID: {ALLOWED_GUILD_ID}')

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """Handle messages for Korean Language Learning Bot."""
        # CRITICAL: Call SpencerBot's original on_message FIRST
        # This ensures SpencerBot features work in all guilds
        if original_on_message:
            try:
                await original_on_message(message)
            except Exception as e:
                logger.error(f'Error in SpencerBot on_message: {e}')

        # Ignore own messages
        if message.author == bot.user:
            return

        # GUILD RESTRICTION - CRITICAL SECURITY CHECK
        # Only process Korean bot features in allowed guild
        if message.guild is None or message.guild.id != ALLOWED_GUILD_ID:
            logger.debug(
                f'Ignored Korean bot message from unauthorized guild: '
                f'{message.guild.id if message.guild else "DM"}'
            )
            return

        try:
            # Check for !sync command
            logger.debug(f'Korean bot received message: "{message.content}" in channel {message.channel.id}')
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

            # Route to channel handler
            handler = channel_map.get(message.channel.id)
            if handler:
                await handler(message)

        except discord.DiscordException as e:
            logger.error(f'Discord API error in Korean bot on_message: {e}')
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
            logger.exception(f'Error handling Korean bot message {message.id}: {e}')
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
