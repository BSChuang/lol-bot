"""Dictation exercise cog for Korean bot - #dictation channel."""

import io
import random
import discord

from korean_config import logger
import anki_db
import gpt
import audio
from korean_state import (
    get_active_deck,
    set_exercise,
    clear_exercise,
)
from .base_handler import ExerciseHandler


class DictationHandler(ExerciseHandler):
    """Handler for dictation exercises."""

    def __init__(self):
        super().__init__('dictation')

    async def generate_and_post_exercise(
        self,
        message: discord.Message,
        user_id: int
    ) -> None:
        """Generate and post dictation exercise with TTS."""
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
                exercise = await gpt.generate_dictation_exercise(words)

            exercise['type'] = 'dictation'
            exercise['deck'] = active_deck
            set_exercise(user_id, exercise)

            try:
                mp3_bytes = await audio.generate_tts(exercise['tts_text'], korean_accent=True)
                audio_file = discord.File(io.BytesIO(mp3_bytes), filename='audio.mp3')

                embed = discord.Embed(
                    title='🎤 Dictation Exercise',
                    description='Listen and type what you hear in Korean.',
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name='English',
                    value=exercise['english'],
                    inline=False
                )

                embed.set_footer(
                    text=f'Active deck: {active_deck} · \'skip\' to reveal · \'stop\' to end · \'list\' for deck info'
                )

                await message.channel.send(embed=embed, file=audio_file)
                logger.info(f'Generated dictation exercise for user {user_id}')

            except RuntimeError:
                logger.warning('TTS failed, posting text-only')
                embed = discord.Embed(
                    title='🎤 Dictation Exercise',
                    description='(Audio unavailable)',
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name='English',
                    value=exercise['english'],
                    inline=False
                )

                embed.set_footer(
                    text=f'Active deck: {active_deck} · \'skip\' to reveal · \'stop\' to end · \'list\' for deck info'
                )

                await message.channel.send(embed=embed)

        except Exception as e:
            logger.exception(f'Error generating dictation exercise: {e}')
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
        """Grade dictation response and generate next exercise."""
        try:
            async with message.channel.typing():
                result = await gpt.grade_dictation(
                    exercise['korean'],
                    student_answer
                )

            clear_exercise(user_id)

            score = result['score']
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

            embed.add_field(name='Your Answer', value=student_answer, inline=False)
            embed.add_field(name='Correct Answer', value=exercise['korean'], inline=False)

            if result.get('feedback'):
                embed.add_field(name='Feedback', value=result['feedback'], inline=False)

            if result.get('diff'):
                embed.add_field(name='Diff', value=result['diff'], inline=False)

            await message.channel.send(embed=embed)
            await self.generate_and_post_exercise(message, user_id)

        except Exception as e:
            logger.exception(f'Error grading dictation: {e}')
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

        embed.add_field(name='Korean', value=exercise['korean'], inline=False)
        embed.add_field(name='English', value=exercise['english'], inline=False)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.exception(f'Error posting skip reveal: {e}')


# Module-level handler instance
_handler = DictationHandler()


async def handle(message: discord.Message) -> None:
    """Handle messages in #dictation channel."""
    await _handler.handle(message)
