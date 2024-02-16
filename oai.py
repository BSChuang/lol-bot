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
        voice="nova",
        input=text
    )

    response.stream_to_file('./speech.mp3')

    return './speech.mp3'

def vision(image):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "How many bottles of wine are displayed here?"},
                {
                "type": "image_url",
                "image_url": {
                    "url": "https://cdn.discordapp.com/attachments/958383842463477770/1184922173064888350/IMG_6491.jpg?ex=658dbbc4&is=657b46c4&hm=e823ed707143b8142f5ad14e9de69a0c6a94f1b33c10d74bc4181eff31db271e&",
                    "detail": "high"
                },
                },
            ],
            }
        ],
        max_tokens=1000,
        )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    print(vision(''))