import requests
import random
import json
import re
import time
import configparser
from datetime import datetime, timedelta
import threading
import asyncio


from bs4 import BeautifulSoup
import hikari

config = configparser.ConfigParser()
config.read("config.ini")

bot = hikari.GatewayBot(token=config['discord']['token'])

items_json = None
with open("items.json") as file:
    file = open("items.json")
    items_json = json.load(file)
    file.close()

items_dict = {}
for d in items_json:
    items_dict[d['id']] = d['name']

def tier_to_roman(tier):
    tier_to_roman = {
        '1': 'I',
        '2': 'II',
        '3': 'III',
        '4': 'IV'
    }
    return tier_to_roman[tier]

def place(num):
    suffix = {
        1: 'st',
        2: 'nd',
        3: 'rd',
    }
    if num in suffix:
        return suffix[num]
    else:
        return 'th'
    
def item_id_to_list(list):
    if 0 in list:
        list = list[:list.index(0)]
    items = [items_dict[x] for x in list]
    return ', '.join(items)

def web_scrape():
    try:
        url = "https://www.op.gg/summoners/na/The%20NMEs%20Support"
        source = requests.get(url, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).text

        soup = BeautifulSoup(source, "html.parser")
        rank_div = soup.find("div", {"class": "css-1v663t e1x14w4w1"})
        tier = rank_div.find("div", {"class": "tier"}).text
        lp = rank_div.find("div", {"class": "lp"}).text

        champ_div = soup.find_all("div", {"class": "champion-box"})
        percentage = "NaN"
        count = "NaN"
        for div in champ_div:
            if div.find("a", {"href": "/champions/sion"}) is not None:
                percentage = div.find("div", {"class": {"css-b0uosc e1g7spwk0"}}).text
                count = div.find("div", {"class": {"count"}}).text.split()[0]

        return f"Bencer is currently {tier[:-2]} {tier_to_roman(tier[-1])}, {lp} with a Sion winrate of {percentage} over {count} games"
    except Exception as e:
        return e
    
def get_game_json():
    url = "https://op.gg/api/v1.0/internal/bypass/games/na/summoners/mGQycLPH483CDFWmBqEVRPFCBurCtpQOfLPlhYd3mzKsR6Q?&limit=20&hl=en_US&game_type=total"
    text = requests.get(url, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).text
    source = json.loads(text)
    return source

def opapi():
    source = get_game_json()

    game_list = source['data']

    my_player = None
    my_game = None
    for game in game_list:
        if game['queue_info']['game_type'] == 'SOLORANKED' and game['myData']['champion_id'] == 14:
            my_game = game
            my_player = game['myData']
            break
            
    if my_player is None:
        return "No solo/duo Sion found in past 20 games"
    
    start_time_str = my_game['created_at']
    #duration = my_game['game_length_second']
    end_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S+09:00") - timedelta(hours=14)# + timedelta(seconds=duration)

    # Return OP Score, KDA, Damage, Wards, CS, Items
    stats = my_player['stats']
    return f"```Last Sion game @ {end_time.strftime('%m/%d/%Y, %H:%M:%S')} EST:\nResult: {stats['result']}\nOP Score: {str(stats['op_score_rank'])}{place(stats['op_score_rank'])}\
        \nKDA: {stats['kill']}/{stats['death']}/{stats['assist']}\
        \nDamage Done/Taken/Mitigated: {stats['total_damage_dealt_to_champions']}/{stats['total_damage_taken']}/{stats['damage_self_mitigated']}\nTotal Heal: {stats['total_heal']}\
        \nWard Placed: {stats['ward_place']}\nMinion CS: {stats['minion_kill']}\nItems: {item_id_to_list(my_player['items'])}```"
    

def refresh():
    try:
        url = "https://op.gg/api/v1.0/internal/bypass/summoners/na/mGQycLPH483CDFWmBqEVRPFCBurCtpQOfLPlhYd3mzKsR6Q/renewal"
        res = requests.post(url, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).text
        print("Refreshed")
        return res
    except:
        print("Can't refresh")


def fact():
    animal_list = ["bird", "cat", "dog", "fox", "kangaroo", "koala", "panda", "raccoon", "red_panda"]
    animal = random.choice(animal_list)
    try:
        r = requests.get("https://some-random-api.ml/animal/" + animal)
        fact = json.loads(r.text)['fact']

        compiled = re.compile(animal, re.IGNORECASE)
        res = compiled.sub("Spencer", fact)
        return res
    except Exception as e:
        return e
    
def read_dominos():
    with open('dominos.txt', 'r') as file:
        return float(file.read())


def write_dominos():
    with open('dominos.txt', 'w') as file:
        file.write(str(datetime.timestamp(datetime.now())))

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

async def dominos(event):
    last_dominos_time = read_dominos()
    secs = (datetime.timestamp(datetime.now()) - last_dominos_time)
    result = td_format(timedelta(seconds = secs))
    await event.message.respond(f"Last Dominos was {result} ago")

async def relapse(event):
    write_dominos()
    
    emote = random.choice(['sadspencer', 'sleepyspencer', 'spencer', 'spencer2', 'spencerangel', 'spencerbaby', 'spencerflirt', 'supersadspencer'])
    await event.message.respond(f":{emote}:")


latest_event = None

@bot.listen()
async def ping(event: hikari.GuildMessageCreateEvent) -> None:
    global latest_event

    # Do not respond to bots nor webhooks pinging us, only user accounts
    if not event.is_human:
        return

    me = bot.get_me()

    if me.id in event.message.user_mentions_ids:
        if event.message.content == '!dominos':
            dominos(event)
        elif event.message.content == '!relapse':
            relapse(event)
        else:
            latest_event = event
            await event.message.respond(fact())
            refresh()
            time.sleep(3)
            await event.message.respond(web_scrape())
            await event.message.respond(opapi())

async def check_for_new_game():
    global latest_event
    frequency = 180
    while True:
        await asyncio.sleep(frequency)
        
        if latest_event is None:
            print("Ping the bot first")
            continue

        try:
            refresh()
            await asyncio.sleep(3)

            source = get_game_json()

            last_game = source['data'][0]

            start_time_str = last_game['created_at']
            #duration = last_game['game_length_second']
            end_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S+09:00") - timedelta(hours=14)# + timedelta(seconds=duration)

            if (datetime.now() - end_time).seconds < frequency * 1.5 and last_game['queue_info']['game_type'] == 'SOLORANKED' and last_game['myData']['champion_id'] == 14:
                await latest_event.message.respond( f'🚨🚨🚨 NEW SION GAME 🚨🚨🚨')

                await latest_event.message.respond(web_scrape())
                await latest_event.message.respond(opapi())
            else:
                print(f"No new Sion game at @ {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} EST")
        except Exception as e:
            print(e)


if __name__ == "__main__":
    print(datetime.now())
    asyncio.get_event_loop().create_task(check_for_new_game())
    bot.run()