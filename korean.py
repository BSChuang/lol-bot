import oai
import dapi
CHANNEL = "conversation"
SERVER = "Chil's server"
PREFACE = "You are my korean tutor. We are having a conversation to help practice my Korean. Please speak in Korean if I speak in Korean and English if I speak in English."

conversation_messages = []
path = ''

async def on_message(bot, message):
    global path
    ctx = await bot.get_context(message)
    channel = message.channel
    server = message.guild.name
    if server != SERVER and channel != CHANNEL:
        return
    
    text = message.content
    if text == 'r':
        await dapi.speak(ctx, bot, path)
        return

    print(text, type(text))
    oai.append_user_message(conversation_messages, text)
    print(conversation_messages)
    
    response = oai.call_gpt(conversation_messages[-20:], PREFACE, False, True)
    oai.append_assistant_message(conversation_messages, response)

    await dapi.reply(message, response)

    path = await oai.tts(response)
    await dapi.speak(ctx, bot, path)

