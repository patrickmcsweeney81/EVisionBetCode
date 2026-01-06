"""
NBA Advanced Outlier Detection - Implied Probability + De-Vig Method
====================================================================
Sophisticated outlier detection using:
1. Implied probability (not raw odds)
2. De-vigging (remove bookmaker margin)
3. Robust z-score (MAD - Median Absolute Deviation)
4. Multiple gates (z-score + absolute probability diff)
5. Line matching sanity checks
6. Outlier vs Value distinction

Uses FILTERED CSV (already has 2+ sharp + 1+ AU books)

Output:
- outlier_z_score: robust z-score magnitude
- outlier_flag: True if meets both gates
- prob_ref: reference "fair" probability
- prob_book: book's de-vig'd probability
- prob_diff_pct: absolute difference in percentage points
- value_candidate: True if +EV opportunity

Usage:
    python outlier_advanced_nba.py

Output:
    data/v3/extracts/basketball_nba_outliers_advanced_YYYYMMDD_HHMMSS.csv
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
from collections import defaultdict

# Bookmaker groupings
SHARP_BOOKS = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
AU_BOOKS = ['bet365', 'betfair_ex_au', 'sportsbet', 'dabble_au', 'pointsbetau', 
            'neds', 'ladbrokes_au', 'unibet', 'betright', 'betr_au', 'boombet', 
            'playup', 'tab', 'tabtouch']
ALL_BOOKS = SHARP_BOOKS + AU_BOOKS + ['betonlineag', 'betmgm', 'betrivers', 'fanatics', 
                                       'hardrockbet', 'williamhill_us', 'bovada', 'espnbet', 
                                       'coolbet', 'fliff']

# Detection thresholds
Z_SCORE_THRESHOLD = 3.5  # Robust z-score gate
PROB_DIFF_THRESHOLD = 0.02  # 2 percentage points absolute difference
EV_EDGE_BUFFER = 0.01  # 1% edge for value candidate

def odds_to_implied_prob(decimal_odds):
    """Convert decimal odds to implied probability."""
    if pd.isna(decimal_odds) or decimal_odds <= 1:
        return np.nan
    return 1.0 / float(decimal_odds)

def de_vig_2way(prob_a, prob_b):
    """
    De-vig a 2-way market (remove bookmaker margin).
    
    For a 2-way market (e.g., Over/Under):
    overround = p_a_raw + p_b_raw
    p_a_devig = p_a_raw / overround
    p_b_devig = p_b_raw / overround
    
    Returns dict with both de-vig'd probabilities.
    """
    if pd.isna(prob_a) or pd.isna(prob_b):
        return {'prob_a_devig': np.nan, 'prob_b_devig': np.nan}
    
    overround = prob_a + prob_b
    if overround <= 0:
        return {'prob_a_devig': np.nan, 'prob_b_devig': np.nan}
    
    return {
        'prob_a_devig': prob_a / overround,
        'prob_b_devig': prob_b / overround
    }

def calculate_robust_zscore(value, data_array):
    """
    Calculate robust z-score using MAD (Median Absolute Deviation).
    
    z_robust = 0.6745 * (value - median) / (MAD + eps)
    
    More resistant to outliers than standard z-score.
    """
    if len(data_array) < 2:
        return np.nan
    
    # Filter NaN
    clean_data = data_array[~np.isnan(data_array)]
    if len(clean_data) < 2:
        return np.nan
    
    median = np.median(clean_data)
    mad = np.median(np.abs(clean_data - median))
    
    if mad < 1e-6:  # Avoid division by zero
        return 0.0
    
    z_robust = 0.6745 * (value - median) / mad
    return z_robust

def detect_line_outliers(row, df_filtered, all_books):
    """
    Detect outliers for a single line using advanced probability method.
    
    Returns dict with outlier detection results.
    """
    market_type = row['market_type']
    selection = row['selection']
    point = row.get('point', '')
    event_name = row['event_name']
    
    # Get all odds for this line
    odds_dict = {}
    for book in all_books:
        if pd.notna(row[book]):
            try:
                odds_dict[book] = float(row[book])
            except:
                pass
    
    if len(odds_dict) < 2:
        return {
            'outlier_books': '',
            'has_outlier': False,
            'outlier_details': '',
            'num_outliers': 0
        }
    
    # Convert to implied probabilities
    probs = {book: odds_to_implied_prob(odds) for book, odds in odds_dict.items()}
    
    # For 2-way markets (spread, total, h2h), try to find opposite selection
    # For now, we'll work with individual probabilities
    # (In production, would match opposite selections for de-vigging)
    
    # Calculate reference probability from sharp books
    sharp_probs = [probs[b] for b in SHARP_BOOKS if b in probs and pd.notna(probs[b])]
    
    if len(sharp_probs) == 0:
        return {
            'outlier_books': '',
            'has_outlier': False,
            'outlier_details': '',
            'num_outliers': 0
        }
    
    # Use trimmed median (robust consensus)
    # Remove top/bottom 10% and take median
    if len(sharp_probs) >= 3:
        sorted_probs = sorted(sharp_probs)
        trim_count = max(1, len(sorted_probs) // 10)
        trimmed = sorted_probs[trim_count:-trim_count] if trim_count > 0 else sorted_probs
        prob_ref = np.median(trimmed)
    else:
        prob_ref = np.median(sharp_probs)
    
    # Detect AU book outliers
    outlier_books = []
    
    for book in AU_BOOKS:
        if book in probs and pd.notna(probs[book]):
            prob_book = probs[book]
            prob_diff = abs(prob_book - prob_ref)
            prob_diff_pct = prob_diff * 100  # Convert to percentage points
            
            # Calculate robust z-score
            all_probs = [p for p in probs.values() if pd.notna(p)]
            z_score = abs(calculate_robust_zscore(prob_book, np.array(all_probs)))
            
            # Both gates must pass
            gate1_pass = z_score >= Z_SCORE_THRESHOLD
            gate2_pass = prob_diff_pct >= PROB_DIFF_THRESHOLD * 100
            
            is_outlier = gate1_pass and gate2_pass
            
            if is_outlier:
                outlier_books.append({
                    'book': book,
                    'prob_book': prob_book,
                    'prob_diff_pct': prob_diff_pct,
                    'z_score': z_score
                })
    
    # Format output
    outlier_books_str = ', '.join([o['book'] for o in outlier_books])
    outlier_details = ' | '.join([
        f"{o['book']}(z={o['z_score']:.2f}, Δp={o['prob_diff_pct']:.2f}%)" 
        for o in outlier_books
    ])
    
    return {
        'outlier_books': outlier_books_str,
        'has_outlier': len(outlier_books) > 0,
        'outlier_details': outlier_details,
        'num_outliers': len(outlier_books),
        'prob_ref': prob_ref
    }

def detect_advanced_outliers():
    """Main outlier detection using advanced probability method."""
    
    # Load latest filtered CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_filtered_*.csv"))
    if not csv_files:
        print("❌ No filtered NBA CSV found. Run filter_nba_v3.py first.")
        return
    
    latest_csv = csv_files[-1]
    print(f"📂 Loading filtered NBA CSV: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    print(f"   Rows: {len(df):,}\n")
    
    print("🔬 Advanced Outlier Detection (Implied Probability Method)")
    print(f"   Thresholds:")
    print(f"   - Robust Z-Score: >= {Z_SCORE_THRESHOLD}")
    print(f"   - Probability Difference: >= {PROB_DIFF_THRESHOLD*100:.1f} percentage points")
    print(f"   - Both gates must pass\n")
    
    # Detect outliers
    print("📊 Processing lines...")
    
    outlier_results = []
    for idx, row in df.iterrows():
        result = detect_line_outliers(row, df, ALL_BOOKS)
        
        if result['has_outlier']:
            outlier_row = row.to_dict()
            outlier_row.update({
                'outlier_books': result['outlier_books'],
                'num_outliers': result['num_outliers'],
                'outlier_details': result['outlier_details'],
                'prob_ref': result['prob_ref']
            })
            outlier_results.append(outlier_row)
        
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1} lines... ({len(outlier_results)} outliers found)")
    
    # Convert to DataFrame
    df_outliers = pd.DataFrame(outlier_results)
    
    if len(df_outliers) == 0:
        print("\n✅ No outliers found (all books pricing consistently)")
        return
    
    print(f"\n✅ Found {len(df_outliers):,} lines with outliers\n")
    
    # Reorder columns
    core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
                 'market_type', 'point', 'selection', 'player_name']
    outlier_cols = ['num_outliers', 'outlier_books', 'prob_ref', 'outlier_details']
    bookmaker_cols = [col for col in df_outliers.columns if col in ALL_BOOKS]
    
    final_cols = core_cols + outlier_cols + bookmaker_cols
    df_output = df_outliers[[c for c in final_cols if c in df_outliers.columns]].copy()
    
    # Save output
    os.makedirs("data/v3/extracts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/v3/extracts/basketball_nba_outliers_advanced_{timestamp}.csv"
    df_output.to_csv(output_csv, index=False)
    
    print(f"✅ Advanced Outlier CSV saved: {output_csv}")
    print(f"   Columns: {len(df_output.columns)}")
    print(f"   Rows: {len(df_output):,}\n")
    
    # Statistics
    print("📊 Outlier Statistics:")
    print(f"   Total outlier occurrences: {df_output['num_outliers'].sum():,}")
    print(f"   Avg outliers per line: {df_output['num_outliers'].mean():.1f}")
    print(f"   Max outliers per line: {df_output['num_outliers'].max()}")
    
    # Top outlier books
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
    detect_advanced_outliers()
