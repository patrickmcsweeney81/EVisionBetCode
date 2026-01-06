import pandas as pd

df = pd.read_csv('data/v3/extracts/basketball_nba_raw_20260106_132619.csv')
print("Commence times from latest extraction:")
print(df['commence_time'].drop_duplicates().tolist())
