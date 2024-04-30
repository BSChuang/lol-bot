import oai
import dapi
from utils import download_from_url

CHANNEL = "conversation"
SERVER = "Chil's server"
PREFACE = "You are my korean tutor. We are having a conversation to help practice my Korean. Please speak in Korean except when I ask a question in English. End with an English translation of what you have said."

conversation_messages = []
path = ''

async def on_message(bot, message):
    global path
    ctx = await bot.get_context(message)
    channel = str(message.channel)
    server = message.guild.name
    
    if not (server == SERVER and channel == CHANNEL):
        return
    
    text = message.content
    if text == 'r':
        await dapi.speak(ctx, bot, path)
        return
    
    if len(message.attachments) != 0:
        recording_url = message.attachments[0].url
        download_from_url(recording_url, 'temp.ogg')
        transcription = oai.whisper('temp.ogg', 'ko')
        text = transcription
        await dapi.reply(message, f'Transcription: {text}')

    oai.append_user_message(conversation_messages, text)
    
    response = oai.call_gpt(conversation_messages[-20:], PREFACE, False, True)
    oai.append_assistant_message(conversation_messages, response)

    await dapi.reply(message, response)
    path = await oai.tts(response)
    await dapi.speak(ctx, bot, path)

