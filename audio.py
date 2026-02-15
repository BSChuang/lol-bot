"""OpenAI TTS wrapper for Korean bot audio exercises."""

from openai import AsyncOpenAI

from korean_config import logger, OPENAI_API_KEY

# Initialize AsyncOpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def generate_tts(text: str, voice: str = 'nova', korean_accent: bool = False) -> bytes:
    """
    Generate TTS audio from text using OpenAI.

    Uses the gpt-4o-mini-tts model for faster generation.

    Args:
        text: Text to convert to speech
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer). Default is 'nova' which works well for Korean.
        korean_accent: If True, prepends instruction to speak with Korean accent/pronunciation

    Returns:
        Raw MP3 audio bytes

    Raises:
        RuntimeError: If TTS generation fails
    """
    try:
        # Prepend accent instruction to text if requested
        tts_text = f"[Speak very slowly with a Korean accent] {text}" if korean_accent else text

        response = await client.audio.speech.create(
            model='gpt-4o-mini-tts',
            voice=voice,
            input=tts_text
        )

        # response.content is the audio bytes
        return response.content

    except Exception as e:
        logger.exception(f'Error generating TTS for text "{text[:50]}...": {e}')
        raise RuntimeError(f'Failed to generate audio: {e}')
