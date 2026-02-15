"""Base handler class for Korean exercise channels."""

from abc import ABC, abstractmethod
import discord

from korean_config import logger
import anki_db
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
                await self.grade_and_continue(message, user_id, exercise, text)
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
            deck_list = '\n'.join(f'• {name}' for name in deck_names[:10])
            if len(deck_names) > 10:
                deck_list += f'\n... and {len(deck_names) - 10} more'

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
            deck_list = '\n'.join(f'• {name}' for name in deck_names[:10])
            if len(deck_names) > 10:
                deck_list += f'\n... and {len(deck_names) - 10} more'

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
