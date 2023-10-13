'''
    Two functions:
    !c [number]: adds calories to the calories of the day
        calories are saved to a csv with two columns: timestamp and calories
    !c: sums the calories eaten today
    !lb [number]: records weight at time of call
        weight is saved to csv with two columns: timestamp and weight
    !lb: prints graph of weight
'''

import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import hikari
import math
import os
import json

def is_valid(num, min_range, max_range):
    try:
        float_num = float(num)
        return math.isfinite(float_num) and not math.isnan(float_num) and min_range < float_num < max_range
    except:
        return False


def calories(body: str):
    if not os.path.isfile('./calories.csv'):
        calories_df = pd.DataFrame(columns=['timestamp', 'calories'])
        calories_df.to_csv('./calories.csv', index=False)
    if not os.path.isfile('./foods.json'):
        save_json({}, 'foods.json')

    try:
        if body != '':
            if body.isdigit():
                calorie = int(body)
            else:
                count, food = body.split(' ', 1)
                count = int(count)
                foods = load_json('foods.json')
                if food in foods:
                    calorie = count * foods[food]
                else:
                    return f'Food not found!'
        else:
            calorie = None

        print(calorie)


        df = pd.read_csv('./calories.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if calorie is not None and is_valid(calorie, 0, 5000):
            df.loc[len(df)] = [pd.Timestamp.now(), int(calorie)]
        
        df.to_csv('./calories.csv', index=False)
        
        day_calories = df.groupby(df['timestamp'].dt.date)['calories'].sum().tail(1).item()
        return f'Total calories for the day: {day_calories}'
    except Exception as e:
        print(e)
        return f"Something went wrong: {e}"
    
def remove_latest():
    try:
        df = pd.read_csv('./calories.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.drop(df.tail(1).index, inplace=True)
        df.to_csv('./calories.csv', index=False)
        
        day_calories = df.groupby(df['timestamp'].dt.date)['calories'].sum().tail(1).item()
        return f'Total calories for the day: {day_calories}'
    except Exception as e:
        print(e)
        return f"Something went wrong: {e}"
    
def load_json(file_str) -> dict:
    with open(file_str) as json_file:
        dictionary = json.load(json_file)
        return dictionary

def save_json(dictionary, file_str):
    with open(file_str, 'w') as json_file:
        json.dump(dictionary, json_file)
    
def set_food(body: str):
    if not os.path.isfile('./foods.json'):
        save_json({}, 'foods.json')

    calorie, food = body.split(' ', 1)
    foods = load_json('foods.json')
    foods[food] = int(calorie)
    save_json(foods, 'foods.json')

    return f'Set {food} to {calorie} calories'
    
def weight(num, user_id):
    if not os.path.isfile(f'./weight_graphs/weight_{user_id}.csv'):
        calories_df = pd.DataFrame(columns=['timestamp', 'weight'])
        calories_df.to_csv(f'./weight_graphs/weight_{user_id}.csv', index=False)

    try:
        df = pd.read_csv(f'./weight_graphs/weight_{user_id}.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if num is not None and is_valid(num, 0, 300):
            df.loc[len(df)] = [pd.Timestamp.now(), float(num)]
            df.to_csv(f'./weight_graphs/weight_{user_id}.csv', index=False)

        df['rolling'] = df['weight'].rolling(7, min_periods=1, center=False).mean()

        plt.plot(df['timestamp'], df[['weight', 'rolling']])
        plt.xlabel("Date")
        plt.ylabel("Weight")
        plt.minorticks_on()
        plt.grid(which='both')
        plt.grid(which='minor', color='#AAAAAA', linestyle=':', linewidth=0.5)
        plt.xticks(rotation=30, fontsize = 'xx-small')
        plt.savefig('weight_graph.png', dpi=300)
        plt.clf()

        f = hikari.File('./weight_graph.png')
        return f
    except Exception as e:
        print(e)
        return "Something went wrong"


def init():
    calories_df = pd.DataFrame(columns=['timestamp', 'calories'])
    calories_df.to_csv('./calories.csv', index=False)


if __name__ == "__main__":
    weight(None, 374970992419799042)