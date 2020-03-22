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



### Momentum Bonus ### 

k = 0.25
df =  (df.assign(momentum_bonus=round(k*100*df.sort_values(by=["ball"])
                                 .groupby(['match_key', 'innings'])
                                 .total_runs
                                 .rolling(3)
                                 .mean()
                                 .reset_index(drop=True),2)))

###########################

df1 =  (df1.assign(SR_player=round(100*df1.sort_values(by=["ball"], ascending=False)
                                 .groupby(['batsman', 'match_key'])
                                 .b_runs
                                 .expanding()
                                 .mean()
                                 .reset_index(drop=True),2)))

df1.head(10)
df3.to_csv("test5.csv")
df1.groupby(['match_key','batsman']).b_runs.expanding().median()

df2 = df1.groupby(['match_key','batsman'])['b_runs'].expanding().mean().reset_index(drop=False)
df2.rename(columns={"b_runs" : "SR_Player"})
df3 = df1.merge(df2, left_on=['match_key','batsman','Unnamed: 0'], right_on=['match_key','batsman','level_2'])


