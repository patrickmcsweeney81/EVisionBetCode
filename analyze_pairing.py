import pandas as pd

# Load filtered CSV
df = pd.read_csv('data/v3/extracts/basketball_nba_filtered_new.csv')

# Check player_assists market with pair_ids
player_assists = df[df['market_type'] == 'player_assists'].copy()
print(f"Total player_assists rows: {len(player_assists)}")

# Show unique pair_id values and their compositions
print("\n=== PAIR ID ANALYSIS ===")
for pair_id in sorted(player_assists['pair_id'].dropna().unique())[:5]:
    pair_group = player_assists[player_assists['pair_id'] == pair_id]
    print(f"\nPair ID {pair_id}:")
    print(pair_group[['event_name', 'player_name', 'point', 'selection']].to_string())
    print(f"   Unique players: {pair_group['player_name'].unique().tolist()}")
    print(f"   Unique points: {pair_group['point'].unique().tolist()}")
    print(f"   Row count: {len(pair_group)}")
