"""Base handler class for Korean exercise channels."""

from abc import ABC, abstractmethod
import discord
import aiohttp

from korean_config import logger
import anki_db
import gpt
from korean_state import (
    get_active_deck,
    set_active_deck,
    get_exercise,
    set_exercise,
    clear_exercise,
    clear_active_deck,
)


class ExerciseHandler(ABC):
    """Base class for exercise channel handlers."""

    def __init__(self, exercise_type: str):
        """
        Initialize handler with exercise type.

        Args:
            exercise_type: Type identifier (e.g., 'translate', 'audio', 'dictation')
        """
        self.exercise_type = exercise_type

    async def _process_audio_attachment(self, message: discord.Message) -> str | None:
        """
        Process audio attachment from message and transcribe to text.

        Supported audio formats: mp3, wav, ogg, m4a, webm, flac

        Args:
            message: Discord message potentially containing audio attachment

        Returns:
            Transcribed text or None if no audio attachment found
        """
        audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.webm', '.flac')
        
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(audio_extensions):
                try:
                    # Download audio file
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status != 200:
                                logger.error(f'Failed to download audio: HTTP {resp.status}')
                                return None
                            audio_bytes = await resp.read()
                    
                    # Transcribe using OpenAI Whisper
                    transcribed_text = await gpt.transcribe_audio(audio_bytes, attachment.filename)
                    logger.info(f'Transcribed audio message from user {message.author.id}: {transcribed_text[:50]}...')
                    return transcribed_text
                
                except Exception as e:
                    logger.exception(f'Error processing audio attachment: {e}')
                    return None
        
        return None

    async def _get_student_answer(self, message: discord.Message) -> str | None:
        """
        Extract student answer from message - either text or audio.

        Args:
            message: Discord message

        Returns:
            Student answer text or None if neither text nor audio found
        """
        # Try audio first
        if message.attachments:
            audio_text = await self._process_audio_attachment(message)
            if audio_text:
                return audio_text
        
        # Fall back to text content
        text = message.content.strip()
        if text:
            return text
        
        return None


    async def handle(self, message: discord.Message) -> None:
        """
        Handle messages in exercise channel.

        Common flow for all exercise types:
        1. Check reserved keywords (stop, skip, list, all)
        2. Try deck name resolution
        3. If no active deck, prompt for deck selection
        4. If exercise pending, grade response
        5. If no exercise, generate new one
        """
        user_id = message.author.id
        text = message.content.strip()
        text_lower = text.lower()

        # 1. Reserved keywords
        if text_lower == 'stop':
            clear_exercise(user_id)
            clear_active_deck(user_id)
            await message.channel.send(
                embed=discord.Embed(
                    title='Session Ended',
                    description='Send any message to start again.',
                    color=discord.Color.light_grey()
                )
            )
            return

        if text_lower == 'skip':
            exercise = get_exercise(user_id)
            if exercise:
                await self.post_skip_reveal(message.channel, exercise)
                await self.generate_and_post_exercise(message, user_id)
            return

        if text_lower == 'list':
            await self._handle_list(message, user_id)
            return

        if text_lower == 'all':
            await self._handle_all(message, user_id)
            return

        # 2. Try deck name resolution
        try:
            deck_name = anki_db.resolve_deck_name(text)
            if deck_name:
                set_active_deck(user_id, deck_name)
                clear_exercise(user_id)
                words = anki_db.get_words_in_deck(deck_name)

                if not words:
                    await message.channel.send(
                        embed=discord.Embed(
                            title='❌ Empty Deck',
                            description=f'Deck **{deck_name}** has no notes. Add cards in Anki first.',
                            color=discord.Color.red()
                        )
                    )
                    return

                await message.channel.send(
                    embed=discord.Embed(
                        title='✅ Deck Selected',
                        description=f'Active deck set to **{deck_name}** ({len(words)} words).\n\nSend any message to start.',
                        color=discord.Color.teal()
                    )
                )
                return

        except RuntimeError as e:
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Anki Error',
                    description=str(e),
                    color=discord.Color.red()
                )
            )
            return

        # 3. Check if deck is selected
        active_deck = get_active_deck(user_id)
        if not active_deck:
            await self._handle_no_deck(message)
            return

        # 4. Check if exercise is pending
        exercise = get_exercise(user_id)
        if exercise:
            # Ensure exercise type matches this channel
            if exercise.get('type') == self.exercise_type:
                # Get student answer - supports both text and audio
                student_answer = await self._get_student_answer(message)
                if not student_answer:
                    await message.channel.send(
                        embed=discord.Embed(
                            title='❌ No Answer',
                            description='Please send a text message or audio recording.',
                            color=discord.Color.red()
                        )
                    )
                    return
                
                await self.grade_and_continue(message, user_id, exercise, student_answer)
                return
            else:
                # Wrong exercise type, clear and generate new one
                clear_exercise(user_id)

        # 5. Generate new exercise
        await self.generate_and_post_exercise(message, user_id)

    async def _handle_list(self, message: discord.Message, user_id: int) -> None:
        """Handle 'list' command - show active deck and available decks."""
        try:
            active_deck = get_active_deck(user_id)
            deck_names = anki_db.get_deck_names()
            deck_list = '\n'.join(f'• {name}' for name in deck_names)

            if active_deck:
                # Use get_all_words for 'All' deck, otherwise get words from specific deck
                if active_deck == 'All':
                    words = anki_db.get_all_words()
                else:
                    words = anki_db.get_words_in_deck(active_deck)
                description = f'**Active: {active_deck}** ({len(words)} words)\n\n**Available decks:**\n{deck_list}'
            else:
                description = f'**No Deck Selected**\n\n**Available decks:**\n{deck_list}'

            await message.channel.send(
                embed=discord.Embed(
                    title='Deck List',
                    description=description,
                    color=discord.Color.teal()
                )
            )
        except Exception as e:
            logger.error(f'Error getting deck list: {e}')
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Error',
                    description='Could not retrieve deck list.',
                    color=discord.Color.red()
                )
            )

    async def _handle_all(self, message: discord.Message, user_id: int) -> None:
        """Handle 'all' command - select all decks."""
        try:
            set_active_deck(user_id, 'All')
            clear_exercise(user_id)
            words = anki_db.get_all_words()

            if not words:
                await message.channel.send(
                    embed=discord.Embed(
                        title='❌ No Words',
                        description='No words found in any deck. Add cards in Anki first.',
                        color=discord.Color.red()
                    )
                )
                return

            await message.channel.send(
                embed=discord.Embed(
                    title='✅ All Decks Selected',
                    description=f'Active deck set to **All** ({len(words)} words from all decks).\n\nSend any message to start.',
                    color=discord.Color.teal()
                )
            )

        except RuntimeError as e:
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Anki Error',
                    description=str(e),
                    color=discord.Color.red()
                )
            )

    async def _handle_no_deck(self, message: discord.Message) -> None:
        """Handle case where no deck is selected."""
        try:
            deck_names = anki_db.get_deck_names()
            deck_list = '\n'.join(f'• {name}' for name in deck_names)

            await message.channel.send(
                embed=discord.Embed(
                    title='No Deck Selected',
                    description=f'Type a deck name to begin.\n\n**Available decks:**\n{deck_list}',
                    color=discord.Color.orange()
                )
            )
        except Exception:
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Error',
                    description='Could not retrieve deck list.',
                    color=discord.Color.red()
                )
            )

    # Abstract methods that subclasses must implement

    @abstractmethod
    async def generate_and_post_exercise(
        self,
        message: discord.Message,
        user_id: int
    ) -> None:
        """Generate and post exercise. Must be implemented by subclass."""
        pass

    @abstractmethod
    async def grade_and_continue(
        self,
        message: discord.Message,
        user_id: int,
        exercise: dict,
        student_answer: str
    ) -> None:
        """Grade response and generate next exercise. Must be implemented by subclass."""
        pass

    @abstractmethod
    async def post_skip_reveal(
        self,
        channel: discord.TextChannel,
        exercise: dict
    ) -> None:
        """Post reveal embed when user skips. Must be implemented by subclass."""
        pass
