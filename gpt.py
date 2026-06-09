"""AsyncOpenAI GPT-4o wrapper for Korean bot exercise generation and grading."""

import json
import re
from openai import AsyncOpenAI

from korean_config import logger, OPENAI_API_KEY

# Initialize AsyncOpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)



def _strip_markdown(text: str) -> str:
    """
    Strip markdown code fences before json.loads.

    Args:
        text: Raw text potentially containing markdown code fences

    Returns:
        Cleaned JSON text
    """
    return re.sub(
        r"^```json\s*|^```\s*|```$",
        "",
        text,
        flags=re.MULTILINE
    ).strip()


async def generate_vocab_list(raw_words: str) -> list[dict]:
    """
    Generate formatted vocabulary list from raw Korean words.

    System prompt: Korean language teacher, return raw JSON array only, no markdown.

    Args:
        raw_words: Raw Korean words/phrases separated by spaces or newlines

    Returns:
        List of vocab dicts with korean, romanization, english, part_of_speech,
        example_korean, example_english
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a Korean language teacher. Generate a B1-level vocabulary list '
                        'from the provided Korean words. Follow these translation rules:\n\n'
                        'VERBS:\n'
                        '- If transitive (takes a direct object): translate as "to do (something)" '
                        'where (something) is in parentheses only if the object is unspecified. '
                        'If the object is specified or implied (e.g. 공연 관람 - watching a performance), no parentheses.\n'
                        '- If intransitive (no direct object): translate as "to be something" '
                        '(e.g. 어색하다 - to be awkward).\n\n'
                        'GRAMMAR PATTERNS:\n'
                        '- Translate with brief explanation followed by "(grammar pattern)" in parentheses '
                        '(e.g. -고 나면 - after doing (grammar pattern)).\n\n'
                        'NOUNS:\n'
                        '- Translate with single concise English noun or noun phrase, no articles unless necessary.\n\n'
                        'ADVERBS AND PARTICLES:\n'
                        '- Translate with single concise English equivalent.\n\n'
                        'GENERAL RULES:\n'
                        '- One translation per term, choosing the most common/useful meaning\n'
                        '- If a term has a spelling error, correct it and translate the corrected version\n'
                        '- No slashes between multiple definitions\n'
                        '- Keep translations concise\n'
                        '- Bold the Korean term in output\n\n'
                        'Return a JSON array with objects containing: korean, romanization, english, '
                        'part_of_speech, example_korean, example_english. Return ONLY the JSON array, '
                        'no markdown or additional text.'
                    )
                },
                {
                    'role': 'user',
                    'content': f'Generate vocab list for these words:\n{raw_words}'
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)

        # Try to parse as array directly, or wrap in array
        try:
            vocab_list = json.loads(content)
            if isinstance(vocab_list, dict):
                vocab_list = vocab_list.get('vocab', [vocab_list])
        except json.JSONDecodeError:
            vocab_list = []

        return vocab_list if isinstance(vocab_list, list) else []

    except Exception as e:
        logger.exception(f'Error generating vocab list: {e}')
        raise RuntimeError(f'Failed to generate vocab list: {e}')


async def generate_translation_exercise(
    words: list[dict],
    direction: str
) -> dict:
    """
    Generate a translation exercise by selecting 3 words and creating one
    sentence per word.

    Direction: en_to_kr or kr_to_en

    Args:
        words: List of word dicts with korean, english, tags
        direction: Translation direction

    Returns:
        Dict with direction, prompt (source sentences), answer (translations), words_used, difficulty_note
    """
    try:
        import random
        direction_text = (
            'English to Korean'
            if direction == 'en_to_kr'
            else 'Korean to English'
        )

        # Randomly select up to 3 words from the provided list
        selected_words = random.sample(words, min(3, len(words)))
        
        # Format words with definitions
        words_with_defs = ', '.join(
            f"{w['korean']}: ({w.get('english', '')})" 
            for w in selected_words
        )

        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a Korean language teacher. For each provided word, generate a B1-level '
                        'sentence appropriate for beginner-intermediate learners. Create exactly one sentence per word in '
                        'the source language (based on the direction). IMPORTANT: Output sentences should contain ONLY the '
                        'sentences themselves, with NO word labels, definitions, or prefix text. For example, output just '
                        '"I want to visit my grandmother this weekend." not "visit: I want to visit...".'
                        'Return a JSON object with the following keys: '
                        'direction, prompt, answer, words_used (list), difficulty_note. The `prompt` should contain the '
                        'source-language sentences (one per line or numbered). The `answer` should contain the corresponding '
                        'translations in the target language (one per line or numbered in the same order). Provide '
                        'difficulty_note in English. Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Generate one {direction_text} translation sentence for each of these words. Definitions are provided for context only: '
                        f'{words_with_defs}. Output sentences must NOT include the word labels or definitions.'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error generating translation exercise: {e}')
        raise RuntimeError(f'Failed to generate translation exercise: {e}')


async def grade_translation(
    prompt: str,
    answer: str,
    student: str,
    direction: str
) -> dict:
    """
    Grade a translation response.

    Args:
        prompt: Original prompt
        answer: Correct answer
        student: Student's response
        direction: Translation direction (en_to_kr or kr_to_en)

    Returns:
        Dict with correct (bool), score (0-100), feedback, corrected (null if correct)
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a Korean language teacher grading translations. '
                        'Return JSON with: correct (bool), score (0-100), feedback (string), '
                        'corrected (null if correct, otherwise corrected version). '
                        'Provide all feedback and explanations in English. '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Grade this translation.\nPrompt: {prompt}\n'
                        f'Correct answer: {answer}\nStudent answer: {student}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error grading translation: {e}')
        raise RuntimeError(f'Failed to grade translation: {e}')


async def generate_audio_exercise(words: list[dict]) -> dict:
    """
    Generate an audio listening exercise with a single sentence.

    Args:
        words: List of word dicts

    Returns:
        Dict with korean, english, tts_text
    """
    try:
        import random
        selected_word = random.choice(words)
        
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a Korean language teacher. Generate a B1-level audio exercise with a single Korean sentence '
                        'appropriate for beginner-intermediate learners. Return JSON with: korean (the sentence), '
                        'english (translation), tts_text (the Korean sentence for text-to-speech). '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Generate an audio exercise using this word: '
                        f'{selected_word["korean"]} ({selected_word.get("english", "")})'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error generating audio exercise: {e}')
        raise RuntimeError(f'Failed to generate audio exercise: {e}')


async def grade_audio_response(
    korean: str,
    english: str,
    student: str
) -> dict:
    """
    Grade an audio listening response.

    Student may respond with meaning or romanization.

    Args:
        korean: Korean text that was played
        english: English translation
        student: Student's response

    Returns:
        Dict with correct (bool), score (0-100), feedback, corrected (null if correct)
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Grade an audio listening response. Student may answer with '
                        'English meaning or romanization. Return JSON with: correct (bool), '
                        'score (0-100), feedback, corrected (null if correct). '
                        'Provide all feedback in English. '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Korean: {korean}\nEnglish: {english}\n'
                        f'Student answered: {student}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error grading audio response: {e}')
        raise RuntimeError(f'Failed to grade audio response: {e}')


async def generate_dictation_exercise(words: list[dict]) -> dict:
    """
    Generate a dictation exercise with a single sentence.

    Args:
        words: List of word dicts

    Returns:
        Dict with korean, english, tts_text
    """
    try:
        import random
        selected_word = random.choice(words)
        
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Generate a B1-level dictation exercise with a single Korean sentence '
                        'appropriate for beginner-intermediate learners. '
                        'Return JSON with: korean (the sentence), english (translation), tts_text (the Korean sentence for dictation). '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Generate a dictation exercise using this word: '
                        f'{selected_word["korean"]} ({selected_word.get("english", "")})'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error generating dictation exercise: {e}')
        raise RuntimeError(f'Failed to generate dictation exercise: {e}')


async def grade_dictation(correct: str, student: str) -> dict:
    """
    Grade a dictation response.

    Strip punctuation before comparing. Character-by-character diff.

    Args:
        correct: Correct Korean text
        student: Student's transcription

    Returns:
        Dict with correct (bool), score (0-100), feedback, diff, corrected
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Grade a Korean dictation. '
                        'Return JSON with: correct (bool), score (0-100), feedback, diff, corrected. '
                        'Provide all feedback in English. '
                        'Return ONLY JSON, no markdown in JSON values.'
                    )
                },
                {
                    'role': 'user',
                    'content': f'Correct: {correct}\nStudent: {student}'
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error grading dictation: {e}')
        raise RuntimeError(f'Failed to grade dictation: {e}')


async def generate_cloze_exercise(words: list[dict]) -> dict:
    """
    Generate a cloze (fill-in-the-blank) exercise.

    4-6 sentence paragraph with 3-5 blanks numbered _1_, _2_, etc.

    Args:
        words: List of word dicts

    Returns:
        Dict with paragraph, blanks (list of dicts), full_paragraph, words_used
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Generate a B1-level cloze exercise appropriate for beginner-intermediate learners: '
                        '4-6 sentence Korean paragraph with 3-5 blanks numbered _1_, _2_, etc. '
                        'Return JSON with: paragraph (with blanks), '
                        'blanks (list of {position, korean, english}), full_paragraph (with words filled in), '
                        'words_used. Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Generate a cloze exercise using these words: '
                        f'{", ".join(w["korean"] for w in words[:5])}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error generating cloze exercise: {e}')
        raise RuntimeError(f'Failed to generate cloze exercise: {e}')


async def grade_cloze(blanks: list[dict], student_answers: str) -> dict:
    """
    Grade cloze responses.

    Parse answers in order, comma or newline separated.

    Args:
        blanks: List of blank dicts from exercise
        student_answers: Student's comma or newline separated answers

    Returns:
        Dict with results (list), score (0-100), feedback
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Grade cloze (fill-in-the-blank) responses. Parse answers in order. '
                        'Return JSON with: results (list of {position, correct (bool), student, answer}), '
                        'score (0-100), feedback. '
                        'Provide all feedback in English. '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Blanks: {json.dumps(blanks)}\nStudent answers: {student_answers}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error grading cloze: {e}')
        raise RuntimeError(f'Failed to grade cloze: {e}')


async def generate_reading_exercise(words: list[dict]) -> dict:
    """
    Generate a reading comprehension exercise.

    6-10 sentence Korean story with 3 English comprehension questions.

    Args:
        words: List of word dicts

    Returns:
        Dict with story_korean, story_english, questions (list), answers (list), words_used
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Generate a B1-level reading exercise appropriate for beginner-intermediate learners: '
                        '6-10 sentence Korean story with 3 English comprehension questions. '
                        'Return JSON with: story_korean, '
                        'story_english (translation), questions (list), answers (list), words_used. '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Generate a reading story using these words: '
                        f'{", ".join(w["korean"] for w in words[:5])}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error generating reading exercise: {e}')
        raise RuntimeError(f'Failed to generate reading exercise: {e}')


async def grade_reading(
    questions: list[str],
    answers: list[str],
    student: str
) -> dict:
    """
    Grade reading comprehension responses.

    GPT parses numbered or prose answers from student message.

    Args:
        questions: List of comprehension questions
        answers: List of correct answers
        student: Student's full response

    Returns:
        Dict with results (list), score (0-100), overall_feedback
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Grade reading comprehension. Parse student answers (numbered or prose). '
                        'Return JSON with: results (list of {question, correct (bool), feedback}), '
                        'score (0-100), overall_feedback. '
                        'Provide all feedback in English. '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Questions: {json.dumps(questions)}\nCorrect answers: {json.dumps(answers)}\n'
                        f'Student response: {student}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error grading reading: {e}')
        raise RuntimeError(f'Failed to grade reading: {e}')


async def generate_write_prompt(words: list[dict]) -> dict:
    """
    Generate a free writing prompt.

    Args:
        words: List of word dicts (target vocabulary)

    Returns:
        Dict with prompt, target_words (list), english_hint
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Generate a B1-level Korean writing prompt appropriate for beginner-intermediate learners. '
                        'Return JSON with: '
                        'prompt (scenario for student to write about), '
                        'target_words (list of Korean words to use), '
                        'english_hint (context hint in English). '
                        'Provide english_hint in English. '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Generate a writing prompt using these target words: '
                        f'{", ".join(w["korean"] for w in words[:5])}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error generating write prompt: {e}')
        raise RuntimeError(f'Failed to generate write prompt: {e}')


async def grade_writing(
    prompt: str,
    target_words: list[str],
    student: str
) -> dict:
    """
    Grade free writing response.

    Max 5 corrections.

    Args:
        prompt: Original prompt
        target_words: Target words list
        student: Student's written response

    Returns:
        Dict with score, target_words_used, target_words_missed, corrections (max 5),
        overall_feedback, improved_version
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Grade Korean writing. Return JSON with: '
                        'score (0-100), target_words_used (list), target_words_missed (list), '
                        'corrections (list of max 5: {original, corrected, explanation}), '
                        'overall_feedback, improved_version. '
                        'Provide all explanations and feedback in English. '
                        'Return ONLY JSON, no markdown in values.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Prompt: {prompt}\nTarget words: {", ".join(target_words)}\n'
                        f'Student writing: {student}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error grading writing: {e}')
        raise RuntimeError(f'Failed to grade writing: {e}')


async def generate_build_exercise(words: list[dict]) -> dict:
    """
    Generate a sentence building exercise.

    Pick 3-5 words and provide example sentence.

    Args:
        words: List of word dicts

    Returns:
        Dict with given_words (list of {korean, english}), difficulty_note, example_answer
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Generate a B1-level sentence building exercise appropriate for beginner-intermediate learners. '
                        'Pick 3-5 words and create an example sentence using them. Return JSON with: '
                        'given_words (list of {korean, english}), difficulty_note, example_answer. '
                        'Provide difficulty_note in English. '
                        'Return ONLY JSON, no markdown.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Generate a sentence building exercise using words from: '
                        f'{", ".join(w["korean"] for w in words[:5])}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error generating build exercise: {e}')
        raise RuntimeError(f'Failed to generate build exercise: {e}')


async def grade_build(
    given_words: list[dict],
    example_answer: str,
    student: str
) -> dict:
    """
    Grade sentence building response.

    Args:
        given_words: List of words provided in exercise
        example_answer: Example sentence from exercise
        student: Student's constructed sentence

    Returns:
        Dict with correct (bool), score (0-100), all_words_used (bool),
        grammar_correct (bool), feedback, corrected (null if correct), example_answer
    """
    try:
        response = await client.chat.completions.create(
            model='gpt-5.4',
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Grade a Korean sentence built from given words. Return JSON with: '
                        'correct (bool), score (0-100), all_words_used (bool), grammar_correct (bool), '
                        'feedback, corrected (null if correct), example_answer (always include). '
                        'Provide all feedback in English. '
                        'Return ONLY JSON, no markdown in values.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Given words: {json.dumps(given_words)}\n'
                        f'Example answer: {example_answer}\n'
                        f'Student sentence: {student}'
                    )
                }
            ]
        )

        content = response.choices[0].message.content
        content = _strip_markdown(content)
        return json.loads(content)

    except Exception as e:
        logger.exception(f'Error grading build: {e}')
        raise RuntimeError(f'Failed to grade build: {e}')


async def transcribe_audio(audio_bytes: bytes, filename: str = 'audio.mp3') -> str:
    """
    Transcribe audio to text using OpenAI Whisper API.

    Args:
        audio_bytes: Raw audio file bytes
        filename: Filename for the audio (including extension)

    Returns:
        Transcribed text

    Raises:
        RuntimeError: If transcription fails
    """
    try:
        from io import BytesIO
        
        # Create a file-like object from bytes
        audio_file = BytesIO(audio_bytes)
        audio_file.name = filename
        
        response = await client.audio.transcriptions.create(
            model='whisper-1',
            file=audio_file,
            language='ko'  # Korean language
        )
        
        return response.text.strip()
    
    except Exception as e:
        logger.exception(f'Error transcribing audio: {e}')
        raise RuntimeError(f'Failed to transcribe audio: {e}')
