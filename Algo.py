import pandas as pd
import numpy as np
import os
from collections import OrderedDict

os.chdir("/Users/basingse/Desktop/Sports fantasy/Data")
print("current working directory :", os.getcwd())

df = pd.read_csv('../Data/T20.csv')

result = list(OrderedDict.fromkeys(list(df.match_key)))

df.to_csv("test3.csv")

df1 = df[(df.match_key == 211028) & (df.innings == "1st innings")]

df =  (df.assign(SR_match=round(100*df.groupby(['match_key','innings'])
                                 .total_runs
                                 .expanding()    
                                 .mean()
                                 .reset_index(drop=True),2)))

df =  (df.assign(SR_player=round(100*df.groupby(['match_key','innings','batsman'])
                                 .b_runs
                                 .expanding()    
                                 .mean()
                                 .reset_index(drop=True),2)))




df.head()


