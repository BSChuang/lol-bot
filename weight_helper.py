'''
    Two functions:
    !c [number]: adds calories to the calories of the day
        calories are saved to a csv with two columns: timestamp and calories
    !c: sums the calories eaten today
    !lb [number]: records weight at time of call
        weight is saved to csv with two columns: timestamp and weight
    !lb: prints graph of weight
'''

from calorieninja import get_calories
import pandas as pd
import matplotlib.pyplot as plt
import hikari
import math
import os

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

    try:
        items = None
        if body == '':
            calorie = None
        elif body.isdigit():
            calorie = float(body)
        else:
            items = get_calories(body)
            calorie = sum([x['calories'] for x in items])

        print(calorie)


        df = pd.read_csv('./calories.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if calorie is not None and is_valid(calorie, 0, 5000):
            df.loc[len(df)] = [pd.Timestamp.now(), float(calorie)]
        
        df.to_csv('./calories.csv', index=False)
        
        day_calories = df.groupby(df['timestamp'].dt.date)['calories'].sum().tail(1).item()


        calories_str = f'Added {calorie} calories' if calorie is not None else ''
        items_str = '\n'.join([str(item) for item in items]) if items else ''
 
        return items_str + f'\n\n{calories_str}\nTotal calories for the day: {round(day_calories)}'
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
        return f'Total calories for the day: {round(day_calories)}'
    except Exception as e:
        print(e)
        return f"Something went wrong: {e}"
    
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