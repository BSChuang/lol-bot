import requests
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

TOKEN = config['discord']['calorie_token']

def get_calories(query):
    res = requests.get(f'https://api.calorieninjas.com/v1/nutrition?query={query}', headers={
        'X-Api-Key': TOKEN
    })

    if res.status_code == 200:
        items = res.json()['items']
        return items
    else:
        raise Exception('Error accessing calories API')


if __name__ == "__main__":
    print(get_calories('1 serving of tonkatsu and rice'))