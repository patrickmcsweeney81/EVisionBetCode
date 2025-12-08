"""
Extract EV hits from raw_odds.csv based on realistic thresholds.

EV hits are opportunities with positive expected value that are worth betting.
Excludes extreme EVs (Betright player props) for more realistic analysis.
"""

import pandas as pd
from pathlib import Path

# Configuration
EV_MIN_THRESHOLD = 3.0  # Minimum 3% edge for profitable bets
EV_MAX_THRESHOLD = 30.0  # Exclude extreme EVs (data quality issues)
# Default to the main raw odds dump produced by ev_arb_bot.py
INPUT_CSV = Path("data/raw_odds.csv")
OUTPUT_CSV = Path("data/ev_hits.csv")

def extract_ev_hits():
    """Extract profitable EV opportunities from CSV."""
    print(f"Reading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    
    # Parse EV percentage
    df['ev_numeric'] = df['ev'].str.rstrip('%').astype(float)
    
    # Filter for profitable EV range (exclude extreme EVs)
    ev_hits = df[(df['ev_numeric'] >= EV_MIN_THRESHOLD) & (df['ev_numeric'] <= EV_MAX_THRESHOLD)].copy()
    
    # Sort by EV descending (best opportunities first)
    ev_hits = ev_hits.sort_values('ev_numeric', ascending=False)
    
    # Drop temporary column
    ev_hits = ev_hits.drop('ev_numeric', axis=1)
    
    # Save file
    ev_hits.to_csv(OUTPUT_CSV, index=False)
    
    # Summary statistics
    total_rows = len(df)
    ev_hits_count = len(ev_hits)
    extreme_count = len(df[df['ev_numeric'] > EV_MAX_THRESHOLD])
    negative_count = len(df[df['ev_numeric'] < 0])
    
    print(f"\n{'='*70}")
    print(f"EV HITS EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Input CSV:              {INPUT_CSV} ({total_rows:,} rows)")
    print(f"EV threshold:           {EV_MIN_THRESHOLD}% to {EV_MAX_THRESHOLD}%")
    print(f"\nResults:")
    print(f"  Extreme EVs (>{EV_MAX_THRESHOLD}%):      {extreme_count:,} rows (excluded - data quality)")
    print(f"  Negative EV (<0%):    {negative_count:,} rows (unfavorable)")
    print(f"  Small positive (<{EV_MIN_THRESHOLD}%):  {total_rows - ev_hits_count - extreme_count - negative_count:,} rows (low edge)")
    print(f"  ✓ EV HITS ({EV_MIN_THRESHOLD}%-{EV_MAX_THRESHOLD}%):   {ev_hits_count:,} rows -> {OUTPUT_CSV}")
    print(f"\nTop 10 EV hits:")
    for idx, row in ev_hits.head(10).iterrows():
        stake = row['stake'] if row['stake'] else "$0"
        print(f"  {row['ev']:>8} | {row['selection'][:30]:30} | {row['book']:15} | Stake: {stake:>6}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    extract_ev_hits()
