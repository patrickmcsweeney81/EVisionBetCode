"""
Detailed comparison: Bam Adebayo Under 9.5 - Old Median vs New Weighted System
"""
import pandas as pd
import numpy as np

# Load filtered data
df = pd.read_csv('data/v3/extracts/basketball_nba_filtered.csv')

# Find Bam Adebayo Under 9.5
bam = df[(df['player_name'] == 'Bam Adebayo') & 
         (df['market_type'] == 'player_rebounds') &
         (df['selection'] == 'Under') &
         (df['point'] == 9.5)]

if bam.empty:
    print("Bam Adebayo line not found")
    exit(1)

under_row = bam.iloc[0]

# Find opposite (Over 9.5)
over = df[(df['player_name'] == 'Bam Adebayo') & 
          (df['market_type'] == 'player_rebounds') &
          (df['selection'] == 'Over') &
          (df['point'] == 9.5)]

if over.empty:
    print("Opposite line not found")
    exit(1)

over_row = over.iloc[0]

# Define book classifications
SHARP_BOOKS_4STAR = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
SHARP_BOOKS_3STAR = ['betonlineag', 'betmgm', 'betrivers', 'fanatics']
SOFT_BOOKS_2STAR = ['hardrockbet', 'williamhill_us', 'bovada', 'espnbet']
SOFT_BOOKS_1STAR = ['coolbet', 'fliff']

# De-vigging function
def devig_2way(p1_raw, p2_raw):
    overround = p1_raw + p2_raw
    if overround <= 0:
        return np.nan, np.nan
    return p1_raw / overround, p2_raw / overround

def odds_to_prob(odds):
    try:
        return 1.0 / float(odds)
    except:
        return np.nan

print('='*80)
print('BAM ADEBAYO REBOUNDS UNDER 9.5 - SYSTEM COMPARISON')
print('='*80)
print()

# Collect all de-vigged probabilities by rating
print('STEP 1: Collect & De-vig All Books')
print('-'*80)

devig_by_rating = {
    '4⭐': {},
    '3⭐': {},
    '2⭐': {},
    '1⭐': {}
}

print(f"{'Book':<20} {'Rating':<6} Under Odds | Over Odds | De-vigged p(U)")
print('-'*80)

for book in SHARP_BOOKS_4STAR + SHARP_BOOKS_3STAR + SOFT_BOOKS_2STAR + SOFT_BOOKS_1STAR:
    if pd.notna(under_row[book]) and pd.notna(over_row[book]):
        under_odds = float(under_row[book])
        over_odds = float(over_row[book])
        
        p_under_raw = odds_to_prob(under_odds)
        p_over_raw = odds_to_prob(over_odds)
        
        p_under_devig, _ = devig_2way(p_under_raw, p_over_raw)
        
        if book in SHARP_BOOKS_4STAR:
            rating = '4⭐'
            devig_by_rating['4⭐'][book] = p_under_devig
        elif book in SHARP_BOOKS_3STAR:
            rating = '3⭐'
            devig_by_rating['3⭐'][book] = p_under_devig
        elif book in SOFT_BOOKS_2STAR:
            rating = '2⭐'
            devig_by_rating['2⭐'][book] = p_under_devig
        else:
            rating = '1⭐'
            devig_by_rating['1⭐'][book] = p_under_devig
        
        print(f"{book:<20} {rating:<6} {under_odds:>9.4f} | {over_odds:>9.4f} | {p_under_devig:>14.6f}")

print()
print('STEP 2: OLD SYSTEM - Median of Sharp Books Only (4⭐ + 3⭐)')
print('-'*80)

sharp_probs = list(devig_by_rating['4⭐'].values()) + list(devig_by_rating['3⭐'].values())
sharp_books = list(devig_by_rating['4⭐'].keys()) + list(devig_by_rating['3⭐'].keys())

print(f"Sharp books: {sharp_books}")
print(f"De-vigged probs: {[f'{p:.6f}' for p in sharp_probs]}")

sorted_sharp = sorted(sharp_probs)
trim_count = max(1, int(len(sorted_sharp) * 0.2))
trimmed_sharp = sorted_sharp[trim_count:-trim_count]

print(f"Sorted: {[f'{p:.6f}' for p in sorted_sharp]}")
print(f"20% trim ({trim_count} books): remove {sorted_sharp[:trim_count]}, keep {[f'{p:.6f}' for p in trimmed_sharp]}, remove {sorted_sharp[-trim_count:]}")

old_fair_prob = np.median(trimmed_sharp)
old_fair_odds = 1.0 / old_fair_prob

print(f"Median of trimmed: {old_fair_prob:.6f} → Fair Odds: {old_fair_odds:.4f}")
print()

print('STEP 3: NEW SYSTEM - Weighted Average of All Books')
print('-'*80)

# For soft books, apply trim first
soft_2star_probs = list(devig_by_rating['2⭐'].values())
soft_1star_probs = list(devig_by_rating['1⭐'].values())

# Trim soft books
all_soft = soft_2star_probs + soft_1star_probs
if len(all_soft) >= 2:
    sorted_soft = sorted(all_soft)
    soft_trim = max(1, int(len(sorted_soft) * 0.2))
    trimmed_soft = sorted_soft[soft_trim:-soft_trim]
    print(f"Soft books (2⭐ + 1⭐): {[f'{p:.6f}' for p in all_soft]}")
    print(f"20% trim: keep {[f'{p:.6f}' for p in trimmed_soft]}")
else:
    trimmed_soft = all_soft

# Combine all (sharp never trimmed, soft trimmed)
all_probs_with_books = []
sharp_4star_list = list(devig_by_rating['4⭐'].items())
sharp_3star_list = list(devig_by_rating['3⭐'].items())

for book, prob in sharp_4star_list:
    all_probs_with_books.append((book, prob, 1.5, '4⭐'))

for book, prob in sharp_3star_list:
    all_probs_with_books.append((book, prob, 1.0, '3⭐'))

# Add trimmed soft books
soft_2star_items = list(devig_by_rating['2⭐'].items())
soft_1star_items = list(devig_by_rating['1⭐'].items())
all_soft_items = soft_2star_items + soft_1star_items

for book, prob in all_soft_items:
    if prob in trimmed_soft:
        if book in [b for b, _ in soft_2star_items]:
            all_probs_with_books.append((book, prob, 0.75, '2⭐'))
        else:
            all_probs_with_books.append((book, prob, 0.5, '1⭐'))
        trimmed_soft.remove(prob)  # Remove used value

print(f"{'Book':<20} {'p(U)':<12} {'Weight':<8} {'Weighted':<12}")
print('-'*80)

total_weighted = 0
total_weight = 0

for book, prob, weight, rating in all_probs_with_books:
    weighted_contrib = prob * weight
    total_weighted += weighted_contrib
    total_weight += weight
    print(f"{book:<20} {prob:>11.6f} {weight:>7.2f} {weighted_contrib:>11.6f}")

new_fair_prob = total_weighted / total_weight
new_fair_odds = 1.0 / new_fair_prob

print('-'*80)
print(f"Total weighted: {total_weighted:.6f} / {total_weight:.2f} = {new_fair_prob:.6f}")
print(f"Fair Odds: {new_fair_odds:.4f} (rounded: {round(new_fair_odds, 2)})")
print()

print('COMPARISON:')
print('-'*80)
print(f"OLD SYSTEM (Sharp Only + Median Trim):  {old_fair_odds:.4f} → Rounded: {round(old_fair_odds, 2)}")
print(f"NEW SYSTEM (All Books Weighted):        {new_fair_odds:.4f} → Rounded: {round(new_fair_odds, 2)}")
print(f"Difference: {abs(new_fair_odds - old_fair_odds):.4f} ({((new_fair_odds - old_fair_odds) / old_fair_odds * 100):.2f}%)")
print()

# Now calculate EV with actual AU odds
au_odds = 1.92  # DabbleAU (from loaded data or manual lookup)
print(f'EV CALCULATION:')
print('-'*80)
print(f"AU Odds (DabbleAU): {au_odds}")
print()
print(f"OLD SYSTEM:")
old_fair_prob_ev = 1.0 / round(old_fair_odds, 2)
old_ev = (au_odds * old_fair_prob_ev) - 1
print(f"  Fair Odds: {round(old_fair_odds, 2)} → p: {old_fair_prob_ev:.6f}")
print(f"  EV = ({au_odds} × {old_fair_prob_ev:.6f}) - 1 = {old_ev:.6f} = {old_ev*100:.2f}%")
print()
print(f"NEW SYSTEM:")
new_fair_prob_ev = 1.0 / round(new_fair_odds, 2)
new_ev = (au_odds * new_fair_prob_ev) - 1
print(f"  Fair Odds: {round(new_fair_odds, 2)} → p: {new_fair_prob_ev:.6f}")
print(f"  EV = ({au_odds} × {new_fair_prob_ev:.6f}) - 1 = {new_ev:.6f} = {new_ev*100:.2f}%")
print()

# Load actual result
ev_data = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')
actual = ev_data[(ev_data['player_name'] == 'Bam Adebayo') & 
                 (ev_data['market_type'] == 'player_rebounds') &
                 (ev_data['selection'] == 'Under') &
                 (ev_data['point'] == 9.5)]

if not actual.empty:
    actual_row = actual.iloc[0]
    print(f"ACTUAL CSV RESULT:")
    print(f"  Fair Odds: {actual_row['Fair odds']}")
    print(f"  EV: {actual_row['EV']}")
