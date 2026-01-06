"""
NBA V3 Data Filtering
======================
Filters extracted NBA odds CSV to include only desired markets and formats.

Usage:
    python filter_nba_v3.py

Output:
    data/v3/filtered/basketball_nba_filtered_YYYYMMDD_HHMMSS.csv
"""

import pandas as pd
import glob
import os
from datetime import datetime

def filter_nba_data():
    """Load latest NBA_Raw CSV and create NBA_Filtered CSV with filters applied."""
    
    # Get latest NBA_Raw CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_raw_*.csv"))
    if not csv_files:
        print("❌ No NBA_Raw CSV files found in data/v3/extracts/")
        return
    
    latest_raw_csv = csv_files[-1]
    print(f"📂 Loading NBA_Raw: {latest_raw_csv}")
    
    df = pd.read_csv(latest_raw_csv)
    print(f"   Starting rows: {len(df):,}")
    
    # ============ APPLY FILTERS HERE ============
    
    # FILTER 1: Normalize market names (treat alternate_spreads same as spreads, etc.)
    df['market_type'] = df['market_type'].replace({
        'alternate_spreads': 'spreads',
        'alternate_totals': 'totals'
    })
    print(f"✅ After normalizing market names: {len(df):,} rows")
    
    # FILTER 2: Remove whole number spreads/totals (only keep .5 increments)
    # For spreads and totals, keep only lines with .5 values
    spreads_totals = df[df['market_type'].isin(['spreads', 'totals'])]
    other_markets = df[~df['market_type'].isin(['spreads', 'totals'])]
    
    # Filter spreads/totals to only .5 increments
    spreads_totals = spreads_totals[spreads_totals['point'] % 1 == 0.5]
    
    # Recombine
    df = pd.concat([spreads_totals, other_markets], ignore_index=True)
    print(f"✅ After removing whole number spreads/totals: {len(df):,} rows")
    
    # FILTER 3: Keep only lines with at least one sharp book
    sharp_books = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
    
    # Check if row has at least one sharp book with a value (not NaN)
    df['has_sharp_book'] = df[sharp_books].notna().any(axis=1)
    df = df[df['has_sharp_book']]
    df = df.drop('has_sharp_book', axis=1)
    print(f"✅ After keeping only lines with sharp books: {len(df):,} rows")
    
    # FILTER 4: Keep only lines with at least one AU bookmaker
    au_books = ['bet365', 'betfair_ex_au', 'sportsbet', 'dabble_au', 'pointsbetau', 
                'neds', 'ladbrokes_au', 'unibet', 'betright', 'betr_au', 'boombet', 
                'playup', 'tab', 'tabtouch']
    
    # Check if row has at least one AU book with a value (not NaN)
    df['has_au_book'] = df[au_books].notna().any(axis=1)
    df = df[df['has_au_book']]
    df = df.drop('has_au_book', axis=1)
    print(f"✅ After keeping only lines with AU books: {len(df):,} rows")
    
    # FILTER 5: Remove duplicate bets (same event + selection + point)
    # Now that spreads and alternate_spreads are named the same, 
    # they'll be grouped together and only first occurrence kept
    df = df.drop_duplicates(subset=['event_name', 'selection', 'point'], keep='first')
    print(f"✅ After removing all duplicate bets: {len(df):,} rows")
    
    # ============ END FILTERS ============
    
    # Save filtered CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/v3/extracts/basketball_nba_filtered_{timestamp}.csv"
    df.to_csv(output_csv, index=False)
    
    print(f"\n✅ NBA_Filtered CSV saved: {output_csv}")
    print(f"   Final rows: {len(df):,}")
    print(f"\nMarket breakdown:")
    print(df['market_type'].value_counts())
    
    return output_csv

if __name__ == "__main__":
    filter_nba_data()
