import pandas as pd
import numpy as np
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
	def __init__(self, df, k1 = 0.25, k2 = 0.25, k3  = 0.25):
		self.df = df
		self.k1 = k1
		self.k2 = k2
		self.k3 = k3

	def momentum_bonus(self):
		self.df = self.df.assign(Momentum_Bonus=round(100*self.k2 * self.df
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
		df1 = self.df.groupby(['match_key','batsman'])['b_runs'].expanding().mean().reset_index(drop=False).rename(columns={"b_runs" : "SR_Player", "level_2" : "Level"})
		self.df = self.df.merge(df1, left_on=['match_key','batsman','Index'], right_on=['match_key','batsman','Level']).drop(['Level'], axis=1)
		self.df['SR_Player'] = (self.df['SR_Player'] * 100)

	def strike_rate_bonus(self):
		self.df["SR_Bonus"] = round((self.df["SR_Player"] - self.df["SR_Match"]) * self.k1,2)

	def support_bonus(self):
		self.df['Support_Bonus'] = (self.df["b_runs"].apply(lambda x: 10*x*self.k3 if x<=3 else 0))

	def performance_score_per_ball(self):
		self.df['Performance_Score'] = self.df['b_runs'] + self.df['SR_Bonus'] + self.df['Momentum_Bonus'] + self.df['Support_Bonus']

	def perfromance_score_match(self):
		return(self.df.groupby(['match_key','batsman']).agg({'Performance_Score' : ['sum','mean','median','max','min'], 'b_runs' : 'sum', 'Index' : 'size' }))

	def generate_score(self):
		self.momentum_bonus()
		self.match_strike_rate()
		self.player_strike_rate()
		self.strike_rate_bonus()
		self.support_bonus()
		self.performance_score_per_ball()
		df = self.perfromance_score_match()
		return(df)


obj1 = batsman_performance(df)
df_output = obj1.generate_score()
print(df_output)
print(obj1.df)

