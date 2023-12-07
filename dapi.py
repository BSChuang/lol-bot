import discord
from time import sleep
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

ffmpeg_path = config['discord']['ffmpeg_path']

async def reply(message, text):
    await message.channel.send(text)

async def react(message, reaction):
    await message.add_reaction(reaction)

async def speak(ctx, bot, path):
    if ctx.author.voice is None:
        return
    voice_channel = ctx.author.voice.channel
    voice_client = None

    if bot.voice_clients != []:
        if bot.voice_clients[0].channel != voice_channel:
            await bot.voice_clients[0].disconnect()
            voice_client = await voice_channel.connect(self_deaf=True)
            sleep(0.5)
        else:
            voice_client = bot.voice_clients[0]
    else:
        voice_client = await voice_channel.connect(self_deaf=True)
        sleep(0.5)

    voice_client.play(discord.FFmpegPCMAudio(source=path, executable=ffmpeg_path))

    return

async def leave(bot):
    if bot.voice_clients != []:
        await bot.voice_clients[0].disconnect()

async def command(message, input_cmd, cmd, reaction, fn):
    if cmd is not None and input_cmd != f'!{cmd}':
        return False

    await react(message, reaction)
    output = await fn()

    if output is None:
        return True
    
    while len(output) > 1900:
        await reply(message, output)
        output = output[1900:]
    await reply(message, output)

    return True