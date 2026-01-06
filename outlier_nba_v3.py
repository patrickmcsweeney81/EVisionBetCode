"""
NBA Odds Spread Outlier Detection
==================================
Detects books offering unusually high/low odds compared to peers.

Uses raw odds data, filters to lines with 1+ sharp books AND 1+ AU books,
then identifies outliers where book odds deviate >2% from median.

Outputs CSV with all EV columns PLUS outlier detection columns.

Usage:
    python outlier_nba_v3.py

Output:
    data/v3/extracts/basketball_nba_outliers_YYYYMMDD_HHMMSS.csv
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
ALL_BOOKS = SHARP_BOOKS + AU_BOOKS + ['betonlineag', 'betmgm', 'betrivers', 'fanatics', 
                                       'hardrockbet', 'williamhill_us', 'bovada', 'espnbet', 
                                       'coolbet', 'fliff']

OUTLIER_THRESHOLD = 0.02  # Flag books that differ >2% from median decimal odds

def detect_odds_outliers(row, sharp_books, au_books):
    """
    Detect AU books offering unusually HIGH odds compared to sharp books.
    
    Only flags AU books with odds >2% above median sharp book odds.
    
    Returns dict with:
    - outlier_books: comma-separated list of AU book HIGH outliers
    - median_sharp_odds: median decimal odds from sharp books
    - num_outliers: count of AU book outliers
    - outlier_details: detailed breakdown
    """
    # Get sharp book odds (for fair market reference)
    sharp_odds = {}
    for book in sharp_books:
        if pd.notna(row[book]):
            try:
                odds = float(row[book])
                sharp_odds[book] = odds
            except:
                pass
    
    if len(sharp_odds) == 0:
        return {
            'outlier_books': '',
            'median_sharp_odds': np.nan,
            'num_outliers': 0,
            'outlier_details': ''
        }
    
    # Calculate median from sharp books (fair market)
    median_sharp = np.median(list(sharp_odds.values()))
    
    # Find AU books with HIGH odds (>2% above sharp median)
    au_outliers = []
    for book in au_books:
        if pd.notna(row[book]):
            try:
                odds = float(row[book])
                deviation = (odds - median_sharp) / median_sharp
                
                # Only flag HIGH outliers (odds > median by >2%)
                if deviation > OUTLIER_THRESHOLD:
                    au_outliers.append({
                        'book': book,
                        'odds': odds,
                        'deviation': deviation
                    })
            except:
                pass
    
    # Format output
    outlier_books = ', '.join([f"{o['book']}" for o in au_outliers])
    outlier_details = ' | '.join([f"{o['book']}:{o['odds']:.3f}(+{o['deviation']:.1%})" 
                                  for o in au_outliers])
    
    return {
        'outlier_books': outlier_books,
        'median_sharp_odds': median_sharp,
        'num_outliers': len(au_outliers),
        'outlier_details': outlier_details
    }

def detect_nba_outliers():
    """Detect odds outliers in raw NBA data."""
    
    # Load latest raw NBA CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_raw_*.csv"))
    if not csv_files:
        print("❌ No raw NBA CSV found. Run extract_nba_v3.py first.")
        return
    
    latest_csv = csv_files[-1]
    print(f"📂 Loading raw NBA CSV: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    print(f"   Rows: {len(df):,}\n")
    
    # Filter to lines with 2+ sharp books AND 1+ AU books
    print("🔍 Filtering to lines with 2+ sharp + 1+ AU books...")
    df['num_sharp_books'] = df[SHARP_BOOKS].notna().sum(axis=1)
    df['num_au_books'] = df[AU_BOOKS].notna().sum(axis=1)
    
    df_filtered = df[(df['num_sharp_books'] >= 2) & (df['num_au_books'] >= 1)].copy()
    print(f"   Starting rows: {len(df):,}")
    print(f"   After filtering: {len(df_filtered):,}\n")
    
    # Detect outliers - vectorized approach
    print("📊 Detecting odds spread outliers...")
    
    # Initialize result columns
    df_filtered['outlier_books'] = ''
    df_filtered['median_odds'] = np.nan
    df_filtered['num_outliers'] = 0
    df_filtered['outlier_details'] = ''
    
    # Process each row (optimized)
    for idx, row in df_filtered.iterrows():
        result = detect_odds_outliers(row, SHARP_BOOKS, AU_BOOKS)
        df_filtered.at[idx, 'outlier_books'] = result['outlier_books']
        df_filtered.at[idx, 'median_odds'] = result['median_sharp_odds']
        df_filtered.at[idx, 'num_outliers'] = result['num_outliers']
        df_filtered.at[idx, 'outlier_details'] = result['outlier_details']
        
        # Progress indicator every 500 rows
        if (idx + 1) % 500 == 0:
            print(f"   Processed {idx + 1} rows...")
    
    # Filter to only lines with outliers
    df_outliers = df_filtered[df_filtered['num_outliers'] > 0].copy()
    print(f"✅ Found {len(df_outliers):,} lines with outliers\n")
    
    # Reorder columns: core metadata + EV-style calcs + outlier columns + books
    core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
                 'market_type', 'point', 'selection', 'player_name']
    outlier_cols = ['num_outliers', 'outlier_books', 'median_odds', 'outlier_details']
    bookmaker_cols = [col for col in df_outliers.columns if col in ALL_BOOKS]
    
    final_cols = core_cols + outlier_cols + bookmaker_cols
    df_output = df_outliers[final_cols].copy()
    
    # Save output
    os.makedirs("data/v3/extracts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/v3/extracts/basketball_nba_outliers_{timestamp}.csv"
    df_output.to_csv(output_csv, index=False)
    
    print(f"✅ Outlier CSV saved: {output_csv}")
    print(f"   Columns: {len(df_output.columns)}")
    print(f"   Rows: {len(df_output):,}\n")
    
    # Statistics
    print("📊 Outlier Statistics:")
    print(f"   Total outlier occurrences: {df_output['num_outliers'].sum():,}")
    print(f"   Avg outliers per line: {df_output['num_outliers'].mean():.1f}")
    print(f"   Max outliers per line: {df_output['num_outliers'].max()}")
    
    # Top outlier books - parse from outlier_books column
    print(f"\n📈 Most Common Outlier Books:")
    all_outliers = []
    for books_str in df_output['outlier_books'].dropna():
        if books_str:
            all_outliers.extend([b.strip() for b in books_str.split(',')])
    
    from collections import Counter
    top_books = Counter(all_outliers)
    for book, count in top_books.most_common(10):
        print(f"   {book}: {count} times")
    
    return output_csv

if __name__ == "__main__":
    detect_nba_outliers()
