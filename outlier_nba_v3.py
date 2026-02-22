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

import glob
import os

import numpy as np
import pandas as pd

# Bookmaker groupings
SHARP_BOOKS = [
    'pinnacle',
    'betfair_ex_eu',
    'matchbook',
    'draftkings',
    'fanduel',
    'lowvig',
]
AU_BOOKS = [
    'bet365',
    'betfair_ex_au',
    'sportsbet',
    'dabble_au',
    'pointsbetau',
    'neds',
    'ladbrokes_au',
    'unibet',
    'betright',
    'betr_au',
    'boombet',
    'playup',
    'tab',
    'tabtouch',
]
ALL_BOOKS = SHARP_BOOKS + AU_BOOKS + [
    'betonlineag',
    'betmgm',
    'betrivers',
    'fanatics',
    'hardrockbet',
    'williamhill_us',
    'bovada',
    'espnbet',
    'coolbet',
    'fliff',
]

OUTLIER_THRESHOLD = 0.02  # Flag books that differ >2% from median decimal odds


def detect_odds_outliers(row, sharp_books, au_books):
    """
    Detect AU books offering unusually HIGH odds compared to sharp books.
    
    Only flags AU books with odds >2% above median sharp book odds.
    
    Returns dict with:
    - outlier_books: comma-separated list of AU book HIGH outliers
    - median_sharp_odds: median decimal odds from sharp books
    - num_outliers: count of AU book outliers
        - outlier_percent: max positive deviation vs sharp median (percent)
            e.g. 2.3 for +2.3%
    - outlier_details: detailed breakdown
    """
    # Get sharp book odds (for fair market reference)
    sharp_odds = {}
    for book in sharp_books:
        if pd.notna(row[book]):
            try:
                odds = float(row[book])
                sharp_odds[book] = odds
            except (TypeError, ValueError):
                pass
    
    if len(sharp_odds) == 0:
        return {
            'outlier_books': '',
            'median_sharp_odds': np.nan,
            'num_outliers': 0,
            'outlier_percent': np.nan,
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
            except (TypeError, ValueError):
                pass

    max_deviation = max((o['deviation'] for o in au_outliers), default=np.nan)
    
    # Format output
    outlier_books = ', '.join([f"{o['book']}" for o in au_outliers])
    outlier_details = ' | '.join(
        [
            f"{o['book']}:{o['odds']:.3f}(+{o['deviation']:.1%})"
            for o in au_outliers
        ]
    )
    
    return {
        'outlier_books': outlier_books,
        'median_sharp_odds': median_sharp,
        'num_outliers': len(au_outliers),
        'outlier_percent': (
            (max_deviation * 100.0) if pd.notna(max_deviation) else np.nan
        ),
        'outlier_details': outlier_details
    }


def detect_nba_outliers():
    """Detect odds outliers in raw NBA data."""
    
    # Load latest raw NBA CSV (prefer _new then main)
    candidates = [
        "data/v3/extracts/NBA_Raw_new.csv",
        "data/v3/extracts/NBA_Raw.csv",
        "data/v3/extracts/basketball_nba_raw.csv",
    ]
    latest_csv = next((c for c in candidates if os.path.exists(c)), None)
    if not latest_csv:
        legacy = sorted(glob.glob("data/v3/extracts/basketball_nba_raw_*.csv"))
        if legacy:
            latest_csv = legacy[-1]
    if not latest_csv:
        print("❌ No raw NBA CSV found. Run extract_nba_v3.py first.")
        return
    
    print(f"📂 Loading raw NBA CSV: {latest_csv}")
    print(f"📂 Loading raw NBA CSV: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    print(f"   Rows: {len(df):,}\n")
    
    # Filter to lines with 2+ sharp books AND 1+ AU books
    print("🔍 Filtering to lines with 2+ sharp + 1+ AU books...")
    df['num_sharp_books'] = df[SHARP_BOOKS].notna().sum(axis=1)
    df['num_au_books'] = df[AU_BOOKS].notna().sum(axis=1)
    
    df_filtered = df[
        (df['num_sharp_books'] >= 2) & (df['num_au_books'] >= 1)
    ].copy()
    print(f"   Starting rows: {len(df):,}")
    print(f"   After filtering: {len(df_filtered):,}\n")
    
    # Detect outliers - vectorized approach
    print("📊 Detecting odds spread outliers...")
    
    # Initialize result columns
    df_filtered['outlier_books'] = ''
    df_filtered['median_odds'] = np.nan
    df_filtered['num_outliers'] = 0
    df_filtered['outlier_percent'] = np.nan
    df_filtered['outlier_details'] = ''
    
    # Process each row (optimized)
    for idx, row in df_filtered.iterrows():
        result = detect_odds_outliers(row, SHARP_BOOKS, AU_BOOKS)
        df_filtered.at[idx, 'outlier_books'] = result['outlier_books']
        df_filtered.at[idx, 'median_odds'] = result['median_sharp_odds']
        df_filtered.at[idx, 'num_outliers'] = result['num_outliers']
        df_filtered.at[idx, 'outlier_percent'] = result['outlier_percent']
        df_filtered.at[idx, 'outlier_details'] = result['outlier_details']
        
        # Progress indicator every 500 rows
        if (idx + 1) % 500 == 0:
            print(f"   Processed {idx + 1} rows...")

    # Format for CSV output: keep median odds to 2 decimals
    df_filtered['median_odds'] = (
        pd.to_numeric(df_filtered['median_odds'], errors='coerce').round(2)
    )

    df_filtered['outlier_percent'] = pd.to_numeric(
        df_filtered['outlier_percent'], errors='coerce'
    ).round(1)

    df_filtered['outlier_percent'] = df_filtered['outlier_percent'].apply(
        lambda x: f"+{x:.1f}%" if pd.notna(x) else ''
    )
    
    # Filter to only lines with outliers
    df_outliers = df_filtered[df_filtered['num_outliers'] > 0].copy()
    print(f"✅ Found {len(df_outliers):,} lines with outliers\n")
    
    # Reorder columns: core metadata + EV-style calcs + outlier columns + books
    core_cols = [
        'event_id',
        'extracted_at',
        'commence_time',
        'league',
        'event_name',
        'market_type',
        'point',
        'selection',
        'player_name',
    ]
    outlier_cols = [
        'num_outliers',
        'outlier_books',
        'outlier_percent',
        'median_odds',
        'outlier_details',
    ]
    bookmaker_cols = [col for col in df_outliers.columns if col in ALL_BOOKS]
    
    final_cols = core_cols + outlier_cols + bookmaker_cols
    df_output = df_outliers[final_cols].copy()

    # Add sport and build combined all-sports outlier file
    df_output['sport'] = 'basketball_nba'
    normalized_cols = [
        'sport',
        'event_id',
        'extracted_at',
        'commence_time',
        'league',
        'event_name',
        'market_type',
        'point',
        'selection',
        'player_name',
        'num_outliers',
        'outlier_books',
        'outlier_percent',
        'median_odds',
        'outlier_details',
    ]
    normalized_cols = [c for c in normalized_cols if c in df_output.columns]
    normalized_cols_with_books = normalized_cols + [
        col for col in bookmaker_cols if col in df_output.columns
    ]
    df_all = df_output[normalized_cols_with_books].copy()
    
    # Save output
    os.makedirs("data/v3/extracts", exist_ok=True)
    output_csv = "data/v3/extracts/NBA_Outliers.csv"
    try:
        df_output.to_csv(output_csv, index=False)
    except PermissionError:
        output_csv = "data/v3/extracts/NBA_Outliers_new.csv"
        df_output.to_csv(output_csv, index=False)
        print(f"⚠️  Main file locked by backend, saved to: {output_csv}")
    else:
        print(f"✅ Outlier CSV saved: {output_csv}")

    combined_csv = "data/v3/extracts/AllSports_Outliers.csv"
    try:
        df_all.to_csv(combined_csv, index=False)
    except PermissionError:
        combined_csv = "data/v3/extracts/AllSports_Outliers_new.csv"
        df_all.to_csv(combined_csv, index=False)
        print(f"⚠️  Combined outliers locked, saved to: {combined_csv}")
    else:
        print(f"✅ All-sports Outlier CSV saved: {combined_csv}")

    print(f"   Columns: {len(df_output.columns)}")
    print(f"   Rows: {len(df_output):,}\n")
    
    # Statistics
    print("📊 Outlier Statistics:")
    print(f"   Total outlier occurrences: {df_output['num_outliers'].sum():,}")
    print(f"   Avg outliers per line: {df_output['num_outliers'].mean():.1f}")
    print(f"   Max outliers per line: {df_output['num_outliers'].max()}")
    
    # Top outlier books - parse from outlier_books column
    print("\n📈 Most Common Outlier Books:")
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
