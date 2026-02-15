"""
SpencerBot - Discord Bot with GPT Integration.

A feature-rich Discord bot that provides GPT chat, voice TTS, message
summarization, fact-checking, and more.
"""

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, logger
from state import BotState
from events import setup_events


def main() -> None:
    """Initialize and run the Discord bot."""
    try:
        # Validate configuration
        if not DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN not found in .env file")

        logger.info("Configuration loaded successfully")

        # Initialize Discord bot
        intents = discord.Intents.all()
        bot = commands.Bot(command_prefix='!', intents=intents)

        # Initialize bot state
        bot_state = BotState()
        logger.info("Bot state initialized")

        # Setup event handlers (includes both SpencerBot and Korean bot)
        setup_events(bot, bot_state)
        logger.info("Event handlers registered")

        # Connect and run bot
        logger.info("Connecting to Discord...")
        bot.run(DISCORD_TOKEN)

    except ValueError as e:
        logger.critical(str(e))
        logger.critical("Create .env file from .env.example and fill in required values")
        raise
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()
