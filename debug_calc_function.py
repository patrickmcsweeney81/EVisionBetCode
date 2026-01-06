"""
Debug: Test calculate_fair_odds function for spreads
"""

import pandas as pd
import numpy as np

df = pd.read_csv("data/v3/extracts/basketball_nba_filtered.csv")

SHARP_BOOKS = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
AU_BOOKS = ['bet365', 'betfair_ex_au', 'sportsbet', 'dabble_au', 'pointsbetau', 
            'neds', 'ladbrokes_au', 'unibet', 'betright', 'betr_au', 'boombet', 
            'playup', 'tab', 'tabtouch']

TWO_WAY_MARKETS = {
    'totals': {'Over': 'Under', 'Under': 'Over'},
    'spreads': {'Home': 'Away', 'Away': 'Home'},
    'h2h': {'Home': 'Away', 'Away': 'Home'},
}

def get_opposite_selection(market_type, selection):
    if market_type not in TWO_WAY_MARKETS:
        return None
    return TWO_WAY_MARKETS[market_type].get(selection)

# Test with first spread
spreads = df[df['market_type'] == 'spreads']
row = spreads.iloc[0]  # Cleveland @ -5.5

print(f"Testing with row: {row['event_name']}, {row['selection']}, {row['point']}")
print(f"market_type = {row['market_type']}")
print(f"selection = {row['selection']}")

opposite_sel = get_opposite_selection(row['market_type'], row['selection'])
print(f"opposite_selection would be: {opposite_sel}")

point = row.get('point', '')
print(f"point from row.get() = {point} (type: {type(point).__name__})")

if row['market_type'] == 'spreads':
    try:
        opposite_point = -float(point) if pd.notna(point) else ''
        print(f"opposite_point calculated = {opposite_point}")
    except Exception as e:
        print(f"ERROR calculating opposite_point: {e}")
        opposite_point = point
    
    print(f"\nSearching for opposite in df...")
    opposite_rows = df[(df['event_id'] == row['event_id']) & 
                       (df['market_type'] == row['market_type']) & 
                       (df['selection'] == opposite_sel) &
                       ((df['point'] == opposite_point) | 
                        (df['point'].astype(str) == str(opposite_point)))]
    
    print(f"Found {len(opposite_rows)} matches")
    if len(opposite_rows) > 0:
        opp = opposite_rows.iloc[0]
        print(f"  {opp['selection']} @ {opp['point']}")
        
        # Check if we have sharp books
        sharp_odds = [opp[book] for book in SHARP_BOOKS if pd.notna(opp[book])]
        print(f"  Sharp books available: {len(sharp_odds)}")
        print(f"  Sharp book values: {sharp_odds}")
