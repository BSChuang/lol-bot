import os
import discord

from datetime import datetime
from utils import download_from_url

import dapi
from service.CVService import scan
from service.NextcloudService import Nextcloud 
from service.DocIntelligenceService import DocIntelligenceService
from service.SQLService import SQLService
from service.SQLAgentService import Agent

RECEIPTS_CHANNEL = "receipts"
QUESTIONS_CHANNEL = "questions"
SERVER = "Chil's server"

nextcloud = Nextcloud()
docIntelligenceService = DocIntelligenceService()
sqlService = SQLService()
agent = Agent()

def get_now():
    # Get the current date and time
    now = datetime.now()

    # Format it as YYYY_MM_DD_HHMMSS
    formatted_date = now.strftime('%Y_%m_%d_%H%M%S')

    return formatted_date

async def on_message(bot, message):
    ctx = await bot.get_context(message)
    channel = str(message.channel)
    server = message.guild.name

    if not (server == SERVER and (channel == RECEIPTS_CHANNEL or channel == QUESTIONS_CHANNEL)):
        return
    
    router = {
        RECEIPTS_CHANNEL: receipts,
        QUESTIONS_CHANNEL: questions,
    }

    await router[channel](message)

async def receipts(message):
    if len(message.attachments) == 0:
        return "No receipt found!"
    
    completion = ''
    try:
        split_tup = os.path.splitext(message.attachments[0].filename)
        file_extension = split_tup[1]
        new_file_path = f'./temp/temp{file_extension}'
        url = message.attachments[0].url
        download_from_url(url, new_file_path)

        completion += '\nDownload from Discord complete...'

        scanned_path = "./temp/scanned_temp.png"
        scan(new_file_path, scanned_path)

        file = discord.File(scanned_path) 
        await dapi.reply(message, file)

        nextcloud.upload_file(scanned_path, f"/Receipts/{get_now()}.png")
        completion += '\nNextcloud upload complete...'

        receipt, items = docIntelligenceService.image_to_df(scanned_path)
        completion += '\nDocument Intelligence scan complete...'

        sqlService.insert_all(receipt, items)
        completion += '\nSQL Insertion complete...'

        completion += "\nUpload complete!"
    except Exception as e:
        print(e)
        completion += "\nUpload failed!"
    await dapi.reply(message, completion)
    


async def questions(message):
    response = agent.ask_question(message.content)
    await dapi.reply(message, response)
