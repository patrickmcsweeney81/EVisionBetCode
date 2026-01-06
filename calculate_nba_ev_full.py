"""
NBA Fair Price & EV Calculation - FULL ANALYSIS VERSION
========================================================
Calculates fair odds and EV, keeps ALL bookmaker columns for analysis.

Usage:
    python calculate_nba_ev_full.py

Output:
    data/v3/extracts/basketball_nba_ev_full_YYYYMMDD_HHMMSS.csv
    (All original columns + fair_odds_decimal + best_au_odds_decimal + 
     best_au_bookmaker + ev_percent)
"""

import pandas as pd
import glob
import os
from datetime import datetime
import numpy as np

# Bookmaker groupings
SHARP_BOOKS = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
AU_BOOKS = ['bet365', 'betfair_ex_au', 'sportsbet', 'dabble_au', 'pointsbetau', 
            'neds', 'ladbrokes_au', 'unibet', 'betright', 'betr_au', 'boombet', 
            'playup', 'tab', 'tabtouch']

def calculate_fair_odds(row):
    """Calculate fair odds from sharp books (simple average)."""
    sharp_odds = [row[book] for book in SHARP_BOOKS if pd.notna(row[book])]
    
    if not sharp_odds:
        return np.nan
    
    # Odds already decimal - just average them
    fair_decimal = np.mean(sharp_odds)
    return fair_decimal

def calculate_best_au_odds(row):
    """Get best odds from AU books."""
    au_odds = [row[book] for book in AU_BOOKS if pd.notna(row[book])]
    
    if not au_odds:
        return np.nan
    
    # Odds already decimal - just find maximum
    return max(au_odds)

def get_best_au_bookmaker(row):
    """Get name of AU bookmaker offering best odds."""
    best_odds = -1
    best_book = None
    
    for book in AU_BOOKS:
        if pd.notna(row[book]) and float(row[book]) > best_odds:
            best_odds = float(row[book])
            best_book = book
    
    return best_book if best_book else "N/A"

def count_available_books(row, all_books):
    """Count total number of bookmakers offering odds for this line."""
    return sum(1 for book in all_books if pd.notna(row[book]))

def calculate_ev(fair_decimal, au_decimal):
    """Calculate EV as percentage."""
    if pd.isna(fair_decimal) or pd.isna(au_decimal):
        return np.nan
    
    # EV% = (Decimal Odds * Implied Probability) - 1
    # Where Implied Probability = 1 / Fair Odds
    implied_prob = 1 / fair_decimal
    ev_percent = (au_decimal * implied_prob) - 1
    return ev_percent * 100  # Convert to percentage

def calculate_nba_ev_full():
    """Calculate EV for filtered NBA data, keep all columns."""
    
    # Load latest filtered CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_filtered_*.csv"))
    if not csv_files:
        print("❌ No filtered NBA CSV found. Run filter_nba_v3.py first.")
        return
    
    latest_csv = csv_files[-1]
    print(f"📂 Loading filtered CSV: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}\n")
    
    # Calculate fair odds and EV
    print("🧮 Calculating fair odds and EV...")
    df['fair_odds_decimal'] = df.apply(calculate_fair_odds, axis=1)
    df['best_au_odds_decimal'] = df.apply(calculate_best_au_odds, axis=1)
    df['best_au_bookmaker'] = df.apply(get_best_au_bookmaker, axis=1)
    df['ev_percent'] = df.apply(lambda row: calculate_ev(row['fair_odds_decimal'], 
                                                          row['best_au_odds_decimal']), axis=1)
    
    # Get all bookmaker columns for counting
    all_books = SHARP_BOOKS + AU_BOOKS + ['betonlineag', 'betmgm', 'betrivers', 'fanatics', 
                                           'hardrockbet', 'williamhill_us', 'bovada', 'espnbet', 
                                           'coolbet', 'fliff']
    
    # Add total_books column
    df['total_books'] = df.apply(lambda row: count_available_books(row, all_books), axis=1)
    
    # Count valid EVs
    valid_evs = df['ev_percent'].notna().sum()
    print(f"✅ Calculated EV for {valid_evs:,} rows\n")
    
    # Format output columns for readability
    df['best_au_odds_formatted'] = df['best_au_odds_decimal'].apply(
        lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
    )
    df['ev_percent_formatted'] = df['ev_percent'].apply(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
    )
    
    # Reorder columns: core → best AU book info → fair odds → all bookmakers
    core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
                 'market_type', 'point', 'selection', 'player_name']
    bookmaker_cols = [col for col in df.columns if col in all_books]
    
    # Build final column order with formatted display columns
    final_cols = (core_cols + 
                  ['best_au_bookmaker', 'best_au_odds_formatted', 'ev_percent_formatted', 
                   'total_books', 'fair_odds_decimal'] + 
                  bookmaker_cols)
    df_output = df[final_cols].copy()
    
    # Save FULL version (all columns, reordered)
    os.makedirs("data/v3/extracts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv_full = f"data/v3/extracts/basketball_nba_ev_full_{timestamp}.csv"
    df_output.to_csv(output_csv_full, index=False)
    
    print(f"✅ Full EV CSV saved: {output_csv_full}")
    print(f"   Columns: {len(df_output.columns)}")
    print(f"   Rows: {len(df):,}\n")
    
    # Print column summary
    print("📊 Column Breakdown:")
    print(f"   Core metadata: 9")
    print(f"   Best AU book info: 3 (best_au_bookmaker, best_au_odds_formatted [$], ev_percent_formatted [%])")
    print(f"   Market info: 2 (total_books, fair_odds_decimal)")
    print(f"   All Bookmakers: {len(bookmaker_cols)}")
    print(f"   Total columns: {len(df_output.columns)}")
    
    print(f"\n📊 EV Statistics:")
    print(f"   Mean EV: {df['ev_percent'].mean():.2f}%")
    print(f"   Median EV: {df['ev_percent'].median():.2f}%")
    print(f"   Min EV: {df['ev_percent'].min():.2f}%")
    print(f"   Max EV: {df['ev_percent'].max():.2f}%")
    
    print(f"\n📈 EV Distribution:")
    print(f"   Positive EV: {(df['ev_percent'] > 0).sum():,}")
    print(f"   Negative EV: {(df['ev_percent'] < 0).sum():,}")
    
    return output_csv_full

if __name__ == "__main__":
    calculate_nba_ev_full()
