import pandas as pd

df = pd.read_csv('data/v3/extracts/basketball_nba_filtered_20260106_130324.csv')
print("Sample commence_time values:")
print(df['commence_time'].head(10).tolist())
