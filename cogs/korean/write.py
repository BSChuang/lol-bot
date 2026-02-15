"""Free writing exercise cog for Korean bot - #write channel."""

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


class WriteHandler(ExerciseHandler):
    """Handler for free writing exercises."""

    def __init__(self):
        super().__init__('write')

    async def generate_and_post_exercise(
        self,
        message: discord.Message,
        user_id: int
    ) -> None:
        """Generate and post free writing exercise."""
        active_deck = get_active_deck(user_id)

        try:
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

            async with message.channel.typing():
                exercise = await gpt.generate_write_prompt(words)

            exercise['type'] = 'write'
            exercise['deck'] = active_deck
            set_exercise(user_id, exercise)

            embed = discord.Embed(
                title='✏️ Free Writing Exercise',
                description=exercise['prompt'],
                color=discord.Color.blue()
            )

            target_words = ', '.join(exercise.get('target_words', []))
            if target_words:
                embed.add_field(name='Target Words', value=target_words, inline=False)

            if exercise.get('english_hint'):
                embed.add_field(name='Hint', value=exercise['english_hint'], inline=False)

            embed.set_footer(
                text=f'Active deck: {active_deck} · \'skip\' to reveal · \'stop\' to end · \'list\' for deck info'
            )

            await message.channel.send(embed=embed)
            logger.info(f'Generated write exercise for user {user_id}')

        except Exception as e:
            logger.exception(f'Error generating write exercise: {e}')
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ Generation Failed',
                    description='Could not generate exercise. Try again.',
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
        """Grade writing and generate next exercise."""
        try:
            async with message.channel.typing():
                result = await gpt.grade_writing(
                    exercise['prompt'],
                    exercise['target_words'],
                    student_answer
                )

            clear_exercise(user_id)

            score = result.get('score', 0)
            if score >= 80:
                color = discord.Color.green()
            elif score >= 50:
                color = discord.Color.orange()
            else:
                color = discord.Color.red()

            embed = discord.Embed(
                title=f'Score: {score}/100',
                color=color
            )

            # Target words
            used = ', '.join(result.get('target_words_used', []))
            missed = ', '.join(result.get('target_words_missed', []))
            if used:
                embed.add_field(name='✅ Words Used', value=used, inline=False)
            if missed:
                embed.add_field(name='❌ Words Missed', value=missed, inline=False)

            # Corrections
            for corr in result.get('corrections', [])[:5]:
                embed.add_field(
                    name='Correction',
                    value=f"**{corr.get('original')}** → **{corr.get('corrected')}**\n{corr.get('explanation', '')}",
                    inline=False
                )

            if result.get('overall_feedback'):
                embed.add_field(name='Feedback', value=result['overall_feedback'], inline=False)

            if result.get('improved_version'):
                embed.add_field(name='Improved Version', value=result['improved_version'], inline=False)

            await message.channel.send(embed=embed)
            await self.generate_and_post_exercise(message, user_id)

        except Exception as e:
            logger.exception(f'Error grading writing: {e}')
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

        embed.add_field(name='Prompt', value=exercise.get('prompt', '?'), inline=False)
        target_words = ', '.join(exercise.get('target_words', []))
        if target_words:
            embed.add_field(name='Target Words', value=target_words, inline=False)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.exception(f'Error posting skip reveal: {e}')


# Module-level handler instance
_handler = WriteHandler()


async def handle(message: discord.Message) -> None:
    """Handle messages in #write channel."""
    await _handler.handle(message)
