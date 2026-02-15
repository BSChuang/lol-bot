"""Configuration for Korean Language Learning Bot."""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv


# ============================================================================
# ENVIRONMENT LOADING
# ============================================================================

# Load .env from korean_bot directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


# ============================================================================
# DISCORD CONFIGURATION
# ============================================================================

DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')

# Guild restriction (Chil's server only)
try:
    ALLOWED_GUILD_ID: int = int(os.getenv('ALLOWED_GUILD_ID', '0'))
except ValueError:
    ALLOWED_GUILD_ID = 0


# ============================================================================
# CHANNEL IDS
# ============================================================================

try:
    CHANNEL_VOCAB: int = int(os.getenv('CHANNEL_VOCAB', '0'))
    CHANNEL_TRANSLATE_EN_KR: int = int(os.getenv('CHANNEL_TRANSLATE_EN_KR', '0'))
    CHANNEL_TRANSLATE_KR_EN: int = int(os.getenv('CHANNEL_TRANSLATE_KR_EN', '0'))
    CHANNEL_AUDIO: int = int(os.getenv('CHANNEL_AUDIO', '0'))
    CHANNEL_DICTATION: int = int(os.getenv('CHANNEL_DICTATION', '0'))
    CHANNEL_CLOZE: int = int(os.getenv('CHANNEL_CLOZE', '0'))
    CHANNEL_READING: int = int(os.getenv('CHANNEL_READING', '0'))
    CHANNEL_WRITE: int = int(os.getenv('CHANNEL_WRITE', '0'))
    CHANNEL_BUILD: int = int(os.getenv('CHANNEL_BUILD', '0'))
except ValueError as e:
    raise ValueError(f"Invalid channel ID configuration: {e}")


# ============================================================================
# ANKI CONFIGURATION
# ============================================================================

ANKI_PROFILE: str = os.getenv('ANKI_PROFILE', 'User 1')
ANKI_DB_PATH: str | None = os.getenv('ANKI_DB_PATH')
ANKIWEB_USER: str = os.getenv('ANKIWEB_USER', '')
ANKIWEB_PASS: str = os.getenv('ANKIWEB_PASS', '')
ANKI_BIN: str | None = os.getenv('ANKI_BIN')


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """
    Configure and return the main logger for Korean bot.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('korean_bot')
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'korean_bot.log',
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
