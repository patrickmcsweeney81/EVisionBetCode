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
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_raw*.csv"))
    if not csv_files:
        print("❌ No NBA_Raw CSV files found in data/v3/extracts/")
        return
    
    latest_raw_csv = csv_files[-1]
    print(f"📂 Loading NBA_Raw: {latest_raw_csv}")
    
    df = pd.read_csv(latest_raw_csv)
    print(f"   Starting rows: {len(df):,}")
    
    # ============ APPLY FILTERS HERE ============
    
    # FILTER 1: Normalize market names - consolidate alternates by base market type
    # Map all variations (alternates, periods) to their base market type
    market_normalization = {
        # Spreads consolidation
        'alternate_spreads': 'spreads',
        'spreads_q1': 'spreads',
        'spreads_q2': 'spreads',
        'spreads_q3': 'spreads',
        'spreads_q4': 'spreads',
        'spreads_h1': 'spreads',
        'spreads_h2': 'spreads',
        
        # Totals consolidation
        'alternate_totals': 'totals',
        'alternate_totals_q1': 'totals',
        'alternate_totals_q2': 'totals',
        'alternate_totals_q3': 'totals',
        'alternate_totals_q4': 'totals',
        'alternate_totals_h1': 'totals',
        'alternate_totals_h2': 'totals',
        'totals_q1': 'totals',
        'totals_q2': 'totals',
        'totals_q3': 'totals',
        'totals_q4': 'totals',
        'totals_h1': 'totals',
        'totals_h2': 'totals',
        
        # Team totals consolidation
        'alternate_team_totals': 'team_totals',
        'alternate_team_totals_q1': 'team_totals',
        'alternate_team_totals_q2': 'team_totals',
        'alternate_team_totals_q3': 'team_totals',
        'alternate_team_totals_q4': 'team_totals',
        'alternate_team_totals_h1': 'team_totals',
        'alternate_team_totals_h2': 'team_totals',
        
        # Player props consolidation
        'player_points_alternate': 'player_points',
        'player_assists_alternate': 'player_assists',
        'player_rebounds_alternate': 'player_rebounds',
        'player_blocks_alternate': 'player_blocks',
        'player_steals_alternate': 'player_steals',
        'player_passes_alternate': 'player_passes',
        'player_tackles_alternate': 'player_tackles',
        'player_goals_alternate': 'player_goals',
        'player_shots_on_target_alternate': 'player_shots_on_target',
        
        # Player combo props consolidation
        'player_points_assists_alternate': 'player_points_assists',
        'player_points_rebounds_alternate': 'player_points_rebounds',
        'player_points_rebounds_assists_alternate': 'player_points_rebounds_assists',
        'player_rebounds_assists_alternate': 'player_rebounds_assists',
    }
    
    df['market_type'] = df['market_type'].replace(market_normalization)
    print(f"✅ After normalizing market names: {len(df):,} rows")
    
    # FILTER 2: Remove whole number spreads/totals (only keep .5 increments)
    # For spreads, totals, and team_totals, keep only lines with .5 values
    spread_total_markets = ['spreads', 'totals', 'team_totals']
    spread_total_rows = df[df['market_type'].isin(spread_total_markets)]
    other_markets = df[~df['market_type'].isin(spread_total_markets)]
    
    # Filter spreads/totals/team_totals to only .5 increments
    spread_total_rows = spread_total_rows[spread_total_rows['point'] % 1 == 0.5]
    
    # Recombine
    df = pd.concat([spread_total_rows, other_markets], ignore_index=True)
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
    
    # FILTER 5: Remove duplicate bets (same event + selection + point + player_name)
    # Now that spreads and alternate_spreads are named the same, 
    # they'll be grouped together and only first occurrence kept
    # For team_totals and player props, player_name distinguishes different bets
    df = df.drop_duplicates(subset=['event_name', 'market_type', 'selection', 'point', 'player_name'], keep='first')
    print(f"✅ After removing all duplicate bets: {len(df):,} rows")
    
    # ============ END FILTERS ============
    
    # Save filtered CSV - overwrites previous file
    output_csv = "data/v3/extracts/basketball_nba_filtered.csv"
    df.to_csv(output_csv, index=False)
    
    print(f"\n✅ NBA_Filtered CSV saved: {output_csv}")
    print(f"   Final rows: {len(df):,}")
    print(f"\nMarket breakdown:")
    print(df['market_type'].value_counts())
    
    return output_csv

if __name__ == "__main__":
    filter_nba_data()
