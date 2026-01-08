import pandas as pd
df = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')
print('First 10 columns:', list(df.columns)[:10])
print(f'\nFirst 5 rows:')
print(df[['id', 'event_name', 'market_type', 'selection', 'pair_id']].head(10).to_string())
