"""
Split all_odds_analysis.csv into normal and extreme EV files.

Extreme EVs (>30%) are moved to a separate file for manual review/analysis.
This helps identify:
1. Genuine high-value opportunities (e.g., star players with high lines)
2. Manipulated sharp book odds (placeholder pricing)
3. Data quality issues
"""

import pandas as pd
from pathlib import Path

# Configuration
EXTREME_EV_THRESHOLD = 30.0  # Percent
INPUT_CSV = Path("data/all_odds_analysis.csv")
OUTPUT_NORMAL = Path("data/all_odds.csv")
OUTPUT_EXTREME = Path("data/extreme_odds.csv")

def split_extreme_evs():
    """Split CSV into normal and extreme EV files."""
    print(f"Reading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    
    # Parse EV percentage
    df['ev_numeric'] = df['ev'].str.rstrip('%').astype(float)
    
    # Split data
    normal = df[df['ev_numeric'] <= EXTREME_EV_THRESHOLD].copy()
    extreme = df[df['ev_numeric'] > EXTREME_EV_THRESHOLD].copy()
    
    # Drop temporary column
    normal = normal.drop('ev_numeric', axis=1)
    extreme = extreme.drop('ev_numeric', axis=1)
    
    # Sort extreme by EV (highest first)
    extreme['ev_sort'] = extreme['ev'].str.rstrip('%').astype(float)
    extreme = extreme.sort_values('ev_sort', ascending=False).drop('ev_sort', axis=1)
    
    # Save files
    normal.to_csv(OUTPUT_NORMAL, index=False)
    extreme.to_csv(OUTPUT_EXTREME, index=False)
    
    print(f"\n{'='*60}")
    print(f"SPLIT COMPLETE")
    print(f"{'='*60}")
    print(f"Total rows:        {len(df):,}")
    print(f"Normal (≤{EXTREME_EV_THRESHOLD}%):    {len(normal):,} rows -> {OUTPUT_NORMAL}")
    print(f"Extreme (>{EXTREME_EV_THRESHOLD}%):   {len(extreme):,} rows -> {OUTPUT_EXTREME}")
    print(f"\nTop 5 extreme EVs:")
    if len(extreme) > 0:
        for idx, row in extreme.head(5).iterrows():
            print(f"  {row['ev']:>8} | {row['selection'][:35]:35} | {row['market'][:25]:25} | {row['book']}")
    else:
        print("  None found!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    split_extreme_evs()
