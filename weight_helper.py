import pandas as pd
import matplotlib.pyplot as plt
import discord
import math
import os

def is_valid(num, min_range, max_range):
    try:
        float_num = float(num)
        return math.isfinite(float_num) and not math.isnan(float_num) and min_range < float_num < max_range
    except:
        return False
    
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

        f = discord.File('./weight_graph.png')
        return f
    except Exception as e:
        print(e)
        return "Something went wrong"

if __name__ == "__main__":
    weight(None, 374970992419799042)