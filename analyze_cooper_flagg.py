"""
Find and analyze Cooper Flagg player_assists line
"""
import pandas as pd
import numpy as np

# Load EV data
df = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')

# Find the specific line
target = df[(df['event_name'] == 'Dallas Mavericks @ Sacramento Kings') & 
            (df['market_type'] == 'player_assists') & 
            (df['player_name'] == 'Cooper Flagg') &
            (df['selection'] == 'Under') & 
            (df['point'] == 5.5)]

if target.empty:
    print("Line not found")
    exit(1)

row = target.iloc[0]

print('🎯 COOPER FLAGG - ASSISTS UNDER 5.5')
print('='*80)
print(f"Event: {row['event_name']}")
print(f"Fair odds: {row['Fair odds']}")
print(f"AU Odds: {row['best_au_odds_decimal']:.4f} ({row['best_au_bookmaker']})")
print(f"EV: {row['EV']}")
print(f"Uses De-vig: {row['uses_devig']}")
print(f"Total Books: {int(row['total_books'])}")
print()

# Load filtered data to find opposite and show calculation
df_filtered = pd.read_csv('data/v3/extracts/basketball_nba_filtered.csv')

# Find opposite row (Over 5.5)
opposite = df_filtered[(df_filtered['market_type'] == 'player_assists') & 
                       (df_filtered['player_name'] == 'Cooper Flagg') &
                       (df_filtered['selection'] == 'Over') & 
                       (df_filtered['point'] == 5.5)]

if opposite.empty:
    print("❌ Opposite (Over) not found in filtered data")
    exit(1)

opposite_row = opposite.iloc[0]

# Get sharp books
sharp_books_4star = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
sharp_books_3star = ['betonlineag', 'betmgm', 'betrivers', 'fanatics']

print('STEP 1: Collect odds from all SHARP books (3⭐ and 4⭐ only)')
print('='*80)
print(f"{'Book':<20} {'Rating':<6} Under 5.5 | Over 5.5  | p(Under) | p(Over) | Overround")
print('-'*80)

all_devig_data = []

for book in sharp_books_4star + sharp_books_3star:
    if book in df_filtered.columns:
        under_odds_filt = row[book] if pd.notna(row[book]) else np.nan
        over_odds_filt = opposite_row[book] if pd.notna(opposite_row[book]) else np.nan
        
        if pd.notna(under_odds_filt) and pd.notna(over_odds_filt):
            p_under = 1.0 / float(under_odds_filt)
            p_over = 1.0 / float(over_odds_filt)
            overround = p_under + p_over
            
            rating = "4⭐" if book in sharp_books_4star else "3⭐"
            print(f"{book:<20} {rating:<6} {float(under_odds_filt):>7.4f}  | {float(over_odds_filt):>7.4f}  | {p_under:>7.4f} | {p_over:>7.4f} | {overround:>8.4f}")
            
            all_devig_data.append({
                'book': book,
                'rating': rating,
                'under_odds': float(under_odds_filt),
                'over_odds': float(over_odds_filt),
                'p_under': p_under,
                'p_over': p_over,
                'overround': overround
            })

print()
print('STEP 2: De-vig - Remove bookmaker margin from each book')
print('='*80)
print(f"{'Book':<20} {'De-vigged p(U)':<16} Calculation")
print('-'*80)

devig_probs = {}
for data in all_devig_data:
    p_under_raw = data['p_under']
    p_over_raw = data['p_over']
    overround = data['overround']
    
    # De-vig: divide by total overround
    p_under_devig = p_under_raw / overround
    devig_probs[data['book']] = p_under_devig
    
    print(f"{data['book']:<20} {p_under_devig:>15.6f}  {p_under_raw:.6f} / {overround:.6f}")

print()
print('STEP 3: Apply 20% trim to remove outliers')
print('='*80)

probs = list(devig_probs.values())
sorted_probs = sorted(probs)
trim_count = max(1, int(len(sorted_probs) * 0.2))

print(f"Total de-vigged probabilities: {len(probs)}")
print(f"Sorted (low to high): {[f'{p:.6f}' for p in sorted_probs]}")
print(f"Trim count (20% from each end): {trim_count}")

if trim_count > 0 and len(sorted_probs) > trim_count * 2:
    trimmed = sorted_probs[trim_count:-trim_count]
    print(f"After trim ({trim_count} removed from each end):")
    print(f"  Removed (bottom): {sorted_probs[:trim_count]}")
    print(f"  Kept: {[f'{p:.6f}' for p in trimmed]}")
    print(f"  Removed (top): {sorted_probs[-trim_count:]}")
else:
    trimmed = sorted_probs
    print(f"Note: Only {len(probs)} books - not enough to trim significantly")

fair_prob = np.median(trimmed) if len(trimmed) > 0 else np.median(probs)
print(f"Median of trimmed: {fair_prob:.6f}")

print()
print('STEP 4: Convert de-vigged probability to fair decimal odds')
print('='*80)
fair_decimal = 1.0 / fair_prob
print(f"Fair Probability: {fair_prob:.6f}")
print(f"Fair Decimal Odds: 1 / {fair_prob:.6f} = {fair_decimal:.4f}")
print(f"Rounded to 2 decimals: {round(fair_decimal, 2)}")
print(f"✓ Matches CSV: {row['Fair odds']}")

print()
print('STEP 5: Calculate EV')
print('='*80)
au_odds = row['best_au_odds_decimal']
fair_prob_for_ev = 1.0 / row['Fair odds']
ev_decimal = (au_odds * fair_prob_for_ev) - 1
ev_pct = ev_decimal * 100

print(f"Fair Odds: {row['Fair odds']}")
print(f"AU Odds ({row['best_au_bookmaker']}): {au_odds:.4f}")
print()
print(f"Implied Probability from Fair Odds: 1 / {row['Fair odds']} = {fair_prob_for_ev:.6f}")
print(f"EV Formula: (AU Odds × Fair Prob) - 1")
print(f"EV = ({au_odds:.4f} × {fair_prob_for_ev:.6f}) - 1")
print(f"EV = {au_odds * fair_prob_for_ev:.6f} - 1")
print(f"EV = {ev_decimal:.6f} = {ev_pct:.2f}%")
print()
print(f"CSV EV: {row['EV']}")
