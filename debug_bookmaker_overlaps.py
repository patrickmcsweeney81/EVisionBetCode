"""
Debug Bookmaker Overlaps
========================
Check if bookmakers offered same point values in both spreads and alternate_spreads.
"""

import pandas as pd
import glob

def check_overlaps():
    """Find bookmakers offering same line in both spreads and alternate_spreads."""
    
    # Load latest NBA_Raw CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_raw_*.csv"))
    df = pd.read_csv(csv_files[-1])
    
    print(f"📂 Analyzing: {csv_files[-1]}\n")
    
    # Get all bookmaker columns (skip core metadata columns)
    core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
                 'market_type', 'point', 'selection', 'player_name']
    bookmaker_cols = [col for col in df.columns if col not in core_cols]
    
    # Find overlaps: same bookmaker, same event, same selection, same point in both spreads and alternate_spreads
    spreads_df = df[df['market_type'] == 'spreads'].copy()
    alt_spreads_df = df[df['market_type'] == 'alternate_spreads'].copy()
    
    # Group by (event_name, selection, point) and check which bookmakers appear in both
    overlap_count = 0
    total_overlap_rows = 0
    
    print("🔍 Checking for bookmaker overlaps (same point in spreads AND alternate_spreads):\n")
    
    for event in df['event_name'].unique():
        for selection in ['home', 'away']:
            for point in df[df['event_name'] == event]['point'].unique():
                spreads_row = spreads_df[(spreads_df['event_name'] == event) & 
                                        (spreads_df['selection'] == selection) & 
                                        (spreads_df['point'] == point)]
                alt_row = alt_spreads_df[(alt_spreads_df['event_name'] == event) & 
                                        (alt_spreads_df['selection'] == selection) & 
                                        (alt_spreads_df['point'] == point)]
                
                if len(spreads_row) > 0 and len(alt_row) > 0:
                    # Check which bookmakers appear in both
                    spreads_books = set(spreads_row.iloc[0][bookmaker_cols].dropna().index)
                    alt_books = set(alt_row.iloc[0][bookmaker_cols].dropna().index)
                    shared = spreads_books & alt_books
                    
                    if shared:
                        overlap_count += 1
                        total_overlap_rows += len(shared)
                        print(f"📌 {event} | {selection} | {point}")
                        print(f"   Shared bookmakers: {shared}")
    
    print(f"\n📊 Summary:")
    print(f"   Unique (event, selection, point) with bookmaker overlap: {overlap_count}")
    print(f"   Total bookmaker overlaps: {total_overlap_rows}")
    print(f"\n✅ These were TRUE duplicates - same bookmaker, same point, both markets")

if __name__ == "__main__":
    check_overlaps()
