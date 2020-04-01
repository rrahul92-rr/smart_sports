import pandas as pd
import numpy as np
import os
from collections import OrderedDict


os.chdir("/Users/basingse/Desktop/Sports fantasy/Data")
print("current working directory :", os.getcwd())

df = pd.read_csv('../Data/T20.csv')
df = df.rename(columns={"Unnamed: 0" : "Index"})

### Expanding Match Strike rate ###

df =  (df.assign(SR_Match=round(100*df.sort_values(by=["ball"])
                                 .groupby(['match_key','innings'])
                                 .total_runs
                                 .expanding()
                                 .mean()
                                 .reset_index(drop=True),2)))

### Expanding Player Strike rate ###

df1 = df.groupby(['match_key','batsman'])['b_runs'].expanding().mean().reset_index(drop=False).rename(columns={"b_runs" : "SR_Player", "level_2" : "Level"})
df2 = df.merge(df1, left_on=['match_key','batsman','Index'], right_on=['match_key','batsman','Level']).drop(['Level'], axis=1)
df2['SR_Player'] = round(df2['SR_Player'] * 100,2)

### Strike rate Bonus ###

k1 = 0.25
df2["SR_Bonus"] = round((df2["SR_Player"] - df2["SR_Match"])*k1,2)

### Momentum Bonus ### 

k2 = 0.20
df =  (df2.assign(Momentum_Bonus=round(k2*100*df2.sort_values(by=["ball"])
                                 .groupby(['match_key', 'innings'])
                                 .total_runs
                                 .rolling(3)
                                 .mean()
                                 .reset_index(drop=True),2)))
df["Momentum_Bonus"] = df["Momentum_Bonus"].replace(np.NaN,0)

### Support Bonus ###

k3 = 0.25
df['Support_Bonus'] = df["b_runs"].apply(lambda x: 10*x*k3 if x<=3 else 0)

### Partnership bonus ###


### Ball-wise performance scores ###

df['Performance_Score'] = df['b_runs'] + df['SR_Bonus'] + df['Momentum_Bonus'] + df['Support_Bonus']


### Performance Aggregation ###

final_player_performance = df.groupby(['match_key','batsman']).agg({'Performance_Score' : ['sum','mean','median','max','min'], 'b_runs' : 'sum', 'Index' : 'size' })


### Defining a class for Batsman performance Algorithm ###

final_player_performance.to_csv("final_player_performance.csv")




