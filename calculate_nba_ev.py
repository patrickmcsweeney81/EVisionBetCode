"""
NBA Fair Price & EV Calculation
================================
Calculates fair odds from sharp books and EV against AU books.

Sharp books (fair odds): pinnacle, betfair_ex_eu, matchbook, draftkings, fanduel, lowvig
AU books (target): bet365, betfair_ex_au, sportsbet, dabble_au, pointsbetau, neds, 
                   ladbrokes_au, unibet, betright, betr_au, boombet, playup, tab, tabtouch

Usage:
    python calculate_nba_ev.py

Output:
    data/v3/extracts/basketball_nba_ev_YYYYMMDD_HHMMSS.csv
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

# Odds in filtered CSV are already decimal - no conversion needed

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

def calculate_ev(fair_decimal, au_decimal):
    """Calculate EV as percentage."""
    if pd.isna(fair_decimal) or pd.isna(au_decimal):
        return np.nan
    
    # EV% = (Decimal Odds * Implied Probability) - 1
    # Where Implied Probability = 1 / Fair Odds
    implied_prob = 1 / fair_decimal
    ev_percent = (au_decimal * implied_prob) - 1
    return ev_percent * 100  # Convert to percentage

def calculate_nba_ev():
    """Calculate EV for filtered NBA data."""
    
    # Load latest filtered CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_filtered_*.csv"))
    if not csv_files:
        print("❌ No filtered NBA CSV found. Run filter_nba_v3.py first.")
        return
    
    latest_csv = csv_files[-1]
    print(f"📂 Loading filtered CSV: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    print(f"   Rows: {len(df):,}\n")
    
    # Calculate fair odds and EV
    print("🧮 Calculating fair odds and EV...")
    df['fair_odds_decimal'] = df.apply(calculate_fair_odds, axis=1)
    df['best_au_odds_decimal'] = df.apply(calculate_best_au_odds, axis=1)
    df['best_au_bookmaker'] = df.apply(get_best_au_bookmaker, axis=1)
    df['ev_percent'] = df.apply(lambda row: calculate_ev(row['fair_odds_decimal'], 
                                                          row['best_au_odds_decimal']), axis=1)
    
    # Count valid EVs
    valid_evs = df['ev_percent'].notna().sum()
    print(f"✅ Calculated EV for {valid_evs:,} rows\n")
    
    # Extract only essential columns for output
    output_cols = [
        'event_name', 'sport', 'market_type', 'selection', 'point',
        'fair_odds_decimal', 'best_au_odds_decimal', 'best_au_bookmaker', 'ev_percent'
    ]
    
    # Add sport column if not present (for single-sport CSVs)
    if 'sport' not in df.columns:
        df['sport'] = 'basketball_nba'
    
    df_output = df[output_cols].copy()
    
    # Save output
    os.makedirs("data/v3/extracts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/v3/extracts/basketball_nba_ev_{timestamp}.csv"
    df_output.to_csv(output_csv, index=False)
    
    print(f"✅ EV CSV saved: {output_csv}")
    print(f"\n📊 EV Statistics:")
    print(f"   Mean EV: {df['ev_percent'].mean():.2f}%")
    print(f"   Median EV: {df['ev_percent'].median():.2f}%")
    print(f"   Min EV: {df['ev_percent'].min():.2f}%")
    print(f"   Max EV: {df['ev_percent'].max():.2f}%")
    
    print(f"\n📈 Positive EV count: {(df['ev_percent'] > 0).sum():,}")
    print(f"   Negative EV count: {(df['ev_percent'] < 0).sum():,}")
    
    return output_csv

if __name__ == "__main__":
    calculate_nba_ev()
