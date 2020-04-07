import pandas as pd
import numpy as np
import math as math
import os
from collections import OrderedDict


os.chdir("/Users/basingse/Desktop/Sports fantasy/Data")
print("current working directory :", os.getcwd())

df = pd.read_csv('../Data/T20.csv')
df = df.rename(columns={"Unnamed: 0" : "Index"})

##    k1 = Strike rate factor
##    k2 = Momentum factor
##    k3 = Support factor

class batsman_performance:
    
	'''This class contains all the methods to generate batsman performance score'''
	''' k1 = Strike rate factor '''
	''' k2 = Momentum factor '''
	''' k3 = Support factor '''
 
	def __init__(self, df, k1 = 0.25, k2 = 0.25, k3  = 0.25):
		self.df = df
		self.k1 = k1
		self.k2 = k2
		self.k3 = k3

	def momentum_bonus_batsman(self):
		self.df = self.df.assign(Momentum_Bonus_Batsman=round(100*self.k2 * self.df
                                                .sort_values(by=["ball"])
                                                .groupby(['match_key', 'innings'])
                                                .total_runs
                                                .rolling(3)
                                                .mean()
                                                .reset_index(drop=True),2)
                           						.replace(np.NaN,0))

	def match_strike_rate(self):
		self.df = self.df.assign(SR_Match=round(100*self.df.sort_values(by=["ball"])
										.groupby(['match_key','innings'])
										.total_runs
										.expanding()
										.mean()
										.reset_index(drop=True),2))

	def player_strike_rate(self):
		self.df.loc[self.df['extras'] > 0, 'b_runs_without_extras'] = np.nan
		self.df.loc[self.df['extras'] == 0, 'b_runs_without_extras'] = self.df['b_runs']
		df1 = self.df.groupby(['match_key','batsman'])['b_runs_without_extras'].expanding(min_periods=1).mean().reset_index(drop=False).rename(columns={"b_runs_without_extras" : "SR_Player", "level_2" : "Level"})
		self.df = self.df.merge(df1, left_on=['match_key','batsman','Index'], right_on=['match_key','batsman','Level']).drop(['Level'], axis=1)
		self.df['SR_Player'] = (self.df['SR_Player'] * 100)

	def strike_rate_bonus(self):
		self.df["SR_Bonus"] = round((self.df["SR_Player"] - self.df["SR_Match"]) * self.k1,2)

	def support_bonus(self):
		self.df['Support_Bonus'] = (self.df["b_runs"].apply(lambda x: 10*x*self.k3 if x<=3 else 0))

	def performance_score_per_ball(self):
		self.df['Performance_Score_Batsman'] = self.df['b_runs'] + self.df['SR_Bonus'] + self.df['Momentum_Bonus_Batsman'] + self.df['Support_Bonus']

	def perfromance_score_batsman(self):
		return(self.df.groupby(['match_key','batsman']).agg({'Performance_Score_Batsman' : ['sum','mean','median','max','min'], 'b_runs' : 'sum', 'Index' : 'size' }))

	def generate_batsman_score(self):
		self.momentum_bonus_batsman()
		self.match_strike_rate()
		self.player_strike_rate()
		self.strike_rate_bonus()
		self.support_bonus()
		self.performance_score_per_ball()
		df = self.perfromance_score_batsman()
		return(df)


obj1 = batsman_performance(df)
df_output = obj1.generate_batsman_score()
print(df_output)
print(obj1.df)


class bowler_performance:
	'''This class includes all the methods to generate bowler performance score'''
	''' k1 = Bonus factor '''

	def __init__(self, df, k1 = 10):
		self.df = df
		self.k1 = k1
  
	def base_points(self):
		df1 = self.df[(self.df['wicket'] == 1) & (self.df['kind'].isin(['caught', 'bowled', 'lbw', 'stumped', 'hit wicket']))]
		df1 = df1.assign(wicket_rank=df1.groupby(['match_key', 'innings'])['ball'].rank(ascending=True)).filter(['match_key','ball','innings','wicket_rank', 'Index'])
		self.df = self.df.merge(df1, on = ['Index','match_key', 'ball', 'innings'], how = 'left', indicator=False).replace(np.NaN,0)
		self.df['Base_Points'] = np.where(np.logical_and(self.df['wicket_rank'] != 0, self.df['ball'] < 15.0) , (44 - self.df['wicket_rank']*4), (33 - self.df['wicket_rank']*3))
		self.df.loc[self.df['wicket_rank'] == 0, 'Base_Points'] = 0

	def overs_bowled(self):
		self.df['overs_match'] = self.df['ball'].apply(lambda x: round(math.modf(x)[1] + (5*math.modf(x)[0])/3 , 2))
		self.df['flag'] = 1
		df1 = self.df.groupby(['match_key', 'bowler'])['flag'].expanding().sum().reset_index(drop=False).rename(columns={'flag' : 'overs_bowler', 'level_2' : 'Level'})
		self.df = self.df.merge(df1, left_on=['match_key', 'bowler', 'Index'], right_on=['match_key', 'bowler', 'Level']).drop(['Level','flag'],axis=1)
		self.df['overs_bowler'] = self.df['overs_bowler'].apply(lambda x: round(x/6,2))
  
	def runs_conceded(self):
		self.df['innings_runs_conceded'] = np.where(np.logical_or(self.df['legbyes'] > 0, self.df['byes'] > 0), 0, self.df['total_runs'])
		self.df = (self.df.assign(cumulative_runs_match=self.df.groupby(['match_key','innings'])
                                         .innings_runs_conceded
                                         .expanding()
                                         .sum()
                                         .reset_index(drop=True)))
		df2 = self.df.groupby(['match_key', 'bowler'])['innings_runs_conceded'].expanding().sum().reset_index(drop=False).rename(columns={'innings_runs_conceded' : 'cumulative_runs_bowler', 'level_2' : 'Level'})
		self.df = self.df.merge(df2, left_on=['match_key', 'bowler', 'Index'], right_on=['match_key', 'bowler', 'Level']).drop(['Level'],axis=1)

	def economy_rate_bonus(self):
		self.df['ER_Match'] = round(self.df['cumulative_runs_match']/self.df['overs_match'],2)
		self.df['ER_Player'] = round(self.df['cumulative_runs_bowler']/self.df['overs_bowler'],2)
		self.df['ER_Bonus'] = self.k1 * round((self.df['ER_Match'] - self.df['ER_Player']) * self.df['overs_bowler'],2)
  
	def momentum_bonus_bowler(self):
		self.df['over'] = self.df['ball'].apply(lambda x: math.floor(x))
		df2 = self.df[self.df['wicket'] == 1]
		df2 = (df2.assign(Momentum_Bonus_Bowler=df2.groupby(['match_key', 'bowler','over'])['Base_Points'].shift()))
		df2['Momentum_Bonus_Bowler'] = df2['Momentum_Bonus_Bowler'] * 0.5
		df2 = df2[['match_key', 'bowler', 'Index', 'Momentum_Bonus_Bowler']]
		self.df = self.df.merge(df2, on=['match_key', 'bowler', 'Index'], how= 'outer', indicator = False).replace(np.NaN,0)
  
	def performance_score_per_ball(self):
		self.df['Performance_Score_Bowler'] = self.df['Base_Points'] + self.df['ER_Bonus'] + self.df['Momentum_Bonus_Bowler']
  
	def performance_score_bowler(self):
		return(self.df.groupby(['match_key', 'bowler']).agg({'Performance_Score_Bowler' : ['sum','mean','median','max','min']}))

	def generate_bowler_score(self):
		self.base_points()
		self.overs_bowled()
		self.runs_conceded()
		self.economy_rate_bonus()
		self.momentum_bonus_bowler()
		self.performance_score_per_ball()
		df = self.performance_score_bowler()
		return(df)

obj2 = bowler_performance(df)
df_output2 = obj2.generate_bowler_score()
print(df_output2)
print(obj2.df)
