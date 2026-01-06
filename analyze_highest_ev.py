"""
Analyze the highest EV line with full fair odds calculation breakdown
"""
import pandas as pd
import numpy as np

# Load the EV data
df = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')

# Parse EV from formatted string
df['ev_percent_numeric'] = df['ev_percent_formatted'].str.rstrip('%').astype(float)

# Find highest EV
max_idx = df['ev_percent_numeric'].idxmax()
row = df.loc[max_idx]

print('🏆 HIGHEST EV LINE')
print('='*80)
print(f"EV: {row['ev_percent_numeric']:.2f}%")
print(f"Event: {row['event_name']}")
print(f"Market: {row['market_type']} - {row['selection']} {row['point'] if pd.notna(row['point']) else ''}")
print(f"Fair Odds: {row['fair_odds_decimal']:.4f}")
print(f"Best AU Odds: {row['best_au_odds_decimal']:.4f} ({row['best_au_bookmaker']})")
print(f"Uses De-vig: {row['uses_devig']}")
print(f"Total Books Available: {int(row['total_books'])}")
print()

# List of all sharp books
sharp_books_4star = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
sharp_books_3star = ['betonlineag', 'betmgm', 'betrivers', 'fanatics']
decent_books_2star = ['hardrockbet', 'williamhill_us', 'bovada', 'espnbet', 'coolbet']

print('SHARP BOOKS (4⭐) - Available odds:')
print('-'*40)
odds_4star = []
for book in sharp_books_4star:
    if book in df.columns and pd.notna(row[book]):
        odds = float(row[book])
        odds_4star.append(odds)
        print(f'{book:20s}: {odds:.4f}')

print()
print('SHARP BOOKS (3⭐) - Available odds:')
print('-'*40)
odds_3star = []
for book in sharp_books_3star:
    if book in df.columns and pd.notna(row[book]):
        odds = float(row[book])
        odds_3star.append(odds)
        print(f'{book:20s}: {odds:.4f}')

print()
print('DECENT BOOKS (2⭐) - Available odds:')
print('-'*40)
odds_2star = []
for book in decent_books_2star:
    if book in df.columns and pd.notna(row[book]):
        odds = float(row[book])
        odds_2star.append(odds)
        print(f'{book:20s}: {odds:.4f}')

# Now show the fair odds calculation
all_odds = odds_4star + odds_3star + odds_2star
print()
print('FAIR ODDS CALCULATION (De-vigged)')
print('='*80)

if row['uses_devig'] and row['market_type'] in ['spreads', 'totals', 'h2h']:
    print(f"Market Type: {row['market_type']} (2-way market - uses de-vigging)")
    print()
    
    # Load filtered data to find opposite
    df_filtered = pd.read_csv('data/v3/extracts/basketball_nba_filtered.csv')
    
    event_id = row['event_id']
    market_type = row['market_type']
    selection = row['selection']
    point = row['point']
    
    print(f"Step 1: Find opposite selection in same event/market")
    print(f"  Event ID: {event_id}, Market: {market_type}, Selection: {selection}, Point: {point}")
    
    # Find opposite
    if market_type == 'spreads':
        try:
            opposite_point = -float(point) if pd.notna(point) else ''
        except:
            opposite_point = point
        
        opposite_rows = df_filtered[(df_filtered['event_id'] == event_id) & 
                                   (df_filtered['market_type'] == market_type) & 
                                   (df_filtered['selection'] != selection) &
                                   ((df_filtered['point'] == opposite_point) | 
                                    (df_filtered['point'].astype(str) == str(opposite_point)))]
    else:
        opposite_rows = df_filtered[(df_filtered['event_id'] == event_id) & 
                                   (df_filtered['market_type'] == market_type) & 
                                   (df_filtered['selection'] != selection)]
    
    if not opposite_rows.empty:
        opposite_row = opposite_rows.iloc[0]
        opposite_sel = opposite_row['selection']
        print(f"  ✓ Found opposite: {opposite_sel}")
        print()
        
        print(f"Step 2: Extract odds for both sides from all sharp books")
        print(f"  This outcome ({selection})  |  Opposite outcome ({opposite_sel})")
        print(f"  {'-'*30}|{'-'*30}")
        
        devig_probs = {}
        for book in sharp_books_4star + sharp_books_3star + decent_books_2star:
            if book in df.columns and pd.notna(row[book]) and pd.notna(opposite_row[book]):
                odds1 = float(row[book])
                odds2 = float(opposite_row[book])
                p1_raw = 1.0 / odds1
                p2_raw = 1.0 / odds2
                overround = p1_raw + p2_raw
                p1_devig = p1_raw / overround
                devig_probs[book] = p1_devig
                
                rating = "4⭐" if book in sharp_books_4star else ("3⭐" if book in sharp_books_3star else "2⭐")
                print(f"  {book:20s} ({rating}) | {odds1:.4f} ({p1_raw:.4f}) | {odds2:.4f} ({p2_raw:.4f})")
                print(f"  {'':20s} | p_devig: {p1_devig:.6f}")
        
        print()
        print(f"Step 3: Apply 20% trim to remove outliers")
        probs = list(devig_probs.values())
        sorted_probs = sorted(probs)
        trim_count = max(1, int(len(sorted_probs) * 0.2))
        trimmed = sorted_probs[trim_count:-trim_count] if trim_count > 0 else sorted_probs
        
        print(f"  Total de-vigged probabilities: {len(probs)}")
        print(f"  Sorted: {[f'{p:.6f}' for p in sorted_probs]}")
        print(f"  Trim count (20%): {trim_count}")
        print(f"  After trim: {[f'{p:.6f}' for p in trimmed]}")
        
        fair_prob = np.median(trimmed) if len(trimmed) > 0 else np.median(probs)
        print(f"  Median of trimmed: {fair_prob:.6f}")
        
        fair_decimal = 1.0 / fair_prob
        print()
        print(f"Step 4: Convert probability back to decimal odds")
        print(f"  Fair Probability: {fair_prob:.6f}")
        print(f"  Fair Decimal: 1 / {fair_prob:.6f} = {fair_decimal:.4f}")
        
else:
    print(f"Market Type: {row['market_type']} (single-outcome market)")
    print("No de-vigging (using simple probability average)")
    probs = [1.0/o for o in all_odds]
    fair_prob = np.mean(probs)
    fair_decimal = 1.0 / fair_prob
    print(f"  Average probability: {fair_prob:.6f}")
    print(f"  Fair decimal: {fair_decimal:.4f}")

print()
print('EV CALCULATION')
print('='*80)
au_odds = row['best_au_odds_decimal']
fair_odds = row['fair_odds_decimal']

print(f"Fair odds: {fair_odds:.4f}")
print(f"AU odds (best): {au_odds:.4f} ({row['best_au_bookmaker']})")
print()
print(f"EV calculation:")
print(f"  1. Fair probability: 1 / {fair_odds:.4f} = {1.0/fair_odds:.6f}")
print(f"  2. EV% = (AU odds × Fair prob) - 1")
print(f"  3. EV% = ({au_odds:.4f} × {1.0/fair_odds:.6f}) - 1")
ev_calc = (au_odds * (1.0/fair_odds)) - 1
print(f"  4. EV% = {ev_calc:.6f} = {ev_calc*100:.2f}%")
print()
print(f"✅ Highest EV opportunity: {row['ev_percent_numeric']:.2f}%")
