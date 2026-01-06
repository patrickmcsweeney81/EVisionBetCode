"""
Debug: Check point values and types for spreads
"""

import pandas as pd
import numpy as np

df = pd.read_csv("data/v3/extracts/basketball_nba_filtered.csv")

spreads = df[df['market_type'] == 'spreads'].head(10)
print("Sample spreads rows:")
print(spreads[['event_name', 'selection', 'point']].to_string())

print(f"\nPoint dtype: {spreads['point'].dtype}")
print(f"\nPoint values:")
for idx, val in spreads['point'].items():
    print(f"  {idx}: {val} (type: {type(val).__name__})")

# Check if negation works
print("\n\nTesting negation:")
test_points = spreads['point'].unique()[:5]
for p in test_points:
    try:
        neg = -float(p)
        print(f"  {p} → {neg}")
    except Exception as e:
        print(f"  {p} → ERROR: {e}")

# Check for exact match
print("\n\nChecking for exact match with negation:")
event_id = spreads.iloc[0]['event_id']
point_val = spreads.iloc[0]['point']
selection = spreads.iloc[0]['selection']
print(f"Looking for opposite of: event={event_id}, selection={selection}, point={point_val}")

opposite_sel = "Indiana Pacers" if selection == "Cleveland Cavaliers" else "Cleveland Cavaliers"
opposite_point = -float(point_val)

print(f"Searching for: selection={opposite_sel}, point={opposite_point}")

matches = df[(df['event_id'] == event_id) & 
             (df['market_type'] == 'spreads') & 
             (df['selection'] == opposite_sel) &
             (df['point'] == opposite_point)]

print(f"Found {len(matches)} matches")
if len(matches) > 0:
    print(matches[['selection', 'point']].to_string())
else:
    # Debug: show what points exist for opposite
    opposite_rows = df[(df['event_id'] == event_id) & 
                       (df['market_type'] == 'spreads') & 
                       (df['selection'] == opposite_sel)]
    print(f"Available points for {opposite_sel}: {opposite_rows['point'].unique()}")
