"""
Debug Duplicate Bets
====================
Finds identical bets across different market types.

Example:
  - Brooklyn Nets @ Washington Wizards | spreads | 3.5 | Brooklyn Nets
  - Brooklyn Nets @ Washington Wizards | alternate_spreads | 3.5 | Brooklyn Nets
  
Both are the SAME bet (same point, same team, same event) but different market labels.
"""

import pandas as pd
import glob

def debug_duplicates():
    """Find and report duplicate bets across market types."""
    
    # Load latest NBA_Raw CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_raw_*.csv"))
    if not csv_files:
        print("❌ No NBA_Raw CSV found")
        return
    
    latest_csv = csv_files[-1]
    df = pd.read_csv(latest_csv)
    
    print(f"📂 Analyzing: {latest_csv}")
    print(f"📊 Total rows: {len(df):,}\n")
    
    # Group by (event_name, selection, point) - ignoring market_type
    # This finds bets that are identical except for market label
    bet_key = ['event_name', 'selection', 'point']
    
    # Find bets that appear multiple times (in different market_types)
    duplicates = df.groupby(bet_key, dropna=False).size().reset_index(name='count')
    duplicates = duplicates[duplicates['count'] > 1]
    
    print(f"🔍 Analysis:")
    print(f"   Unique bets (event + selection + point): {len(duplicates) + (len(df.groupby(bet_key)) - len(duplicates)):,}")
    print(f"   Duplicate bets (same across market types): {len(duplicates):,}")
    print(f"   Total rows in duplicates: {duplicates['count'].sum():,}")
    print(f"   Rows that could be REMOVED: {duplicates['count'].sum() - len(duplicates):,}")
    print(f"   % Reduction: {((duplicates['count'].sum() - len(duplicates)) / len(df) * 100):.1f}%\n")
    
    # Show examples
    if len(duplicates) > 0:
        print("📋 Example duplicates:")
        print("=" * 100)
        
        # Find a duplicate example
        sample_bet = duplicates.iloc[0]
        event, sel, point = sample_bet['event_name'], sample_bet['selection'], sample_bet['point']
        
        # Get all rows for this bet
        dup_rows = df[(df['event_name'] == event) & 
                      (df['selection'] == sel) & 
                      (df['point'] == point)]
        
        print(f"\n{event} | {sel} | {point}")
        print(f"  Appears in {len(dup_rows)} rows across different market_types:\n")
        
        for idx, row in dup_rows.iterrows():
            print(f"  • market_type: {row['market_type']:20} | pinnacle: {row.get('pinnacle', 'N/A')}")
        
        print("\n" + "=" * 100)
        print(f"\nIf we keep only 1 copy per unique bet, we'd keep {len(dup_rows) // len(duplicates[duplicates['event_name'] == event])} rows")
        print(f"and remove {len(dup_rows) - 1} redundant rows for this bet alone\n")
    
    # Market type breakdown
    print("📊 Market type breakdown in duplicates:")
    dup_market_counts = []
    for _, row in duplicates.iterrows():
        event, sel, point = row['event_name'], row['selection'], row['point']
        markets = df[(df['event_name'] == event) & 
                    (df['selection'] == sel) & 
                    (df['point'] == point)]['market_type'].tolist()
        dup_market_counts.extend(markets)
    
    import collections
    market_freq = collections.Counter(dup_market_counts)
    for market, count in market_freq.most_common():
        print(f"   {market:25} {count:6,} occurrences in duplicates")

if __name__ == "__main__":
    debug_duplicates()
