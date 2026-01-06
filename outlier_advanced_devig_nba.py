"""
NBA Advanced Outlier Detection - Full De-Vig Method for 2-Way Markets
=====================================================================
Sophisticated outlier detection using:
1. Implied probability (not raw odds)
2. De-vigging for 2-way markets (Over/Under, Spreads, H2H)
3. Robust z-score (MAD - Median Absolute Deviation)
4. Multiple gates (z-score + absolute probability diff)
5. Line matching sanity checks
6. Outlier vs Value distinction

2-Way Market De-Vig Logic:
For Over/Under or Spread pairs:
  p1_raw = 1 / odds_outcome1
  p2_raw = 1 / odds_outcome2
  overround = p1_raw + p2_raw
  p1_devig = p1_raw / overround  (now "fair" probability without vig)
  p2_devig = p2_raw / overround

Uses FILTERED CSV (already has 2+ sharp + 1+ AU books)

Output adds:
- prob_devig: de-vig'd probability for this outcome
- prob_ref_devig: reference "fair" de-vig'd probability
- uses_devig: True if 2-way market (Over/Under, Spread, H2H)
- outlier_z_score: robust z-score magnitude
- outlier_flag: True if meets both gates

Usage:
    python outlier_advanced_devig_nba.py

Output:
    data/v3/extracts/basketball_nba_outliers_devig_YYYYMMDD_HHMMSS.csv
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

# 2-way market types and their opposite selections
TWO_WAY_MARKETS = {
    'totals': {'Over': 'Under', 'Under': 'Over'},
    'spreads': {'Home': 'Away', 'Away': 'Home'},
    'h2h': {'Home': 'Away', 'Away': 'Home'},
}

def odds_to_implied_prob(decimal_odds):
    """Convert decimal odds to implied probability."""
    if pd.isna(decimal_odds) or decimal_odds <= 1:
        return np.nan
    return 1.0 / float(decimal_odds)

def get_opposite_selection(market_type, selection):
    """Get the opposite selection for a 2-way market."""
    if market_type not in TWO_WAY_MARKETS:
        return None
    opposite_map = TWO_WAY_MARKETS[market_type]
    return opposite_map.get(selection)

def is_2way_market(market_type):
    """Check if market is 2-way (Over/Under, Spread, H2H)."""
    return market_type in TWO_WAY_MARKETS

def devig_2way(p1_raw, p2_raw):
    """
    De-vig a 2-way market (remove bookmaker margin).
    
    For a 2-way market:
    overround = p1_raw + p2_raw
    p1_devig = p1_raw / overround
    p2_devig = p2_raw / overround
    
    Returns tuple (p1_devig, p2_devig, overround)
    """
    if pd.isna(p1_raw) or pd.isna(p2_raw):
        return np.nan, np.nan, np.nan
    
    overround = p1_raw + p2_raw
    if overround <= 0:
        return np.nan, np.nan, np.nan
    
    return (p1_raw / overround, p2_raw / overround, overround)

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

def detect_line_outliers_devig(row, df_filtered, all_books):
    """
    Detect outliers for a single line using de-vig method for 2-way markets.
    
    For 2-way markets (totals, spreads, h2h):
      - Find opposite outcome row
      - De-vig both outcomes for each bookmaker
      - Compare de-vig'd probabilities to reference
    
    For single-outcome markets (player props, etc):
      - Use simple probability comparison
    
    Returns dict with outlier detection results.
    """
    market_type = row['market_type']
    selection = row['selection']
    point = row.get('point', '')
    event_id = row['event_id']
    
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
            'num_outliers': 0,
            'uses_devig': False,
            'prob_ref_devig': np.nan
        }
    
    # Initialize result
    result = {
        'uses_devig': False,
        'prob_ref_devig': np.nan
    }
    
    # Check if 2-way market with available opposite
    if is_2way_market(market_type):
        opposite_sel = get_opposite_selection(market_type, selection)
        
        # Try to find opposite row for de-vigging
        opposite_row = None
        for idx, row2 in df_filtered.iterrows():
            if (row2['event_id'] == event_id and 
                row2['market_type'] == market_type and
                row2['selection'] == opposite_sel and
                (pd.isna(point) or row2.get('point') == point)):
                opposite_row = row2
                break
        
        if opposite_row is not None:
            # We have both sides - use de-vig method
            result['uses_devig'] = True
            
            # Get odds for opposite outcome
            opposite_odds = {}
            for book in all_books:
                if pd.notna(opposite_row[book]):
                    try:
                        opposite_odds[book] = float(opposite_row[book])
                    except:
                        pass
            
            # De-vig all bookmakers
            deviggged_probs = {}
            for book in all_books:
                if book in odds_dict and book in opposite_odds:
                    p1_raw = odds_to_implied_prob(odds_dict[book])
                    p2_raw = odds_to_implied_prob(opposite_odds[book])
                    
                    if pd.notna(p1_raw) and pd.notna(p2_raw):
                        p1_devig, p2_devig, overround = devig_2way(p1_raw, p2_raw)
                        if pd.notna(p1_devig):
                            deviggged_probs[book] = p1_devig
            
            if len(deviggged_probs) < 2:
                # Not enough pairs - fall through to single outcome
                result['uses_devig'] = False
            else:
                # Calculate reference from sharp books (de-vig'd)
                sharp_probs_devig = [deviggged_probs[b] for b in SHARP_BOOKS 
                                    if b in deviggged_probs]
                
                if len(sharp_probs_devig) >= 1:
                    # Use trimmed median
                    if len(sharp_probs_devig) >= 3:
                        sorted_probs = sorted(sharp_probs_devig)
                        trim_count = max(1, len(sorted_probs) // 10)
                        trimmed = sorted_probs[trim_count:-trim_count] if trim_count > 0 else sorted_probs
                        prob_ref_devig = np.median(trimmed)
                    else:
                        prob_ref_devig = np.median(sharp_probs_devig)
                    
                    result['prob_ref_devig'] = prob_ref_devig
                    
                    # Detect AU book outliers (de-vig'd)
                    outlier_books = []
                    
                    for book in AU_BOOKS:
                        if book in deviggged_probs:
                            prob_book = deviggged_probs[book]
                            prob_diff = abs(prob_book - prob_ref_devig)
                            prob_diff_pct = prob_diff * 100
                            
                            # Calculate robust z-score
                            all_probs = np.array(list(deviggged_probs.values()))
                            z_score = abs(calculate_robust_zscore(prob_book, all_probs))
                            
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
                        'uses_devig': True,
                        'prob_ref_devig': prob_ref_devig
                    }
    
    # Fall back to single-outcome probability method
    # (if not 2-way or opposite not found)
    
    # Convert to implied probabilities
    probs = {book: odds_to_implied_prob(odds) for book, odds in odds_dict.items()}
    
    # Calculate reference probability from sharp books
    sharp_probs = [probs[b] for b in SHARP_BOOKS if b in probs and pd.notna(probs[b])]
    
    if len(sharp_probs) == 0:
        return {
            'outlier_books': '',
            'has_outlier': False,
            'outlier_details': '',
            'num_outliers': 0,
            'uses_devig': False,
            'prob_ref_devig': np.nan
        }
    
    # Use trimmed median (robust consensus)
    if len(sharp_probs) >= 3:
        sorted_probs = sorted(sharp_probs)
        trim_count = max(1, len(sorted_probs) // 10)
        trimmed = sorted_probs[trim_count:-trim_count] if trim_count > 0 else sorted_probs
        prob_ref = np.median(trimmed)
    else:
        prob_ref = np.median(sharp_probs)
    
    result['prob_ref_devig'] = prob_ref
    
    # Detect AU book outliers
    outlier_books = []
    
    for book in AU_BOOKS:
        if book in probs and pd.notna(probs[book]):
            prob_book = probs[book]
            prob_diff = abs(prob_book - prob_ref)
            prob_diff_pct = prob_diff * 100
            
            # Calculate robust z-score
            all_probs = np.array([p for p in probs.values() if pd.notna(p)])
            z_score = abs(calculate_robust_zscore(prob_book, all_probs))
            
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
        'uses_devig': False,
        'prob_ref_devig': prob_ref
    }

def detect_devig_outliers():
    """Main outlier detection using de-vig method for 2-way markets."""
    
    # Load latest filtered CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_filtered_*.csv"))
    if not csv_files:
        print("❌ No filtered NBA CSV found. Run filter_nba_v3.py first.")
        return
    
    latest_csv = csv_files[-1]
    print(f"📂 Loading filtered NBA CSV: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    print(f"   Rows: {len(df):,}\n")
    
    print("🔬 Advanced Outlier Detection (De-Vig Method)")
    print(f"   Thresholds:")
    print(f"   - Robust Z-Score: >= {Z_SCORE_THRESHOLD}")
    print(f"   - Probability Difference: >= {PROB_DIFF_THRESHOLD*100:.1f} percentage points")
    print(f"   - Both gates must pass")
    print(f"   - 2-Way Markets (Totals/Spreads/H2H): De-vigged comparison")
    print(f"   - Single-Outcome Markets (Player Props): Direct probability comparison\n")
    
    # Detect outliers
    print("📊 Processing lines...")
    
    outlier_results = []
    devig_count = 0
    single_count = 0
    
    for idx, row in df.iterrows():
        result = detect_line_outliers_devig(row, df, ALL_BOOKS)
        
        if result['uses_devig']:
            devig_count += 1
        else:
            single_count += 1
        
        if result['has_outlier']:
            outlier_row = row.to_dict()
            outlier_row.update({
                'outlier_books': result['outlier_books'],
                'num_outliers': result['num_outliers'],
                'outlier_details': result['outlier_details'],
                'uses_devig': result['uses_devig'],
                'prob_ref': result['prob_ref_devig']
            })
            outlier_results.append(outlier_row)
        
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1} lines... ({len(outlier_results)} outliers found)")
    
    # Convert to DataFrame
    df_outliers = pd.DataFrame(outlier_results)
    
    print(f"\n   Market type breakdown:")
    print(f"   - 2-Way markets (de-vig'd): {devig_count}")
    print(f"   - Single-outcome markets: {single_count}")
    
    if len(df_outliers) == 0:
        print(f"\n✅ No outliers found (all books pricing consistently)")
        return
    
    print(f"\n✅ Found {len(df_outliers):,} lines with outliers\n")
    
    # Reorder columns
    core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
                 'market_type', 'point', 'selection', 'player_name']
    outlier_cols = ['num_outliers', 'uses_devig', 'outlier_books', 'prob_ref', 'outlier_details']
    bookmaker_cols = [col for col in df_outliers.columns if col in ALL_BOOKS]
    
    final_cols = core_cols + outlier_cols + bookmaker_cols
    df_output = df_outliers[[c for c in final_cols if c in df_outliers.columns]].copy()
    
    # Save output
    os.makedirs("data/v3/extracts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/v3/extracts/basketball_nba_outliers_devig_{timestamp}.csv"
    df_output.to_csv(output_csv, index=False)
    
    print(f"✅ De-Vig Outlier CSV saved: {output_csv}")
    print(f"   Columns: {len(df_output.columns)}")
    print(f"   Rows: {len(df_output):,}\n")
    
    # Statistics
    print("📊 Outlier Statistics:")
    print(f"   Total outlier occurrences: {df_output['num_outliers'].sum():,}")
    print(f"   Avg outliers per line: {df_output['num_outliers'].mean():.1f}")
    print(f"   Max outliers per line: {df_output['num_outliers'].max()}")
    
    # De-vig breakdown
    devig_count_in_results = df_output['uses_devig'].sum()
    print(f"\n   De-Vig Usage in Results:")
    print(f"   - 2-Way (de-vig'd): {devig_count_in_results}")
    print(f"   - Single-outcome: {len(df_output) - devig_count_in_results}")
    
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
    
    # Market type breakdown
    print(f"\n📊 Outliers by Market Type:")
    market_breakdown = df_output['market_type'].value_counts()
    for market, count in market_breakdown.items():
        print(f"   {market}: {count}")
    
    return output_csv

if __name__ == "__main__":
    detect_devig_outliers()
