import oai
import dapi
import gcloud
from utils import download_from_url


SERVER = "Chil's server"

VOCAB_CHANNEL = "vocab"
CHANNEL = "vocab"

PREFACE = "Use the following vocab terms and make 3 sentences for each one. Format it using the example below:\
\
냉동실\
Freezer\
냉동실에 얼린 과일로 스무디를 만들었다.\
I made a smoothie with frozen fruit from the freezer.\
\
Vocabulary Terms:\
"

vocab = ""

def is_english(sentence):
    # Define a set of common English characters
    english_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    # Check if the sentence contains any English characters
    for char in sentence:
        if char in english_chars:
            return True
        
    return False

async def on_message(bot, message):
    global path
    ctx = await bot.get_context(message)
    channel = str(message.channel)
    server = message.guild.name
    text = message.content
    
    if not (server == SERVER and channel == CHANNEL):
        return
        
    if text != "read":
        set_vocab(text)
        await dapi.reply(message, "Vocab Set!")
    else:
        conversation_messages = []
        oai.append_user_message(conversation_messages, PREFACE + vocab)
        response = oai.call_gpt(conversation_messages)

        await dapi.reply(message, response)

        sentences = response.split("\n")
        for sentence in sentences:
            path = await gcloud.tts(sentence, ("ko-KR", "ko-KR-Wavenet-C") if not is_english(sentence) else ('en-US', 'en-US-Casual-K'))
            await dapi.speak(ctx, bot, path)

def set_vocab(text):
    global vocab
    vocab = text