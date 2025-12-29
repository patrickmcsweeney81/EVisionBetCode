"""
SPREADS/TOTALS: GROUP ALL AVAILABLE LINES
Preserve every market point variation as separate market
"""

import pandas as pd
import glob
from pathlib import Path

def get_latest_csv():
    """Find latest CSV file"""
    files = sorted(glob.glob(r"data/v3/extracts/*.csv"))
    return files[-1] if files else None

def load_and_group_markets(csv_path):
    """
    Load CSV and group by (event_id, market_type, point, selection)
    Each group = one complete market with all bookmakers
    """
    
    df = pd.read_csv(csv_path)
    
    # Filter to spreads and totals
    markets_df = df[df['market_type'].isin(['spreads', 'totals'])].copy()
    
    # Convert point to numeric
    markets_df['point'] = pd.to_numeric(markets_df['point'], errors='coerce')
    
    print(f"\n{'='*70}")
    print(f"SPREADS & TOTALS: ALL AVAILABLE LINES")
    print(f"{'='*70}\n")
    
    # Group by market key
    grouped = markets_df.groupby(
        ['event_id', 'market_type', 'point', 'selection'],
        as_index=False
    )
    
    # Statistics
    total_markets = len(grouped)
    events = markets_df['event_id'].nunique()
    spreads_count = len(markets_df[markets_df['market_type'] == 'spreads'])
    totals_count = len(markets_df[markets_df['market_type'] == 'totals'])
    
    print(f"Total Events: {events}")
    print(f"Total Market Points: {total_markets}")
    print(f"  - Spreads: {spreads_count} rows")
    print(f"  - Totals: {totals_count} rows")
    print(f"\n{'='*70}\n")
    
    # Display by event
    for event_id in markets_df['event_id'].unique():
        event_data = markets_df[markets_df['event_id'] == event_id]
        event_name = event_data['event_name'].iloc[0]
        
        print(f"\n📍 EVENT: {event_name}")
        print(f"   ID: {event_id}")
        print(f"   {'-'*65}")
        
        # Show spreads
        spreads = event_data[event_data['market_type'] == 'spreads']
        if len(spreads) > 0:
            print(f"\n   SPREADS:")
            for (point, selection), group in spreads.groupby(['point', 'selection']):
                # Get bookmakers with odds
                books_with_odds = group.dropna(subset=[col for col in group.columns if col not in 
                    ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 'market_type', 'point', 'selection']])
                
                num_books = len(books_with_odds.columns) - 8  # Subtract metadata columns
                print(f"      {selection:8} @ {point:5.1f}  →  {num_books:2} books available")
        
        # Show totals
        totals = event_data[event_data['market_type'] == 'totals']
        if len(totals) > 0:
            print(f"\n   TOTALS:")
            for (point, selection), group in totals.groupby(['point', 'selection']):
                num_books = len(group.columns) - 8
                print(f"      {selection:8} @ {point:6.1f}  →  {num_books:2} books available")
        
        print()
    
    print(f"\n{'='*70}")
    print(f"BOOKMAKER COVERAGE BY MARKET TYPE")
    print(f"{'='*70}\n")
    
    # Show which books appear in which markets
    all_bookmakers = [col for col in df.columns if col not in 
        ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 'market_type', 'point', 'selection']]
    
    for market_type in ['spreads', 'totals']:
        market_data = markets_df[markets_df['market_type'] == market_type]
        print(f"\n{market_type.upper()}:")
        print(f"  Total rows: {len(market_data)}")
        
        # Count non-null values per bookmaker
        book_coverage = {}
        for book in all_bookmakers:
            non_null = market_data[book].notna().sum()
            if non_null > 0:
                book_coverage[book] = non_null
        
        # Sort by coverage
        for book, count in sorted(book_coverage.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {book:25} {count:3} markets")
        
        if len(book_coverage) > 10:
            print(f"    ... and {len(book_coverage) - 10} more")
    
    print(f"\n{'='*70}\n")
    
    return markets_df

if __name__ == "__main__":
    csv_path = get_latest_csv()
    
    if not csv_path:
        print("❌ No CSV found in data/v3/extracts/")
        exit(1)
    
    print(f"\n📂 Loading: {Path(csv_path).name}")
    
    df = load_and_group_markets(csv_path)
