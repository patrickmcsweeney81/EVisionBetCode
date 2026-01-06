import pandas as pd

# Check raw
df_raw = pd.read_csv('data/v3/extracts/basketball_nba_raw_20260106_132312.csv')
print("Raw CSV commence_time (first 5):")
print(df_raw['commence_time'].head(5).tolist())
