"""Configuration, constants, and logging setup for SpencerBot."""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from root directory
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# ============================================================================
# BOT CONFIGURATION
# ============================================================================

BOT_MENTION_ID: str = '<@1064717164579393577>'
MAX_MESSAGE_HISTORY: int = 500
MAX_CONTEXT_MESSAGES: int = 10

# API Keys and Tokens
DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
FFMPEG_PATH: str | None = os.getenv('FFMPEG_PATH') or None

# ============================================================================
# EMOTES
# ============================================================================

SPENCER_EMOTES: tuple[str, ...] = (
    '<:sadspencer:976908811904385104>',
    '<:spencer:968679218550550569>',
    '<:spencer2:972178114941714492>',
    '<:spencerangel:996846084712312853>',
    '<:spencerbaby:1017119767359926282>',
    '<:spencerflirt:1046478467191013447>',
    '<:supersadspencer:1002683850964611153>',
)

# ============================================================================
# REACTIONS
# ============================================================================

REACTION_PIZZA: str = "🍕"
REACTION_CRY: str = "😭"
REACTION_SPEAKER: str = "🔊"
REACTION_CLIPBOARD: str = "📋"
REACTION_CHECKMARK: str = "✅"
REACTION_THINKING: str = "🤔"

# ============================================================================
# FILE PATHS
# ============================================================================

DOMINOS_TRACKER_FILE: str = 'dominos.txt'

# ============================================================================
# TIME PERIODS (SECONDS)
# ============================================================================

SECONDS_PER_YEAR: int = 365 * 24 * 60 * 60
SECONDS_PER_MONTH: int = 30 * 24 * 60 * 60
SECONDS_PER_DAY: int = 24 * 60 * 60
SECONDS_PER_HOUR: int = 60 * 60
SECONDS_PER_MINUTE: int = 60

# ============================================================================
# LOGGING SETUP
# ============================================================================


def setup_logging() -> logging.Logger:
    """
    Configure and return the main logger for SpencerBot.

    Sets up both console and file logging with appropriate formats.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('spencerbot')
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'spencerbot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Initialize logger
logger = setup_logging()
logger.info("SpencerBot configuration loaded")
