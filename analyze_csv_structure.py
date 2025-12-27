"""
V3 STANDARDIZATION & CLEANUP PLAN
Generated: December 28, 2025

GOAL: One clean V3 folder with no confusion. Use YOUR CSV structure as the standard.
"""

import pandas as pd

# Load your reference CSV (what you want)
df = pd.read_csv('data/v3/extracts/basketball_nba_raw_20251227_065532.csv')

print("=" * 80)
print("YOUR V3 STANDARD STRUCTURE")
print("=" * 80)
print(f"\nCSV Shape: {df.shape[0]} rows x {df.shape[1]} columns")
print(f"\nCore Columns (8):")
core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 'market_type', 'point', 'selection']
for i, col in enumerate(core_cols, 1):
    print(f"  {i}. {col}")

print(f"\nBookmakers Columns ({df.shape[1] - 8}):")
bookmaker_cols = [c for c in df.columns if c not in core_cols]
for i, col in enumerate(bookmaker_cols, 1):
    print(f"  {i}. {col}")

print(f"\nMarket Types: {df['market_type'].unique().tolist()}")
print(f"Sample Data:\n{df.iloc[0][core_cols]}")
