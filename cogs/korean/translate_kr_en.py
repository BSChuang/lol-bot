"""Korean to English translation exercise cog."""

import random
import discord

from korean_config import logger
import anki_db
import gpt
from korean_state import (
    get_active_deck,
    set_exercise,
    clear_exercise,
)
from .base_handler import ExerciseHandler


class TranslateKrEnHandler(ExerciseHandler):
    """Handler for Korean to English translation exercises."""

    def __init__(self):
        super().__init__('translate_kr_en')

    async def generate_and_post_exercise(
        self,
        message: discord.Message,
        user_id: int
    ) -> None:
        """Generate and post a new translation exercise."""
        active_deck = get_active_deck(user_id)

        try:
            # Load words
            if active_deck == 'All':
                words = anki_db.get_all_words()
            else:
                words = anki_db.get_words_in_deck(active_deck)

            # Sample at most 15 words
            if len(words) > 15:
                words = random.sample(words, 15)

            if not words:
                await message.channel.send(
                    embed=discord.Embed(
                        title='❌ Empty Deck',
                        description=f'Deck **{active_deck}** has no words.',
                        color=discord.Color.red()
                    )
                )
                return

            # Korean to English
            direction = 'kr_to_en'

            # Generate exercise
            async with message.channel.typing():
                exercise = await gpt.generate_translation_exercise(words, direction)

            # Add metadata
            exercise['type'] = 'translate_kr_en'
            exercise['deck'] = active_deck

            # Store in state
            set_exercise(user_id, exercise)

            # Post exercise embed
            direction_label = '🇰🇷 → 🇺🇸'

            embed = discord.Embed(
                title=f'Translation Exercise {direction_label}',
                description=f'**{exercise["prompt"]}**',
                color=discord.Color.blue()
            )

            embed.set_footer(
                text=f'Active deck: {active_deck} · \'skip\' to reveal · \'stop\' to end · \'list\' for deck info'
            )

            await message.channel.send(embed=embed)
            logger.info(f'Generated Korean→English translation exercise for user {user_id} in deck {active_deck}')

        except RuntimeError as e:
            logger.exception(f'Error generating translation exercise: {e}')
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Generation Failed',
                    description='Could not generate exercise. Try again.',
                    color=discord.Color.red()
                )
            )
        except Exception as e:
            logger.exception(f'Unexpected error generating exercise: {e}')
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Error',
                    description='Something went wrong. Check the bot logs.',
                    color=discord.Color.red()
                )
            )

    async def grade_and_continue(
        self,
        message: discord.Message,
        user_id: int,
        exercise: dict,
        student_answer: str
    ) -> None:
        """Grade student response and generate next exercise."""
        try:
            # Grade response
            async with message.channel.typing():
                result = await gpt.grade_translation(
                    exercise['prompt'],
                    exercise['answer'],
                    student_answer,
                    exercise['direction']
                )

            # Clear current exercise
            clear_exercise(user_id)

            # Determine color
            score = result['score']
            if score >= 80:
                color = discord.Color.green()
            elif score >= 50:
                color = discord.Color.orange()
            else:
                color = discord.Color.red()

            # Post grade embed
            embed = discord.Embed(
                title=f'{"✅" if result["correct"] else "❌"} Score: {score}/100',
                color=color
            )

            embed.add_field(
                name='Your Answer',
                value=student_answer,
                inline=False
            )

            embed.add_field(
                name='Reference Answer',
                value=exercise['answer'],
                inline=False
            )

            if result.get('feedback'):
                embed.add_field(
                    name='Feedback',
                    value=result['feedback'],
                    inline=False
                )

            if result.get('corrected'):
                embed.add_field(
                    name='Corrected',
                    value=result['corrected'],
                    inline=False
                )

            await message.channel.send(embed=embed)
            logger.info(f'Graded Korean→English translation for user {user_id}: score {score}')

            # Generate next exercise
            await self.generate_and_post_exercise(message, user_id)

        except Exception as e:
            logger.exception(f'Error grading translation: {e}')
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Grading Failed',
                    description='Could not grade response. Try again.',
                    color=discord.Color.red()
                )
            )

    async def post_skip_reveal(self, channel: discord.TextChannel, exercise: dict) -> None:
        """Post reveal embed when user skips."""
        embed = discord.Embed(
            title='⏭️ Skipped',
            color=discord.Color.light_grey()
        )

        embed.add_field(
            name='Question',
            value=exercise['prompt'],
            inline=False
        )

        embed.add_field(
            name='Answer',
            value=exercise['answer'],
            inline=False
        )

        if exercise.get('words_used'):
            embed.add_field(
                name='Words Used',
                value=', '.join(exercise['words_used']),
                inline=False
            )

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.exception(f'Error posting skip reveal: {e}')


# Module-level handler instance
_handler = TranslateKrEnHandler()


async def handle(message: discord.Message) -> None:
    """Handle messages in Korean→English translation channel."""
    await _handler.handle(message)
