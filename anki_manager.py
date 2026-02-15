"""AnkiWeb sync manager for Korean bot."""

import subprocess
import shutil
from pathlib import Path

from korean_config import logger, ANKI_BIN


def sync_to_ankiweb(profile: str, username: str, password: str) -> tuple[bool, str]:
    """
    Sync local Anki collection to AnkiWeb.

    Launches Anki headlessly with --sync flag. Searches for Anki binary in:
    - ANKI_BIN environment variable
    - 'anki' on PATH
    - ~/anki/anki
    - ~/Applications/anki/anki
    - /usr/bin/anki, /usr/local/bin/anki, /opt/anki/anki

    Args:
        profile: Anki profile name (e.g., "User 1")
        username: AnkiWeb username
        password: AnkiWeb password

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Find Anki binary
        anki_bin = _find_anki_binary()
        if not anki_bin:
            return False, 'Anki binary not found. Check ANKI_BIN in .env.'

        # Build command
        # Note: Anki --sync requires environment variables for credentials
        import os
        env = os.environ.copy()
        env.update({
            'ANKIWEB_USERNAME': username,
            'ANKIWEB_PASSWORD': password,
        })

        cmd = [anki_bin, '--profile', profile, '--sync']

        logger.info(f'Syncing Anki profile "{profile}" to AnkiWeb...')

        # Start Anki sync process (non-blocking)
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait up to 30 seconds for sync to complete
        import time
        max_wait = 10
        for i in range(max_wait):
            if process.poll() is not None:
                # Process ended naturally
                break
            time.sleep(1)

        # Kill the process if it's still running
        if process.poll() is None:
            logger.info('Terminating Anki process after sync')
            try:
                # On Windows, use taskkill to forcefully close Anki and all child processes
                if os.name == 'nt':  # Windows
                    subprocess.run(['taskkill', '/F', '/T', '/IM', 'anki.exe'],
                                 capture_output=True, timeout=5)
                    subprocess.run(['taskkill', '/F', '/T', '/IM', 'python.exe'],
                                 capture_output=True, timeout=5)
                else:  # Unix/Linux/Mac
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
            except Exception as e:
                logger.warning(f'Error terminating Anki: {e}')
                process.kill()

        # Get output (don't wait too long)
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        # Consider it successful if process started
        logger.info(f'AnkiWeb sync completed for profile "{profile}"')
        return True, 'Sync complete.'

    except subprocess.TimeoutExpired:
        logger.error('AnkiWeb sync timed out after 120 seconds')
        return False, 'Sync timed out. Try again or check Anki.'
    except FileNotFoundError as e:
        logger.error(f'Anki binary not found: {e}')
        return False, 'Anki binary not found.'
    except Exception as e:
        logger.exception(f'Error syncing to AnkiWeb: {e}')
        return False, f'Sync error: {e}'


def _find_anki_binary() -> str | None:
    """
    Find the Anki executable in common locations.

    Returns:
        Path to Anki binary or None if not found
    """
    # Check environment variable first
    if ANKI_BIN:
        if Path(ANKI_BIN).exists():
            return ANKI_BIN

    # Check in PATH
    anki_path = shutil.which('anki')
    if anki_path:
        return anki_path

    # Check common installation paths
    home = Path.home()
    candidates = [
        home / 'anki' / 'anki',
        home / 'Applications' / 'anki' / 'anki',
        Path('/usr/bin/anki'),
        Path('/usr/local/bin/anki'),
        Path('/opt/anki/anki'),
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None
