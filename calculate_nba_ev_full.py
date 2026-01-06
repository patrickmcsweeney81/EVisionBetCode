"""
NBA Fair Price & EV Calculation - FULL ANALYSIS VERSION (WITH DE-VIGGING)
==========================================================================
Calculates fair odds and EV using de-vigging for 2-way markets (spreads, totals, H2H).

Features:
- De-vigging for 2-way markets (removes bookmaker margin)
- Trimmed median reference for robust calculations
- Simple probability for single-outcome markets (player props)
- Keeps ALL bookmaker columns for detailed analysis

Usage:
    python calculate_nba_ev_full.py

Output:
    data/v3/extracts/basketball_nba_ev_full.csv
    (All original columns + fair_odds_decimal + best_au_odds_decimal + 
     best_au_bookmaker + ev_percent + uses_devig)
"""

import pandas as pd
import glob
import os
from datetime import datetime
import numpy as np

# Bookmaker groupings for fair odds calculation
# Use ALL books with weighted averaging by sharpness:
# 4⭐ (sharpest):    weight 1.5
# 3⭐ (sharp):       weight 1.0
# 2⭐ (soft):        weight 0.75  (trim 20% outliers first)
# 1⭐ (softest):     weight 0.5   (trim 20% outliers first)
SHARP_BOOKS_4STAR = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
SHARP_BOOKS_3STAR = ['betonlineag', 'betmgm', 'betrivers', 'fanatics']
SOFT_BOOKS_2STAR = ['hardrockbet', 'williamhill_us', 'bovada', 'espnbet']  # Soft/recreational
SOFT_BOOKS_1STAR = ['coolbet', 'fliff']  # Mentioned in data but low volume

# ALL books for fair odds (weighted by sharpness)
FAIR_ODDS_BOOKS = SHARP_BOOKS_4STAR + SHARP_BOOKS_3STAR + SOFT_BOOKS_2STAR + SOFT_BOOKS_1STAR  # 20 books total
BOOK_WEIGHTS = {}
for book in SHARP_BOOKS_4STAR:
    BOOK_WEIGHTS[book] = 1.5
for book in SHARP_BOOKS_3STAR:
    BOOK_WEIGHTS[book] = 1.0
for book in SOFT_BOOKS_2STAR:
    BOOK_WEIGHTS[book] = 0.75
for book in SOFT_BOOKS_1STAR:
    BOOK_WEIGHTS[book] = 0.5

# AU books for EV opportunities (0⭐)
AU_BOOKS = ['bet365', 'betfair_ex_au', 'sportsbet', 'dabble_au', 'pointsbetau', 
            'neds', 'ladbrokes_au', 'unibet', 'betright', 'betr_au', 'boombet', 
            'playup', 'tab', 'tabtouch']

# 2-way markets for de-vigging
TWO_WAY_MARKETS = {
    'totals': {'Over': 'Under', 'Under': 'Over'},
    'spreads': 'pair_with_other_team',  # Special: find opposite team in same event
    'h2h': 'pair_with_other_team',  # Special: find opposite team in same event
    # Player props - Over/Under are 2-way opposites
    'player_rebounds': {'Over': 'Under', 'Under': 'Over'},
    'player_points': {'Over': 'Under', 'Under': 'Over'},
    'player_assists': {'Over': 'Under', 'Under': 'Over'},
    'player_passes': {'Over': 'Under', 'Under': 'Over'},
    'player_tackles': {'Over': 'Under', 'Under': 'Over'},
    'player_goals': {'Over': 'Under', 'Under': 'Over'},
    'player_shots_on_target': {'Over': 'Under', 'Under': 'Over'},
}

def odds_to_implied_prob(decimal_odds):
    """Convert decimal odds to implied probability."""
    if pd.isna(decimal_odds) or decimal_odds <= 1:
        return np.nan
    return 1.0 / float(decimal_odds)

def devig_2way(p1_raw, p2_raw):
    """De-vig a 2-way market (remove bookmaker margin)."""
    if pd.isna(p1_raw) or pd.isna(p2_raw):
        return np.nan, np.nan
    
    overround = p1_raw + p2_raw
    if overround <= 0:
        return np.nan, np.nan
    
    return p1_raw / overround, p2_raw / overround

def get_opposite_selection(market_type, selection, event_id, df):
    """Get opposite selection for 2-way markets."""
    if market_type not in TWO_WAY_MARKETS:
        return None
    
    mapping = TWO_WAY_MARKETS[market_type]
    
    # If mapping is a dict (totals), use it
    if isinstance(mapping, dict):
        return mapping.get(selection)
    
    # If it's 'pair_with_other_team' (spreads/h2h), find the other team
    if mapping == 'pair_with_other_team':
        # Get all selections for this event and market
        event_rows = df[(df['event_id'] == event_id) & 
                        (df['market_type'] == market_type)]
        other_teams = event_rows[event_rows['selection'] != selection]['selection'].unique()
        return other_teams[0] if len(other_teams) > 0 else None
    
    return None

def is_2way_market(market_type):
    """Check if market is 2-way."""
    return market_type in TWO_WAY_MARKETS

def calculate_fair_odds(row, df):
    """
    Calculate fair odds using weighted average across ALL books:
    - 4⭐ sharp books: weight 1.5
    - 3⭐ sharp books: weight 1.0
    - 2⭐ soft books: weight 0.75 (with 20% trim on soft books)
    - 1⭐ soft books: weight 0.5 (with 20% trim on soft books)
    
    For 2-way markets: de-vig first, then weighted average.
    For single-outcome markets: simple weighted average of implied probabilities.
    Special handling for spreads: opposite team has negated point value.
    """
    available_books = [book for book in FAIR_ODDS_BOOKS if pd.notna(row[book])]
    
    if not available_books:
        return np.nan, False
    
    # Check if this is a 2-way market with available opposite
    market_type = row['market_type']
    uses_devig = False
    
    if is_2way_market(market_type):
        event_id = row['event_id']
        opposite_sel = get_opposite_selection(market_type, row['selection'], event_id, df)
        point = row.get('point', '')
        player = row.get('player_name', '')
        
        # Try to find opposite row
        # Special cases:
        # - spreads: opposite team has negated point, match by event_id
        # - player props: opposite selection (Under/Over), match by player_name + market_type + point
        # - totals/h2h: same point, opposite selection, match by event_id
        
        if market_type == 'spreads':
            # For spreads, opposite point is negated
            try:
                opposite_point = -float(point) if pd.notna(point) else ''
            except:
                opposite_point = point
            
            # Match opposite team with negated point
            opposite_rows = df[(df['event_id'] == event_id) & 
                               (df['market_type'] == market_type) & 
                               (df['selection'] == opposite_sel) &
                               ((df['point'] == opposite_point) | 
                                (df['point'].astype(str) == str(opposite_point)))]
        
        elif market_type.startswith('player_'):
            # For player props: match by player_name, market_type, point, opposite selection
            opposite_rows = df[(df['market_type'] == market_type) & 
                               (df['player_name'] == player) & 
                               (df['selection'] == opposite_sel) &
                               ((pd.isna(point) & pd.isna(df.get('point'))) | 
                                (df.get('point') == point))]
        
        else:
            # For totals/h2h: same point, opposite selection, match by event_id
            opposite_rows = df[(df['event_id'] == event_id) & 
                               (df['market_type'] == market_type) & 
                               (df['selection'] == opposite_sel) &
                               ((pd.isna(point) & pd.isna(df.get('point'))) | 
                                (df.get('point') == point))]
        
        if not opposite_rows.empty:
            opposite_row = opposite_rows.iloc[0]
            devig_probs = {}
            
            # De-vig all books (4⭐ + 3⭐ + 2⭐ + 1⭐) that have both sides
            for book in FAIR_ODDS_BOOKS:
                if book in available_books and pd.notna(opposite_row[book]):
                    p1_raw = odds_to_implied_prob(row[book])
                    p2_raw = odds_to_implied_prob(opposite_row[book])
                    
                    if pd.notna(p1_raw) and pd.notna(p2_raw):
                        p1_devig, _ = devig_2way(p1_raw, p2_raw)
                        if pd.notna(p1_devig):
                            devig_probs[book] = p1_devig
            
            if len(devig_probs) >= 1:
                # Separate sharp and soft books
                sharp_probs = {book: prob for book, prob in devig_probs.items() 
                              if book in SHARP_BOOKS_4STAR + SHARP_BOOKS_3STAR}
                soft_probs = {book: prob for book, prob in devig_probs.items() 
                             if book in SOFT_BOOKS_2STAR + SOFT_BOOKS_1STAR}
                
                # Trim 20% outliers from soft books only
                if len(soft_probs) >= 2:
                    soft_list = list(soft_probs.values())
                    sorted_soft = sorted(soft_list)
                    trim_count = max(1, int(len(sorted_soft) * 0.2))
                    trimmed_soft = sorted_soft[trim_count:-trim_count] if trim_count > 0 else sorted_soft
                    
                    # Reconstruct soft_probs with only trimmed values
                    trimmed_books = []
                    trimmed_values = set(trimmed_soft)
                    for book, prob in soft_probs.items():
                        if prob in trimmed_values:
                            trimmed_books.append(book)
                            trimmed_values.discard(prob)  # Avoid duplicates
                    soft_probs = {book: devig_probs[book] for book in trimmed_books}
                
                # Combine all devigged probs (sharp + trimmed soft)
                all_probs = {**sharp_probs, **soft_probs}
                
                if len(all_probs) >= 1:
                    # Weighted average
                    prob_list = list(all_probs.values())
                    weight_list = [BOOK_WEIGHTS[book] for book in all_probs.keys()]
                    fair_prob = np.average(prob_list, weights=weight_list)
                    
                    # Convert back to decimal odds
                    fair_decimal = 1.0 / fair_prob if fair_prob > 0 else np.nan
                    uses_devig = True
                    return fair_decimal, uses_devig
    
    # Fall back to weighted probability average for single-outcome markets
    probs = [odds_to_implied_prob(row[book]) for book in available_books]
    probs = [p for p in probs if pd.notna(p)]
    
    if probs:
        weights = [BOOK_WEIGHTS[book] for book in available_books if pd.notna(odds_to_implied_prob(row[book]))]
        fair_decimal = 1.0 / np.average(probs, weights=weights)
        return fair_decimal, uses_devig
    
    return np.nan, uses_devig

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
    """Calculate EV for filtered NBA data with de-vigging, keep all columns."""
    
    # Load filtered CSV
    filtered_csv = "data/v3/extracts/basketball_nba_filtered.csv"
    if not os.path.exists(filtered_csv):
        print("❌ No filtered NBA CSV found. Run filter_nba_v3.py first.")
        return
    
    print(f"📂 Loading filtered CSV: {filtered_csv}")
    
    df = pd.read_csv(filtered_csv)
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}\n")
    
    # Calculate fair odds and EV
    print("🧮 Calculating fair odds and EV (with de-vigging for 2-way markets)...")
    result = df.apply(lambda row: pd.Series(calculate_fair_odds(row, df)), axis=1)
    df['fair_odds_decimal'] = result[0]
    df['uses_devig'] = result[1]
    
    df['best_au_odds_decimal'] = df.apply(calculate_best_au_odds, axis=1)
    df['best_au_bookmaker'] = df.apply(get_best_au_bookmaker, axis=1)
    df['ev_percent'] = df.apply(lambda row: calculate_ev(row['fair_odds_decimal'], 
                                                          row['best_au_odds_decimal']), axis=1)
    
    # Get all bookmaker columns for counting (include soft books for reference)
    all_books = FAIR_ODDS_BOOKS + AU_BOOKS + SOFT_BOOKS_2STAR + SOFT_BOOKS_1STAR
    
    # Add total_books column
    df['total_books'] = df.apply(lambda row: count_available_books(row, all_books), axis=1)
    
    # Count valid EVs
    valid_evs = df['ev_percent'].notna().sum()
    print(f"✅ Calculated EV for {valid_evs:,} rows\n")
    
    # Format output columns for readability
    df['best_au_odds_formatted'] = df['best_au_odds_decimal'].apply(
        lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
    )
    # Round fair odds to 2 decimals
    df['Fair odds'] = df['fair_odds_decimal'].apply(
        lambda x: round(x, 2) if pd.notna(x) else np.nan
    )
    # Format EV as percentage
    df['EV'] = df['ev_percent'].apply(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
    )
    
    # Reorder columns: core → best AU book info → fair odds → all bookmakers
    core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
                 'market_type', 'point', 'selection', 'player_name']
    bookmaker_cols = [col for col in df.columns if col in all_books]
    
    # Build final column order with formatted display columns + de-vig flag (no numeric ev_percent)
    final_cols = (core_cols + 
                  ['best_au_bookmaker', 'best_au_odds_formatted', 'best_au_odds_decimal',
                   'EV', 'Fair odds',
                   'total_books', 'uses_devig'] + 
                  bookmaker_cols)
    df_output = df[final_cols].copy()
    
    # Save FULL version (all columns, reordered)
    os.makedirs("data/v3/extracts", exist_ok=True)
    output_csv_full = "data/v3/extracts/basketball_nba_ev_full.csv"
    
    # Write to temp file first, then move (handles locked files better)
    import shutil
    temp_file = output_csv_full + ".tmp"
    df_output.to_csv(temp_file, index=False)
    
    # Move temp file to final location
    try:
        if os.path.exists(output_csv_full):
            os.remove(output_csv_full)
    except:
        pass
    shutil.move(temp_file, output_csv_full)
    
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
