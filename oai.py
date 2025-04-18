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
        voice="alloy",
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

def call_gpt(messages, preface = None):
    system_preface = [{'role': 'system', 'content': preface}] if preface else []
    completion = client.chat.completions.create(
            model="gpt-4o",
            messages= system_preface + messages
        )

    answer = completion.choices[0].message.content.strip()
    return answer

def call_gpt_single(text):
    return call_gpt([{'role': 'user', 'content': text}])
    
def append_user_message(message, text):
    return message.append({'role': 'user', 'content': text})

def append_assistant_message(message, text):
    return message.append({'role': 'assistant', 'content': text})

def whisper(audio_path, language):
    audio_file= open(audio_path, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language=language
    )
    return transcription.text
    

def dalle(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response.data[0].url


if __name__ == "__main__":
    print(vision(''))