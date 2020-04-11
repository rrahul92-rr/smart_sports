import pandas as pd
import numpy as np
import math as math
import sys
import os
from collections import OrderedDict

sys.setrecursionlimit(2500)

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

df.loc[df['extras'] > 0, 'b_runs_without_extras'] = np.nan
df.loc[df['extras'] == 0, 'b_runs_without_extras'] = df['b_runs']
df1 = df.groupby(['match_key','batsman'])['b_runs_without_extras'].expanding(min_periods=1).mean().reset_index(drop=False).rename(columns={"b_runs_without_extras" : "SR_Player", "level_2" : "Level"})
df2 = df.merge(df1, left_on=['match_key','batsman','Index'], right_on=['match_key','batsman','Level']).drop(['Level'], axis=1)
df2['SR_Player'] = round(df2['SR_Player'] * 100,2)
df2[df2.match_key == 211028]
df2.to_csv("test1.csv")
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


df =  (df.assign(SR_Match=round(100*df.sort_values(by=["ball"])
                                 .groupby(['match_key','innings'])
                                 .total_runs
                                 .expanding()
                                 .mean()
                                 .reset_index(drop=True),2)))

###############################################################################################################################################################

### Bowler base points ###

df1 = df[(df['wicket'] == 1)]
df1 = df1.assign(wicket_rank=df1.groupby(['match_key', 'innings'])['ball'].rank(ascending=True)).filter(['match_key','ball','innings','wicket_rank', 'Index'])
df2 = df.merge(df1, on = ['Index','match_key', 'ball', 'innings'], how = 'left', indicator=False).replace(np.NaN,0)
df2['base_points'] = np.where(np.logical_and(df2['wicket_rank'] != 0, df2['ball'] < 15.0) , (44 - df2['wicket_rank']*4), (33 - df2['wicket_rank']*3))
df2.loc[df2['wicket_rank'] == 0, 'base_points'] = 0



### ER bonus ###

## Overs ##

df['overs_match'] = df['ball'].apply(lambda x: round(math.modf(x)[1] + (5*math.modf(x)[0])/3 , 2))
df['flag'] = 1
df1 = df.groupby(['match_key', 'bowler'])['flag'].expanding().sum().reset_index(drop=False).rename(columns={'flag' : 'overs_bowler', 'level_2' : 'Level'})
df2 = df.merge(df1, left_on=['match_key', 'bowler', 'Index'], right_on=['match_key', 'bowler', 'Level']).drop(['Level','flag'],axis=1)
df2['overs_bowler'] = df2['overs_bowler'].apply(lambda x: round(x/6,2))


## Runs ##

df2['innings_runs_conceded'] = np.where(np.logical_or(df2['legbyes'] > 0, df2['byes'] > 0), 0,df2['total_runs'])
df2 = (df2.assign(cumulative_runs_match=df2.groupby(['match_key','innings'])
                                         .innings_runs_conceded
                                         .expanding()
                                         .sum()
                                         .reset_index(drop=True)))
df3 = df2.groupby(['match_key', 'bowler'])['innings_runs_conceded'].expanding().sum().reset_index(drop=False).rename(columns={'innings_runs_conceded' : 'cumulative_runs_bowler', 'level_2' : 'Level'})
df4 = df2.merge(df3, left_on=['match_key', 'bowler', 'Index'], right_on=['match_key', 'bowler', 'Level']).drop(['Level'],axis=1)

## Bonus Calculation ##

df4['ER_Match'] = round(df4['cumulative_runs_match']/df4['overs_match'],2)
df4['ER_Player'] = round(df4['cumulative_runs_bowler']/df4['overs_bowler'],2)
k1 = 10
df4['ER_Bonus'] = k1 * round((df4['ER_Match'] - df4['ER_Player']) * df4['overs_bowler'],2)
 

### Momentum Bonus ###

df2['over'] = df2['ball'].apply(lambda x: math.floor(x))
df3 = df2[df2['wicket'] == 1]
df3 = (df3.assign(momentum_bonus_bowler=df3.groupby(['match_key', 'bowler','over'])['base_points'].shift()))
df3['momentum_bonus_bowler'] = df3['momentum_bonus_bowler'] * 0.5
df3 = df3[['match_key', 'bowler', 'Index', 'momentum_bonus_bowler']]
df4 = df2.merge(df3, on=['match_key', 'bowler', 'Index'], how= 'outer', indicator = False).replace(np.NaN,0)
df4 = df4[df4['match_key'] == 211028]
df4.to_csv("test_overs_player.csv")


