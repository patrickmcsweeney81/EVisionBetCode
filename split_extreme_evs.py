"""
Split raw_odds.csv into three CSV files:
1. all_odds.csv - ALL opportunities (reference)
2. ev_hits.csv - Positive EV opportunities (0% to 30%) - RECOMMENDED FOR BETTING
3. extreme_odds.csv - Extreme EV (>30% OR <-5%) - FOR MANUAL ANALYSIS

Extreme EVs are moved to a separate file for manual review/analysis:
- High positive EV (>30%): Potential value or data issues
- Negative EV (<-5%): Poor value, sharp book discrepancies, stale odds
"""

import pandas as pd
from pathlib import Path

# Configuration
EXTREME_EV_THRESHOLD = 30.0  # Percent (upper bound)
NEGATIVE_EV_THRESHOLD = -5.0  # Percent (lower bound for extreme bad value)
POSITIVE_EV_THRESHOLD = 0.0  # Percent
INPUT_CSV = Path("data/raw_odds.csv")
OUTPUT_ALL = Path("data/all_odds.csv")
OUTPUT_EV_HITS = Path("data/ev_hits.csv")
OUTPUT_EXTREME = Path("data/extreme_odds.csv")

def split_extreme_evs():
    """Split CSV into all_odds, ev_hits, and extreme EV files."""
    print(f"Reading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    
    # Parse EV percentage
    df['ev_numeric'] = df['ev'].str.rstrip('%').astype(float)
    
    # Split data into 3 categories
    all_odds = df.copy()
    ev_hits = df[(df['ev_numeric'] > POSITIVE_EV_THRESHOLD) & (df['ev_numeric'] <= EXTREME_EV_THRESHOLD)].copy()
    extreme = df[(df['ev_numeric'] > EXTREME_EV_THRESHOLD) | (df['ev_numeric'] < NEGATIVE_EV_THRESHOLD)].copy()
    
    # Drop temporary column from all
    all_odds = all_odds.drop('ev_numeric', axis=1)
    ev_hits = ev_hits.drop('ev_numeric', axis=1)
    extreme = extreme.drop('ev_numeric', axis=1)
    
    # Sort by EV descending (best first)
    all_odds['ev_sort'] = all_odds['ev'].str.rstrip('%').astype(float)
    all_odds = all_odds.sort_values('ev_sort', ascending=False).drop('ev_sort', axis=1)
    
    ev_hits['ev_sort'] = ev_hits['ev'].str.rstrip('%').astype(float)
    ev_hits = ev_hits.sort_values('ev_sort', ascending=False).drop('ev_sort', axis=1)
    
    extreme['ev_sort'] = extreme['ev'].str.rstrip('%').astype(float)
    extreme = extreme.sort_values('ev_sort', ascending=False).drop('ev_sort', axis=1)
    
    # Save files
    all_odds.to_csv(OUTPUT_ALL, index=False)
    ev_hits.to_csv(OUTPUT_EV_HITS, index=False)
    extreme.to_csv(OUTPUT_EXTREME, index=False)
    
    print(f"\n{'='*70}")
    print(f"SPLIT COMPLETE - 3 CSV FILES CREATED")
    print(f"{'='*70}")
    print(f"Total rows:        {len(df):,}")
    print(f"\n📊 ALL_ODDS ({POSITIVE_EV_THRESHOLD}% to 100%)")
    print(f"   {len(all_odds):,} rows -> {OUTPUT_ALL}")
    print(f"   (Reference file with all opportunities)")
    print(f"\n✓ EV_HITS ({POSITIVE_EV_THRESHOLD}% to {EXTREME_EV_THRESHOLD}%)")
    print(f"   {len(ev_hits):,} rows -> {OUTPUT_EV_HITS}")
    print(f"   (RECOMMENDED FOR BETTING - realistic edges)")
    print(f"\n⚠️  EXTREME_EV (>{EXTREME_EV_THRESHOLD}% OR <{NEGATIVE_EV_THRESHOLD}%)")
    print(f"   {len(extreme):,} rows -> {OUTPUT_EXTREME}")
    print(f"   (Manual review only - outliers/data issues)")
    
    print(f"\n{'─'*70}")
    print(f"Top 5 EV_HITS (sorted by highest edge):")
    if len(ev_hits) > 0:
        for idx, row in ev_hits.head(5).iterrows():
            stake = row['stake'] if row['stake'] else "$0"
            print(f"  {row['ev']:>8} | {row['selection'][:28]:28} | {row['book']:15} | Stake: {stake:>6}")
    else:
        print("  None found!")
    
    print(f"\n{'─'*70}")
    print(f"Top 5 EXTREME_EV (for analysis):")
    if len(extreme) > 0:
        for idx, row in extreme.head(5).iterrows():
            print(f"  {row['ev']:>8} | {row['selection'][:28]:28} | {row['book']:15}")
    else:
        print("  None found!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    split_extreme_evs()
