"""Vocab generation cog for Korean bot - #vocab channel (stateless)."""

import discord

from korean_config import logger
import gpt


async def handle(message: discord.Message) -> None:
    """
    Handle messages in #vocab channel.

    Stateless - no Anki DB interaction, no state management.
    Just generate vocab lists from raw input.
    """
    if message.author.bot:
        return

    try:
        async with message.channel.typing():
            vocab_list = await gpt.generate_vocab_list(message.content)

        if not vocab_list:
            await message.channel.send(
                embed=discord.Embed(
                    title='❌ No Results',
                    description='Could not generate vocab list. Try again with different words.',
                    color=discord.Color.red()
                )
            )
            return

        # Paginate at 10 words per embed
        for i in range(0, len(vocab_list), 10):
            chunk = vocab_list[i:i+10]
            embed = discord.Embed(
                title=f'📚 Vocabulary List ({i+1}-{i+len(chunk)})',
                color=discord.Color.blue()
            )

            for word in chunk:
                name = (
                    f"{word.get('korean', '?')} "
                    f"· {word.get('part_of_speech', 'word')}"
                )
                value = (
                    f"{word.get('english', '?')}\n"
                    f"예: {word.get('example_korean', '?')}\n"
                    f"→ {word.get('example_english', '?')}"
                )
                embed.add_field(name=name, value=value, inline=False)

            embed.set_footer(
                text=f'{len(vocab_list)} words generated · '
                'Add them to an Anki deck to use in practice channels'
            )

            await message.channel.send(embed=embed)

        logger.info(f'Generated vocab list with {len(vocab_list)} words for user {message.author.id}')

    except Exception as e:
        logger.exception(f'Error generating vocab list: {e}')
        await message.channel.send(
            embed=discord.Embed(
                title='❌ Error',
                description='Could not generate vocab list. Check the bot logs.',
                color=discord.Color.red()
            )
        )
