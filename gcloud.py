import os
import configparser

config = configparser.ConfigParser()
config.read("config.ini")


credential_path = config['discord']['gcloud_cred_path']
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

async def tts(text, voice):
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code=voice[0],
        name=voice[1],
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with open("speech.mp3", "wb") as out:
        out.write(response.audio_content)

    return "speech.mp3"

if __name__ == "__main__":
    tts("Hello")