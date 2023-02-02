import requests
import random
import json
import re
import time
import configparser

from bs4 import BeautifulSoup
import hikari

config = configparser.ConfigParser()
config.read("config.ini")

tier_to_roman = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV'
}

def place(num):
    place = {
        '1': 'st',
        '2': 'nd',
        '3': 'rd',
    }
    if str(num) in place:
        return place[num]
    else:
        return 'th'

items_json = None
with open("items.json") as file:
    file = open("items.json")
    items_json = json.load(file)
    file.close()

items_dict = {}
for d in items_json:
    items_dict[d['id']] = d['name']

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

        return f"Bencer currently is {tier[:-2]} {tier_to_roman[tier[-1]]}, {lp} with a Sion winrate of {percentage} over {count} games"
    except Exception as e:
        return e

def item_id_to_list(list):
    miss = list.index(0)
    if miss != -1:
        list = list[:miss]
    items = [items_dict[x] for x in list]
    return ', '.join(items)

def opapi():
    url = "https://op.gg/api/v1.0/internal/bypass/games/na/summoners/mGQycLPH483CDFWmBqEVRPFCBurCtpQOfLPlhYd3mzKsR6Q?&limit=20&hl=en_US&game_type=total"
    text = requests.get(url, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).text
    source = json.loads(text)

    game_list = source['data']

    my_player = None
    for game in game_list:
        if game['queue_info']['game_type'] == 'SOLORANKED' and game['myData']['champion_id'] == 14:
            my_player = game['myData']
            break

            
    if my_player is None:
        return "No solo/duo Sion found in past 20 games"

    # Return OP Score, KDA, Damage, Wards, CS, Items
    stats = my_player['stats']
    return f"```Latest game:\nResult: {stats['result']}\nOP Score: {stats['op_score_rank']}{place(stats['op_score_rank'])}\nKDA: {stats['kill']}/{stats['death']}/{stats['assist']}\
        \nDamage Done/Taken: {stats['total_damage_dealt_to_champions']}/{stats['total_damage_taken']}\nWard Placed: {stats['ward_place']}\
        \nMinion CS: {stats['minion_kill']}\nItems: {item_id_to_list(my_player['items'])}```"
    

def refresh():
    try:
        url = "https://op.gg/api/v1.0/internal/bypass/summoners/na/mGQycLPH483CDFWmBqEVRPFCBurCtpQOfLPlhYd3mzKsR6Q/renewal"
        res = requests.post(url, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}).text
        print("Refreshed")
    except:
        print("Can't refresh")
    return res



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
        return res


bot = hikari.GatewayBot(token=config['discord']['token'])

@bot.listen()
async def ping(event: hikari.GuildMessageCreateEvent) -> None:
    """If a non-bot user mentions your bot, respond with 'Pong!'."""

    # Do not respond to bots nor webhooks pinging us, only user accounts
    if not event.is_human:
        return

    me = bot.get_me()

    if me.id in event.message.user_mentions_ids:
        await event.message.respond(fact())
        refresh()
        time.sleep(3)
        await event.message.respond(web_scrape())
        await event.message.respond(opapi())

if True:
    bot.run()