"""Audio listening exercise cog for Korean bot - #audio channel."""

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


class AudioHandler(ExerciseHandler):
    """Handler for audio listening exercises."""

    def __init__(self):
        super().__init__('audio')

    async def generate_and_post_exercise(
        self,
        message: discord.Message,
        user_id: int
    ) -> None:
        """Generate and post audio exercise with TTS."""
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

            # Generate exercise
            async with message.channel.typing():
                exercise = await gpt.generate_audio_exercise(words)

            # Add metadata
            exercise['type'] = 'audio'
            exercise['deck'] = active_deck
            set_exercise(user_id, exercise)

            # Try to generate TTS
            try:
                mp3_bytes = await audio.generate_tts(exercise['tts_text'], korean_accent=True)
                audio_file = discord.File(io.BytesIO(mp3_bytes), filename='audio.mp3')

                embed = discord.Embed(
                    title='🔊 Audio Exercise',
                    description='Listen to the audio and respond with the meaning.',
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name='Korean (spoiler)',
                    value=f'||{exercise["korean"]}||',
                    inline=False
                )

                embed.set_footer(
                    text=f'Active deck: {active_deck} · \'skip\' to reveal · \'stop\' to end · \'list\' for deck info'
                )

                await message.channel.send(embed=embed, file=audio_file)
                logger.info(f'Generated audio exercise for user {user_id}')

            except RuntimeError as e:
                # TTS failed - send text-only
                logger.warning(f'TTS failed, posting text-only: {e}')
                embed = discord.Embed(
                    title='🔊 Audio Exercise',
                    description='(Audio unavailable)',
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name='Korean (spoiler)',
                    value=f'||{exercise["korean"]}||',
                    inline=False
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
            logger.exception(f'Error generating audio exercise: {e}')
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
        """Grade audio response and generate next exercise."""
        try:
            async with message.channel.typing():
                result = await gpt.grade_audio_response(
                    exercise['korean'],
                    exercise['english'],
                    student_answer
                )

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

            embed.add_field(name='Your Answer', value=student_answer, inline=False)
            embed.add_field(name='Korean', value=exercise['korean'], inline=False)
            embed.add_field(name='English', value=exercise['english'], inline=False)

            if result.get('feedback'):
                embed.add_field(name='Feedback', value=result['feedback'], inline=False)

            await message.channel.send(embed=embed)

            # Generate next exercise
            await self.generate_and_post_exercise(message, user_id)

        except Exception as e:
            logger.exception(f'Error grading audio response: {e}')
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
_handler = AudioHandler()


async def handle(message: discord.Message) -> None:
    """Handle messages in #audio channel."""
    await _handler.handle(message)
