import openai
from openai import OpenAI
import configparser
from pathlib import Path
from time import sleep

config = configparser.ConfigParser()
config.read("config.ini")

client = OpenAI(api_key=config['discord']['openai_key'])

async def tts(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )

    response.stream_to_file('./speech.mp3')

    return './speech.mp3'

if __name__ == "__main__":
    tts('hello')