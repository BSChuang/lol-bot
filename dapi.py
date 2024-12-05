import discord
from time import sleep
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

ffmpeg_path = config['discord']['ffmpeg_path'] if 'ffmpeg_path' in config['discord'] else None 

async def reply(message, text):
    if type(text) == str:
        for i in range(0, len(text), 1999):
            await message.channel.send(text[i:i+1999])
    else:
        await message.channel.send(file=text)

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

    # Stop any currently playing audio
    if voice_client.is_playing():
        voice_client.stop()

    if ffmpeg_path:
        voice_client.play(discord.FFmpegPCMAudio(source=path, executable=ffmpeg_path))
    else:
        voice_client.play(discord.FFmpegPCMAudio(source=path))

    return None

async def disconnect(ctx, bot):
    # Check if the bot is connected to a voice channel
    if bot.voice_clients:
        # Find the voice client associated with the server where the command is invoked
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client:
            await voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
        else:
            await ctx.send("The bot is not connected to any voice channel in this server.")
    else:
        await ctx.send("The bot is not connected to any voice channel.")

async def command(message, input_cmd, cmd, reaction, fn):
    if cmd is not None and input_cmd != f'!{cmd}':
        return False

    await react(message, reaction)
    output = await fn()

    if output is None:
        return True
    
    while type(output) == str and len(output) > 1900:
        await reply(message, output[:1900])
        output = output[1900:]
    await reply(message, output)

    return True