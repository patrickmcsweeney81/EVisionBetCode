"""
NFL Fair Price & EV Calculation - FULL ANALYSIS VERSION (WITH DE-VIGGING)
==========================================================================
Calculates fair odds and EV using de-vigging for 2-way markets (spreads, totals, H2H).

Features:
- De-vigging for 2-way markets (removes bookmaker margin)
- Trimmed median reference for robust calculations
- Simple probability for single-outcome markets (player props)
- Keeps ALL bookmaker columns for detailed analysis

Usage:
    python calculate_nfl_ev_full.py

Output:
    data/v3/extracts/NFL_EV.csv
    (All original columns + fair_odds_decimal + best_au_odds_decimal + 
     best_au_bookmaker + ev_percent + uses_devig)
"""

import pandas as pd
import glob
import os
import sys
import subprocess
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
    # Main markets
    'totals': {'Over': 'Under', 'Under': 'Over'},
    'spreads': 'pair_with_other_team',
    'h2h': 'pair_with_other_team',
    'h2h_lay': 'pair_with_other_team',
    'team_totals': {'Over': 'Under', 'Under': 'Over'},

    # Alternate / period markets
    'alternate_spreads': 'pair_with_other_team',
    'alternate_totals': {'Over': 'Under', 'Under': 'Over'},
    'alternate_team_totals': {'Over': 'Under', 'Under': 'Over'},
    'first_half_spreads': 'pair_with_other_team',
    'first_half_totals': {'Over': 'Under', 'Under': 'Over'},
    'first_half_team_totals': {'Over': 'Under', 'Under': 'Over'},

    # Player props (Over/Under or Yes/No)
    'player_pass_yds': {'Over': 'Under', 'Under': 'Over'},
    'player_pass_tds': {'Over': 'Under', 'Under': 'Over'},
    'player_pass_completions': {'Over': 'Under', 'Under': 'Over'},
    'player_pass_longest_completion': {'Over': 'Under', 'Under': 'Over'},
    'player_pass_attempts': {'Over': 'Under', 'Under': 'Over'},
    'player_rush_yds': {'Over': 'Under', 'Under': 'Over'},
    'player_rush_attempts': {'Over': 'Under', 'Under': 'Over'},
    'player_rush_longest': {'Over': 'Under', 'Under': 'Over'},
    'player_receptions': {'Over': 'Under', 'Under': 'Over'},
    'player_receiving_yds': {'Over': 'Under', 'Under': 'Over'},
    'player_td_anytime': {'Yes': 'No', 'No': 'Yes'},
    'player_field_goals': {'Over': 'Under', 'Under': 'Over'},
    'player_kicking_points': {'Over': 'Under', 'Under': 'Over'},
}

def odds_to_implied_prob(decimal_odds):
    """Convert decimal odds to implied probability."""
    if pd.isna(decimal_odds) or decimal_odds <= 1:
        return np.nan
    return 1.0 / float(decimal_odds)

def remove_betfair_commission(decimal_odds, commission_rate=0.06):
    """
    Remove Betfair's commission from odds to get true market probability.
    
    Betfair is an exchange - odds already include commission impact.
    Commission typically 5-6% (default 6%).
    
    Formula: true_odds = decimal_odds / (1 - commission_rate)
    
    Example:
        Betfair odds: 1.90
        Commission: 6%
        True odds: 1.90 / 0.94 = 2.02
    """
    if pd.isna(decimal_odds) or decimal_odds <= 1:
        return decimal_odds
    
    return decimal_odds / (1 - commission_rate)

def devig_2way(p1_raw, p2_raw):
    """De-vig a 2-way market (remove bookmaker margin)."""
    if pd.isna(p1_raw) or pd.isna(p2_raw):
        return np.nan, np.nan
    
    overround = p1_raw + p2_raw
    if overround <= 0:
        return np.nan, np.nan
    
    return p1_raw / overround, p2_raw / overround

def is_mad_outlier(value, data_list, threshold=2.5):
    """
    Detect if a value is an outlier using Median Absolute Deviation (MAD).
    
    MAD = median(|x_i - median(x)|)
    A value is an outlier if: |value - median| > threshold * MAD
    
    threshold=2.5 is equivalent to ~2.5 standard deviations for normal distribution
    (more lenient than 2.0, less strict than 3.0)
    """
    if len(data_list) < 3:
        return False
    
    data_array = np.array(data_list)
    median = np.median(data_array)
    mad = np.median(np.abs(data_array - median))
    
    # Avoid division by zero
    if mad == 0:
        return False
    
    # Check if this value is an outlier
    is_outlier = abs(value - median) > threshold * mad
    return is_outlier

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
    Calculate fair odds using weighted average across ALL books with MAD-based outlier detection:
    
    4⭐ sharp books: weight 1.5
      - Almost never auto-remove (preserves best data)
      - Only remove if BOTH: MAD outlier AND conflicts with other 4⭐/3⭐ consensus
    
    3⭐ sharp books: weight 1.0
      - Keep unless MAD outlier (statistically extreme)
    
    2⭐ soft books: weight 0.75
      - Keep but downweight; remove if MAD outlier
    
    1⭐ soft books: weight 0.5
      - Keep but downweight; remove if MAD outlier
    
    Outlier Detection: Median Absolute Deviation (MAD)
      - More robust than % trim (doesn't assume linear scaling)
      - threshold=2.5 equivalent to ~2.5 std devs (lenient on noise)
      - Adaptive to actual disagreement in data
    
    For 2-way markets: de-vig first, then weighted average.
    For single-outcome markets: simple weighted average of implied probabilities.
    """
    available_books = [book for book in FAIR_ODDS_BOOKS if pd.notna(row[book])]
    
    if not available_books:
        return np.nan, False
    
    # Check if this is a 2-way market with available opposite
    market_type = row['market_type']
    uses_devig = False
    
    if is_2way_market(market_type):
        # USE PAIR_ID for reliable pairing (already validated during filter stage)
        pair_id = row.get('pair_id')
        
        # If pair_id exists, find opposite row using pair_id
        if pd.notna(pair_id):
            # Find the opposite row in the same pair (pair_id matches, but different row)
            same_pair = df[df['pair_id'] == pair_id]
            opposite_rows = same_pair[same_pair.index != row.name]
        else:
            # Fallback to old logic if pair_id not available (shouldn't happen with filtered data)
            event_id = row['event_id']
            opposite_sel = get_opposite_selection(market_type, row['selection'], event_id, df)
            point = row.get('point', '')
            player = row.get('player_name', '')
            
            # Try to find opposite row
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
                    # Remove Betfair commission if using Betfair exchange
                    odds_1 = row[book]
                    odds_2 = opposite_row[book]
                    
                    if book == 'betfair_ex_eu':
                        odds_1 = remove_betfair_commission(odds_1, commission_rate=0.06)
                        odds_2 = remove_betfair_commission(odds_2, commission_rate=0.06)
                    
                    p1_raw = odds_to_implied_prob(odds_1)
                    p2_raw = odds_to_implied_prob(odds_2)
                    
                    if pd.notna(p1_raw) and pd.notna(p2_raw):
                        p1_devig, _ = devig_2way(p1_raw, p2_raw)
                        if pd.notna(p1_devig):
                            devig_probs[book] = p1_devig
            
            if len(devig_probs) >= 1:
                # Separate by rating for MAD-based outlier detection
                probs_4star = {book: prob for book, prob in devig_probs.items() 
                              if book in SHARP_BOOKS_4STAR}
                probs_3star = {book: prob for book, prob in devig_probs.items() 
                              if book in SHARP_BOOKS_3STAR}
                probs_2star = {book: prob for book, prob in devig_probs.items() 
                             if book in SOFT_BOOKS_2STAR}
                probs_1star = {book: prob for book, prob in devig_probs.items() 
                             if book in SOFT_BOOKS_1STAR}
                
                # MAD-based outlier detection with rating-specific logic
                final_probs = {}
                
                # 4⭐: Almost never auto-remove; only if extreme MAD outlier AND conflicts with other 4⭐/3⭐
                if len(probs_4star) > 0:
                    consensus_4_3 = np.median(list(probs_4star.values()) + list(probs_3star.values())) if (probs_4star or probs_3star) else None
                    
                    for book, prob in probs_4star.items():
                        # Only remove if BOTH: MAD outlier AND conflicts with 4⭐/3⭐ consensus
                        all_4star_probs = list(probs_4star.values())
                        is_mad_out = is_mad_outlier(prob, all_4star_probs, threshold=2.5) if len(all_4star_probs) >= 3 else False
                        
                        if consensus_4_3 is not None:
                            conflicts_consensus = abs(prob - consensus_4_3) > 0.03  # 3% disagreement = conflict
                        else:
                            conflicts_consensus = False
                        
                        # Only remove if BOTH conditions met AND we have backup 4/3 star books
                        should_remove = is_mad_out and conflicts_consensus and len(probs_4star) > 1
                        
                        if not should_remove:
                            final_probs[book] = prob
                
                # 3⭐: Keep unless MAD outlier
                if len(probs_3star) > 0:
                    all_3star_probs = list(probs_3star.values())
                    for book, prob in probs_3star.items():
                        is_mad_out = is_mad_outlier(prob, all_3star_probs, threshold=2.5) if len(all_3star_probs) >= 3 else False
                        if not is_mad_out:
                            final_probs[book] = prob
                
                # 2⭐: Keep but downweight; remove if MAD outlier
                if len(probs_2star) > 0:
                    all_2star_probs = list(probs_2star.values())
                    for book, prob in probs_2star.items():
                        is_mad_out = is_mad_outlier(prob, all_2star_probs, threshold=2.5) if len(all_2star_probs) >= 3 else False
                        if not is_mad_out:
                            final_probs[book] = prob
                
                # 1⭐: Keep but downweight; remove if MAD outlier (rare to have many 1⭐)
                if len(probs_1star) > 0:
                    all_1star_probs = list(probs_1star.values())
                    for book, prob in probs_1star.items():
                        is_mad_out = is_mad_outlier(prob, all_1star_probs, threshold=2.5) if len(all_1star_probs) >= 2 else False
                        if not is_mad_out:
                            final_probs[book] = prob
                
                if len(final_probs) >= 1:
                    # Weighted average
                    prob_list = list(final_probs.values())
                    weight_list = [BOOK_WEIGHTS[book] for book in final_probs.keys()]
                    fair_prob = np.average(prob_list, weights=weight_list)
                    
                    # Convert back to decimal odds
                    fair_decimal = 1.0 / fair_prob if fair_prob > 0 else np.nan
                    uses_devig = True
                    return fair_decimal, uses_devig
    
    # Fall back to weighted probability average for single-outcome markets
    probs_single = {}
    for book in available_books:
        odds = row[book]
        # Remove Betfair commission if using Betfair exchange
        if book == 'betfair_ex_eu':
            odds = remove_betfair_commission(odds, commission_rate=0.06)
        prob = odds_to_implied_prob(odds)
        if pd.notna(prob):
            probs_single[book] = prob
    
    if probs_single:
        probs = list(probs_single.values())
        weights = [BOOK_WEIGHTS[book] for book in probs_single.keys()]
        fair_decimal = 1.0 / np.average(probs, weights=weights)
        return fair_decimal, uses_devig
    
    return np.nan, uses_devig


def calculate_fair_odds_fast(row, df, pair_lookup):
    """
    Fast version using pre-built pair_lookup (avoids repeated dataframe lookups).
    """
    available_books = [book for book in FAIR_ODDS_BOOKS if pd.notna(row[book])]
    
    if not available_books:
        return np.nan, False
    
    # Check if this is a 2-way market with available opposite
    market_type = row['market_type']
    uses_devig = False
    
    if is_2way_market(market_type):
        # USE PAIR_ID for reliable pairing (already validated during filter stage)
        pair_id = row.get('pair_id')
        
        # If pair_id exists, find opposite row using pair_lookup
        if pd.notna(pair_id) and pair_id in pair_lookup:
            pair_indices = pair_lookup[pair_id]
            # Find the other row in this pair
            opposite_idx = [idx for idx in pair_indices if idx != row.name]
            
            if opposite_idx:
                opposite_row = df.loc[opposite_idx[0]]
                devig_probs = {}
                
                # De-vig all books (4⭐ + 3⭐ + 2⭐ + 1⭐) that have both sides
                for book in FAIR_ODDS_BOOKS:
                    if book in available_books and pd.notna(opposite_row[book]):
                        # Remove Betfair commission if using Betfair exchange
                        odds_1 = row[book]
                        odds_2 = opposite_row[book]
                        
                        if book == 'betfair_ex_eu':
                            odds_1 = remove_betfair_commission(odds_1, commission_rate=0.06)
                            odds_2 = remove_betfair_commission(odds_2, commission_rate=0.06)
                        
                        p1_raw = odds_to_implied_prob(odds_1)
                        p2_raw = odds_to_implied_prob(odds_2)
                        
                        if pd.notna(p1_raw) and pd.notna(p2_raw):
                            p1_devig, _ = devig_2way(p1_raw, p2_raw)
                            if pd.notna(p1_devig):
                                devig_probs[book] = p1_devig
                
                if len(devig_probs) >= 1:
                    # Use weighted average directly (skip MAD outlier detection for speed)
                    prob_list = list(devig_probs.values())
                    weight_list = [BOOK_WEIGHTS[book] for book in devig_probs.keys()]
                    fair_prob = np.average(prob_list, weights=weight_list)
                    
                    # Convert back to decimal odds
                    fair_decimal = 1.0 / fair_prob if fair_prob > 0 else np.nan
                    uses_devig = True
                    return fair_decimal, uses_devig
    
    # Fall back to weighted probability average for single-outcome markets
    probs_single = {}
    for book in available_books:
        odds = row[book]
        # Remove Betfair commission if using Betfair exchange
        if book == 'betfair_ex_eu':
            odds = remove_betfair_commission(odds, commission_rate=0.06)
        prob = odds_to_implied_prob(odds)
        if pd.notna(prob):
            probs_single[book] = prob
    
    if probs_single:
        probs = list(probs_single.values())
        weights = [BOOK_WEIGHTS[book] for book in probs_single.keys()]
        fair_decimal = 1.0 / np.average(probs, weights=weights)
        return fair_decimal, uses_devig
    
    return np.nan, uses_devig

def calculate_best_au_odds(row):
    """
    Calculate fair odds using weighted average across ALL books with MAD-based outlier detection:
    
    4⭐ sharp books: weight 1.5
      - Almost never auto-remove (preserves best data)
      - Only remove if BOTH: MAD outlier AND conflicts with other 4⭐/3⭐ consensus
    
    3⭐ sharp books: weight 1.0
      - Keep unless MAD outlier (statistically extreme)
    
    2⭐ soft books: weight 0.75
      - Keep but downweight; remove if MAD outlier
    
    1⭐ soft books: weight 0.5
      - Keep but downweight; remove if MAD outlier
    
    Outlier Detection: Median Absolute Deviation (MAD)
      - More robust than % trim (doesn't assume linear scaling)
      - threshold=2.5 equivalent to ~2.5 std devs (lenient on noise)
      - Adaptive to actual disagreement in data
    
    For 2-way markets: de-vig first, then weighted average.
    For single-outcome markets: simple weighted average of implied probabilities.
    """
    available_books = [book for book in FAIR_ODDS_BOOKS if pd.notna(row[book])]
    
    if not available_books:
        return np.nan, False
    
    # Check if this is a 2-way market with available opposite
    market_type = row['market_type']
    uses_devig = False
    
    if is_2way_market(market_type):
        # USE PAIR_ID for reliable pairing (already validated during filter stage)
        pair_id = row.get('pair_id')
        
        # If pair_id exists, find opposite row using pair_id
        if pd.notna(pair_id):
            # Find the opposite row in the same pair (pair_id matches, but different row)
            same_pair = df[df['pair_id'] == pair_id]
            opposite_rows = same_pair[same_pair.index != row.name]
        else:
            # Fallback to old logic if pair_id not available (shouldn't happen with filtered data)
            event_id = row['event_id']
            opposite_sel = get_opposite_selection(market_type, row['selection'], event_id, df)
            point = row.get('point', '')
            player = row.get('player_name', '')
            
            # Try to find opposite row
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
                    # Remove Betfair commission if using Betfair exchange
                    odds_1 = row[book]
                    odds_2 = opposite_row[book]
                    
                    if book == 'betfair_ex_eu':
                        odds_1 = remove_betfair_commission(odds_1, commission_rate=0.06)
                        odds_2 = remove_betfair_commission(odds_2, commission_rate=0.06)
                    
                    p1_raw = odds_to_implied_prob(odds_1)
                    p2_raw = odds_to_implied_prob(odds_2)
                    
                    if pd.notna(p1_raw) and pd.notna(p2_raw):
                        p1_devig, _ = devig_2way(p1_raw, p2_raw)
                        if pd.notna(p1_devig):
                            devig_probs[book] = p1_devig
            
            if len(devig_probs) >= 1:
                # Separate by rating for MAD-based outlier detection
                probs_4star = {book: prob for book, prob in devig_probs.items() 
                              if book in SHARP_BOOKS_4STAR}
                probs_3star = {book: prob for book, prob in devig_probs.items() 
                              if book in SHARP_BOOKS_3STAR}
                probs_2star = {book: prob for book, prob in devig_probs.items() 
                             if book in SOFT_BOOKS_2STAR}
                probs_1star = {book: prob for book, prob in devig_probs.items() 
                             if book in SOFT_BOOKS_1STAR}
                
                # MAD-based outlier detection with rating-specific logic
                final_probs = {}
                
                # 4⭐: Almost never auto-remove; only if extreme MAD outlier AND conflicts with other 4⭐/3⭐
                if len(probs_4star) > 0:
                    consensus_4_3 = np.median(list(probs_4star.values()) + list(probs_3star.values())) if (probs_4star or probs_3star) else None
                    
                    for book, prob in probs_4star.items():
                        # Only remove if BOTH: MAD outlier AND conflicts with 4⭐/3⭐ consensus
                        all_4star_probs = list(probs_4star.values())
                        is_mad_out = is_mad_outlier(prob, all_4star_probs, threshold=2.5) if len(all_4star_probs) >= 3 else False
                        
                        if consensus_4_3 is not None:
                            conflicts_consensus = abs(prob - consensus_4_3) > 0.03  # 3% disagreement = conflict
                        else:
                            conflicts_consensus = False
                        
                        # Only remove if BOTH conditions met AND we have backup 4/3 star books
                        should_remove = is_mad_out and conflicts_consensus and len(probs_4star) > 1
                        
                        if not should_remove:
                            final_probs[book] = prob
                
                # 3⭐: Keep unless MAD outlier
                if len(probs_3star) > 0:
                    all_3star_probs = list(probs_3star.values())
                    for book, prob in probs_3star.items():
                        is_mad_out = is_mad_outlier(prob, all_3star_probs, threshold=2.5) if len(all_3star_probs) >= 3 else False
                        if not is_mad_out:
                            final_probs[book] = prob
                
                # 2⭐: Keep but downweight; remove if MAD outlier
                if len(probs_2star) > 0:
                    all_2star_probs = list(probs_2star.values())
                    for book, prob in probs_2star.items():
                        is_mad_out = is_mad_outlier(prob, all_2star_probs, threshold=2.5) if len(all_2star_probs) >= 3 else False
                        if not is_mad_out:
                            final_probs[book] = prob
                
                # 1⭐: Keep but downweight; remove if MAD outlier (rare to have many 1⭐)
                if len(probs_1star) > 0:
                    all_1star_probs = list(probs_1star.values())
                    for book, prob in probs_1star.items():
                        is_mad_out = is_mad_outlier(prob, all_1star_probs, threshold=2.5) if len(all_1star_probs) >= 2 else False
                        if not is_mad_out:
                            final_probs[book] = prob
                
                if len(final_probs) >= 1:
                    # Weighted average
                    prob_list = list(final_probs.values())
                    weight_list = [BOOK_WEIGHTS[book] for book in final_probs.keys()]
                    fair_prob = np.average(prob_list, weights=weight_list)
                    
                    # Convert back to decimal odds
                    fair_decimal = 1.0 / fair_prob if fair_prob > 0 else np.nan
                    uses_devig = True
                    return fair_decimal, uses_devig
    
    # Fall back to weighted probability average for single-outcome markets
    probs_single = {}
    for book in available_books:
        odds = row[book]
        # Remove Betfair commission if using Betfair exchange
        if book == 'betfair_ex_eu':
            odds = remove_betfair_commission(odds, commission_rate=0.06)
        prob = odds_to_implied_prob(odds)
        if pd.notna(prob):
            probs_single[book] = prob
    
    if probs_single:
        probs = list(probs_single.values())
        weights = [BOOK_WEIGHTS[book] for book in probs_single.keys()]
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

def calculate_nfl_ev_full():
    """Calculate EV for filtered NFL data with de-vigging, keep all columns."""
    
    print("[INIT] EV Calculation Pipeline for NFL")
    print()

    # Manage AllSports_EV: archive previous runs, cleanup old files
    print("[MANAGE] Archiving previous runs and cleaning up old files...")
    try:
        result = subprocess.run(
            [sys.executable, "manage_allsports_ev.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            print(f"[WARN] Management script error: {result.stderr}")
    except Exception as e:
        print(f"[WARN] Could not run management script: {e}")
    print()
    
    # Load filtered CSV (prefer NFL_Filtered_new then NFL_Filtered)
    candidates = [
        "data/v3/extracts/NFL_Filtered_new.csv",
        "data/v3/extracts/NFL_Filtered.csv",
    ]
    filtered_csv = next((c for c in candidates if os.path.exists(c)), None)
    if not filtered_csv:
        legacy = sorted(glob.glob("data/v3/extracts/NFL_Filtered*.csv"))
        if legacy:
            filtered_csv = legacy[-1]
    if not filtered_csv:
        print("[ERROR] No filtered NFL CSV found. Run filter_nfl_v3.py first.")
        return
    
    print(f"[*] Loading filtered CSV: {filtered_csv}")
    
    df = pd.read_csv(filtered_csv)
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}\n")
    
    # PRE-BUILD pair_id lookup to speed up calculations (avoids repeated df lookups)
    print("[PREP] Building pair_id lookup table...")
    pair_lookup = {}
    for idx, row in df.iterrows():
        pair_id = row['pair_id']
        if pd.notna(pair_id):
            if pair_id not in pair_lookup:
                pair_lookup[pair_id] = []
            pair_lookup[pair_id].append(idx)
    print(f"[OK] Pair lookup built: {len(pair_lookup):,} unique pairs\n")
    
    # Calculate fair odds and EV
    print("[CALC] Calculating fair odds and EV (with de-vigging for 2-way markets)...")
    
    # Use iterrows with pair_lookup for faster access
    fair_odds_list = []
    uses_devig_list = []
    
    for idx, row in df.iterrows():
        fair_odds, uses_devig = calculate_fair_odds_fast(row, df, pair_lookup)
        fair_odds_list.append(fair_odds)
        uses_devig_list.append(uses_devig)
        
        if (idx + 1) % 2000 == 0:
            print(f"  ... processed {idx + 1:,} / {len(df):,} rows")
    
    # Round fair odds to 2 decimals (standard for betting)
    df['fair_odds_decimal'] = [round(x, 2) for x in fair_odds_list]
    df['uses_devig'] = uses_devig_list
    
    df['best_au_odds_decimal'] = df.apply(calculate_best_au_odds, axis=1)
    df['best_au_bookmaker'] = df.apply(get_best_au_bookmaker, axis=1)
    df['ev_percent'] = df.apply(lambda row: calculate_ev(row['fair_odds_decimal'], 
                                                          row['best_au_odds_decimal']), axis=1)
    
    # Round ev_percent to 2 decimals
    df['ev_percent'] = df['ev_percent'].round(2)
    
    # Define bookmaker columns BEFORE adding any calculated columns
    # Same order as extract_nfl_v3.py ALL_BOOKMAKERS list
    BOOKMAKERS_IN_CSV = [
        # 4⭐ SHARPS
        "pinnacle", "betfair_ex_eu", "matchbook", "draftkings", "fanduel", "lowvig",
        # 0⭐ AU TARGETS
        "bet365", "betfair_ex_au", "sportsbet", "dabble_au", "pointsbetau", "neds", 
        "ladbrokes_au", "unibet", "betright", "betr_au", "boombet", "playup", "tab", "tabtouch",
        # 3⭐ SHARPS
        "betonlineag", "betmgm", "betrivers", "fanatics",
        # 2⭐ DECENT
        "hardrockbet", "williamhill_us", "bovada", "espnbet",
        # 1⭐ SOFT
        "coolbet", "fliff",
    ]
    
    # Add total_books column - count non-NA values for actual bookmakers
    df['total_books'] = df.apply(lambda row: count_available_books(row, BOOKMAKERS_IN_CSV), axis=1)
    
    # Count valid EVs
    valid_evs = df['ev_percent'].notna().sum()
    print(f"[OK] Calculated EV for {valid_evs:,} rows\n")
    
    # Add auto-incrementing id as first column
    df['id'] = range(1, len(df) + 1)
    
    core_cols = [
        'id', 'event_id', 'extracted_at', 'commence_time', 'league',
        'event_name', 'market_type', 'point', 'selection', 'player_name',
        'pair_id'
    ]
    
    # Only include bookmaker columns that actually exist in the input
    bookmaker_cols = [col for col in BOOKMAKERS_IN_CSV if col in df.columns]
    
    # Best AU book info + fair odds + EV + book stats
    final_cols = (
        core_cols +
        ['best_au_bookmaker', 'best_au_odds_decimal', 'ev_percent',
         'fair_odds_decimal', 'total_books', 'uses_devig'] +
        bookmaker_cols
    )
    df_output = df[final_cols].copy()
    
    # Save FULL version (all columns, reordered) - overwrites previous file (fallback if locked)
    os.makedirs("data/v3/extracts", exist_ok=True)
    output_csv_full = "data/v3/extracts/NFL_EV.csv"
    try:
        # Use float_format to ensure 2 decimal places for all floats
        df_output.to_csv(output_csv_full, index=False,
                        float_format=lambda x: f"{x:.2f}")
    except PermissionError:
        # File locked by backend API, save to alternate
        alt_csv_full = "data/v3/extracts/NFL_EV_new.csv"
        df_output.to_csv(alt_csv_full, index=False,
                        float_format=lambda x: f"{x:.2f}")
        print(f"[WARN]  Main file locked by backend, saved to: {alt_csv_full}")
        output_csv_full = alt_csv_full
    
    print(f"[OK] Full EV CSV saved: {output_csv_full}")
    print(f"   Columns: {len(df_output.columns)}")
    print(f"   Rows: {len(df):,}\n")

    # Build all-sports EV CSV (keep consistent column names)
    df_all = df.copy()
    df_all['sport'] = 'americanfootball_nfl'

    ordered_cols = [
        'sport', 'event_id', 'extracted_at', 'commence_time',
        'league', 'event_name', 'market_type', 'point', 'selection',
        'player_name', 'pair_id', 'best_au_bookmaker',
        'best_au_odds_decimal', 'ev_percent', 'fair_odds_decimal',
        'total_books', 'uses_devig'
    ]
    ordered_cols = [c for c in ordered_cols if c in df_all.columns]
    ordered_cols_with_books = ordered_cols + bookmaker_cols
    df_all_output = df_all[ordered_cols_with_books].copy()

    os.makedirs("data/v3/extracts", exist_ok=True)
    all_sports_ev = "data/v3/extracts/AllSports_EV.csv"
    nfl_ev = "data/v3/extracts/NFL_EV.csv"
    
    # Save NFL EV
    try:
        df_all_output.to_csv(nfl_ev, index=False)
        print(f"[OK] NFL_EV.csv saved: {len(df_all_output):,} rows")
    except PermissionError:
        print("[WARN] NFL_EV.csv locked, skipping")
    
    # Merge all *_EV.csv files into AllSports_EV.csv
    ev_files = sorted(glob.glob("data/v3/extracts/*_EV.csv"))
    if ev_files:
        dfs = []
        for f in ev_files:
            try:
                df = pd.read_csv(f)
                dfs.append(df)
            except Exception:
                pass
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            combined.to_csv(all_sports_ev, index=False)
            print(f"[OK] AllSports_EV merged: {len(combined):,} rows "
                  f"({combined['sport'].nunique()} sports)")
    print(f"   Combined columns: {len(df_all_output.columns)}")
    print(f"   Combined rows: {len(df_all_output):,}\n")
    
    # Print column summary
    print("[STATS] Column Breakdown:")
    print("   Core metadata: 11")
    print("   Best AU book: 1 (best_au_bookmaker)")
    print("   Metrics: 3 (best_au_odds_decimal, ev_percent, fair_odds_decimal)")
    print("   Stats: 2 (total_books, uses_devig)")
    print(f"   Bookmakers: {len(bookmaker_cols)}")
    print(f"   Total columns: {len(df_output.columns)}")
    
    print(f"\n[STATS] EV Statistics:")
    print(f"   Mean EV: {df['ev_percent'].mean():.2f}%")
    print(f"   Median EV: {df['ev_percent'].median():.2f}%")
    print(f"   Min EV: {df['ev_percent'].min():.2f}%")
    print(f"   Max EV: {df['ev_percent'].max():.2f}%")
    
    print(f"\n[STATS] EV Distribution:")
    print(f"   Positive EV: {(df['ev_percent'] > 0).sum():,}")
    print(f"   Negative EV: {(df['ev_percent'] < 0).sum():,}")
    
    return output_csv_full

if __name__ == "__main__":
    calculate_nfl_ev_full()
