import pandas as pd

df = pd.read_csv('data/v3/extracts/basketball_nba_filtered_20260109_060509.csv')
paired = df[df['pair_id'].notna()]

print(f"Total rows with pair_id: {len(paired):,}")
print(f"Unique pair_ids: {paired['pair_id'].nunique():,}")
print(f"\nCardinality distribution:")
cardinality_dist = paired.groupby('pair_id').size().value_counts().sort_index()
for card, count in cardinality_dist.items():
    print(f"  {card} rows: {count:,} pair_ids")

# Find which pairs have cardinality != 2
non_2_pairs = paired.groupby('pair_id').size()
non_2_pairs = non_2_pairs[non_2_pairs != 2]
print(f"\nPairs with cardinality != 2: {len(non_2_pairs)}")

# Show a sample of the problematic pair
if len(non_2_pairs) > 0:
    bad_pair_id = non_2_pairs.index[0]
    bad_group = paired[paired['pair_id'] == bad_pair_id]
    print(f"\nSample bad pair (id={bad_pair_id}, rows={len(bad_group)}):")
    print(bad_group[['event_name', 'market_type', 'player_name', 'point', 'selection']].to_string())
