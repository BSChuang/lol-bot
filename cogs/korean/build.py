"""Sentence building exercise cog for Korean bot - #build channel."""

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


class BuildHandler(ExerciseHandler):
    """Handler for sentence building exercises."""

    def __init__(self):
        super().__init__('build')

    async def generate_and_post_exercise(
        self,
        message: discord.Message,
        user_id: int
    ) -> None:
        """Generate and post sentence building exercise."""
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
                exercise = await gpt.generate_build_exercise(words)

            exercise['type'] = 'build'
            exercise['deck'] = active_deck
            set_exercise(user_id, exercise)

            embed = discord.Embed(
                title='🏗️ Sentence Building Exercise',
                description='Build a sentence using the given words.',
                color=discord.Color.blue()
            )

            # Add given words
            words_text = '\n'.join(
                f"• {w['korean']} ({w['english']})"
                for w in exercise.get('given_words', [])
            )
            if words_text:
                embed.add_field(name='Given Words', value=words_text, inline=False)

            if exercise.get('difficulty_note'):
                embed.add_field(name='Difficulty Note', value=exercise['difficulty_note'], inline=False)

            embed.set_footer(
                text=f'Active deck: {active_deck} · \'skip\' to reveal · \'stop\' to end · \'list\' for deck info'
            )

            await message.channel.send(embed=embed)
            logger.info(f'Generated build exercise for user {user_id}')

        except Exception as e:
            logger.exception(f'Error generating build exercise: {e}')
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
        """Grade sentence building response and generate next exercise."""
        try:
            async with message.channel.typing():
                result = await gpt.grade_build(
                    exercise['given_words'],
                    exercise['example_answer'],
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
                title=f'{"✅" if result["correct"] else "❌"} Score: {score}/100',
                color=color
            )

            embed.add_field(name='Your Sentence', value=student_answer, inline=False)

            all_words = '✅' if result.get('all_words_used') else '❌'
            grammar = '✅' if result.get('grammar_correct') else '❌'
            embed.add_field(name='All Words Used', value=all_words, inline=True)
            embed.add_field(name='Grammar Correct', value=grammar, inline=True)

            if result.get('feedback'):
                embed.add_field(name='Feedback', value=result['feedback'], inline=False)

            embed.add_field(
                name='Example Answer',
                value=result.get('example_answer', exercise.get('example_answer', '?')),
                inline=False
            )

            await message.channel.send(embed=embed)
            await self.generate_and_post_exercise(message, user_id)

        except Exception as e:
            logger.exception(f'Error grading build: {e}')
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
            name='Example Answer',
            value=exercise.get('example_answer', '?'),
            inline=False
        )

        words_text = '\n'.join(
            f"• {w['korean']} ({w['english']})"
            for w in exercise.get('given_words', [])
        )
        if words_text:
            embed.add_field(name='Given Words', value=words_text, inline=False)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.exception(f'Error posting skip reveal: {e}')


# Module-level handler instance
_handler = BuildHandler()


async def handle(message: discord.Message) -> None:
    """Handle messages in #build channel."""
    await _handler.handle(message)
