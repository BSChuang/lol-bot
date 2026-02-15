"""Reading comprehension exercise cog for Korean bot - #reading channel."""

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


class ReadingHandler(ExerciseHandler):
    """Handler for reading comprehension exercises."""

    def __init__(self):
        super().__init__('reading')

    async def generate_and_post_exercise(
        self,
        message: discord.Message,
        user_id: int
    ) -> None:
        """Generate and post reading comprehension exercise."""
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
                exercise = await gpt.generate_reading_exercise(words)

            exercise['type'] = 'reading'
            exercise['deck'] = active_deck
            set_exercise(user_id, exercise)

            embed = discord.Embed(
                title='📖 Reading Comprehension',
                description='Read the story and answer the questions in English.',
                color=discord.Color.blue()
            )

            embed.add_field(
                name='Story',
                value=exercise['story_korean'],
                inline=False
            )

            embed.add_field(
                name='English (spoiler)',
                value=f'||{exercise["story_english"]}||',
                inline=False
            )

            # Add questions
            for i, question in enumerate(exercise.get('questions', []), 1):
                embed.add_field(
                    name=f'Question {i}',
                    value=question,
                    inline=False
                )

            embed.set_footer(
                text=f'Active deck: {active_deck} · \'skip\' to reveal · \'stop\' to end · \'list\' for deck info'
            )

            await message.channel.send(embed=embed)
            logger.info(f'Generated reading exercise for user {user_id}')

        except Exception as e:
            logger.exception(f'Error generating reading exercise: {e}')
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
        """Grade reading response and generate next exercise."""
        try:
            async with message.channel.typing():
                result = await gpt.grade_reading(
                    exercise['questions'],
                    exercise['answers'],
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

            # Show per-question results
            for res in result.get('results', []):
                symbol = '✅' if res.get('correct') else '❌'
                embed.add_field(
                    name=f'{symbol} {res.get("question", "Question")}',
                    value=res.get('feedback', ''),
                    inline=False
                )

            if result.get('overall_feedback'):
                embed.add_field(name='Overall Feedback', value=result['overall_feedback'], inline=False)

            await message.channel.send(embed=embed)
            await self.generate_and_post_exercise(message, user_id)

        except Exception as e:
            logger.exception(f'Error grading reading: {e}')
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

        for i, (question, answer) in enumerate(
            zip(exercise.get('questions', []), exercise.get('answers', [])), 1
        ):
            embed.add_field(
                name=f'Q{i}: {question}',
                value=answer,
                inline=False
            )

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.exception(f'Error posting skip reveal: {e}')


# Module-level handler instance
_handler = ReadingHandler()


async def handle(message: discord.Message) -> None:
    """Handle messages in #reading channel."""
    await _handler.handle(message)
