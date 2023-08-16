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

def calories(num):
    try:
        df = pd.read_csv('./calories.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if num is not None:
            df.loc[len(df)] = [pd.Timestamp.now(), float(num)]
        
        df.to_csv('./calories.csv', index=False)
        
        day_calories = df.groupby(df['timestamp'].dt.date)['calories'].sum().tail(1).item()
        return f'Total calories for the day: {day_calories}'
    except:
        return "Something went wrong"
    
def weight(num):
    try:
        df = pd.read_csv('./weight.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if num is not None:
            df.loc[len(df)] = [pd.Timestamp.now(), float(num)]
            df.to_csv('./weight.csv', index=False)
            
        df.plot(x='timestamp', y='weight', kind='line').set_ylim(bottom=0)
        plt.savefig('weight_graph.png', dpi=300)
        f = hikari.File('./weight_graph.png')
        return f
    except:
        return "Something went wrong"


def init():
    calories_df = pd.DataFrame(columns=['timestamp', 'calories'])
    weight_df = pd.DataFrame(columns=['timestamp', 'weight'])

    calories_df.to_csv('./calories.csv', index=False)
    weight_df.to_csv('./weight.csv', index=False)


if __name__ == "__main__":
    init()