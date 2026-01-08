import pandas as pd

df = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')
devig = df[df['uses_devig'] == True]

print(f'Rows with uses_devig=TRUE: {len(devig)}')
print(f'Of those, paired (has pair_id): {devig["pair_id"].notna().sum()}')
print(f'\nSample devig rows with pair_ids:')
sample = devig[devig['pair_id'].notna()][['event_name', 'market_type', 'selection', 'point', 'pair_id', 'uses_devig', 'EV']].head(10)
print(sample.to_string())
