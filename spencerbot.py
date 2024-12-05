from dapi import command, disconnect, speak
import random
import configparser
from datetime import datetime, timedelta
from weight_helper import weight
import discord
from discord.ext import commands
import korean
import service.VocabService
import service.YoutubeService
import gcloud

config = configparser.ConfigParser()
config.read("config.ini")

intents = discord.Intents.all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)

def td_format(td_object):
    seconds = int(td_object.total_seconds())
    periods = [
        ('year',        60*60*24*365),
        ('month',       60*60*24*30),
        ('day',         60*60*24),
        ('hour',        60*60),
        ('minute',      60),
        ('second',      1)
    ]

    strings=[]
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value , seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)

voices = {
    374970992419799042: ("ko-KR", "ko-KR-Neural2-C"), # Ben
    # 276216359749419009 # Suchir
    # 267891995157069826 # Spencer
    202579063217455104: ("ja-JP", "ja-JP-Neural2-D") # Gnole
    # 283436282082885632 # Alex
    # 369923734447849477 # Harrison
    # 762044954930446428 # Mistry
    # 660172839655178250 # Paul
    # 815086417612111922 # Dylan
    # 711029919546736651 # Deverell GOAT
    # 304353367294214155 # Deverell Economist
}
    
def read(filename):
    with open(filename, 'r') as file:
        return file.read()
    
def write(filename, text):
    with open(filename, 'w') as file:
        file.write(text)
    
def read_dominos():
    return float(read('dominos.txt'))

def write_dominos():
    write('dominos.txt', str(datetime.timestamp(datetime.now())))

async def dominos():
    last_dominos_time = read_dominos()
    secs = (datetime.timestamp(datetime.now()) - last_dominos_time)
    result = td_format(timedelta(seconds = secs))
    return f"Last Dominos was {result} ago"

async def relapse():
    write_dominos()
    
    emote = random.choice(['<:sadspencer:976908811904385104>', '<:spencer:968679218550550569>', '<:spencer2:972178114941714492>',\
                          '<:spencerangel:996846084712312853>', '<:spencerbaby:1017119767359926282>', '<:spencerflirt:1046478467191013447>', '<:supersadspencer:1002683850964611153>'])
    return emote


messages = []
preface = ""

user_speak = set()
@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)
    bot_id = '<@1064717164579393577>'
    user_id = message.author.id

    text = message.content.replace(bot_id, '').strip()

    if message.author == bot.user:
        return

    if ' ' in text:
        input_cmd, input_text = text.split(' ', 1)
    else:
        input_cmd, input_text = text, None

    async def send_command(cmd, reaction, fn):
        return await command(message, input_cmd, cmd, reaction, fn)
    
    async def cmd_toggle_speak():
        if user_id in user_speak:
            user_speak.remove(user_id)
            if len(user_speak) == 0:
                await leave(bot)
            return "TTS deactivated!"
        else:
            user_speak.add(user_id)
            return "TTS activated!"

    async def cmd_speak():
        voice = voices[message.author.id] if message.author.id in voices else ('en-US', 'en-US-Casual-K')
        if message.author == client.user or not message.content.startswith(bot_id):
            path = await gcloud.tts(text, voice)
            return await speak(ctx, bot, path)
    
    async def cmd_leave():
        return await disconnect(ctx, bot)
    
    async def cmd_weight():
        return weight(input_text if input_text != '' else None, message.author.id)

    async def cmd_youtube():
        file = await service.YoutubeService.download_youtube_audio(input_text)
        return await speak(ctx, bot, file)
    
    if user_id in user_speak:
        await cmd_speak()

    await korean.on_message(bot, message)
    # await receipts.on_message(bot, message)
    await service.VocabService.on_message(bot, message)
        
    if not message.content.startswith(bot_id):
        return
    
    command_list = [
        await send_command('dominos', "🍕", dominos),
        await send_command('relapse', "😭", relapse),
        await send_command('lb', "🏋️", cmd_weight),
        await send_command('st', "🔊", cmd_toggle_speak),
        await send_command('l', "🔊", cmd_leave),
        await send_command('stop', "🔊", cmd_leave),
        await send_command('play', '🔊', cmd_youtube)
    ]

    if not any(command_list):
        async def gpt_chat():
            return await chat(text)
        await command(message, text, None, "🤔", gpt_chat)


if __name__ == "__main__":
    bot.run(config['discord']['token'])