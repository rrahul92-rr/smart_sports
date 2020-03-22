import pandas as pd
import numpy as np
import os
from collections import OrderedDict

os.chdir("/Users/basingse/Desktop/Sports fantasy/Data")
print("current working directory :", os.getcwd())

df = pd.read_csv('../Data/T20.csv')

result = list(OrderedDict.fromkeys(list(df.match_key)))

df1 = df[(df.team == "England") &  (df.batsman == "ME Trescothick")]


### Expanding Match Strike rate ###

df =  (df.assign(SR_match=round(100*df.sort_values(by=["ball"])
                                 .groupby(['match_key','innings'])
                                 .total_runs
                                 .expanding()
                                 .mean()
                                 .reset_index(drop=True),2)))

### Expanding Player Strike rate ###

df1 = df.groupby(['match_key','batsman'])['b_runs'].expanding().mean().reset_index(drop=False).rename(columns={"b_runs" : "SR_Player", "level_2" : "Level"})
df2 = df.merge(df1, left_on=['match_key','batsman','Unnamed: 0'], right_on=['match_key','batsman','Level']).drop(['Level'], axis=1)
df2['SR_Player'] = round(df2['SR_Player'] * 100,2)



### Momentum Bonus ### 

k = 0.25
df =  (df.assign(momentum_bonus=round(k*100*df.sort_values(by=["ball"])
                                 .groupby(['match_key', 'innings'])
                                 .total_runs
                                 .rolling(3)
                                 .mean()
                                 .reset_index(drop=True),2)))

###########################


