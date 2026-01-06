"""
Detailed comparison: Bam Adebayo with MAD vs Fixed Trim
"""
import pandas as pd
import numpy as np

df = pd.read_csv('data/v3/extracts/basketball_nba_filtered.csv')

# Find Bam line
bam = df[(df['player_name'] == 'Bam Adebayo') & 
         (df['market_type'] == 'player_rebounds') &
         (df['selection'] == 'Under') &
         (df['point'] == 9.5)]

if bam.empty:
    print("Not found")
    exit(1)

under_row = bam.iloc[0]

over = df[(df['player_name'] == 'Bam Adebayo') & 
          (df['market_type'] == 'player_rebounds') &
          (df['selection'] == 'Over') &
          (df['point'] == 9.5)]

if over.empty:
    print("Opposite not found")
    exit(1)

over_row = over.iloc[0]

SHARP_BOOKS_4STAR = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
SHARP_BOOKS_3STAR = ['betonlineag', 'betmgm', 'betrivers', 'fanatics']
SOFT_BOOKS_2STAR = ['hardrockbet', 'williamhill_us', 'bovada', 'espnbet']
SOFT_BOOKS_1STAR = ['coolbet', 'fliff']

def odds_to_prob(odds):
    try:
        return 1.0 / float(odds)
    except:
        return np.nan

def devig_2way(p1_raw, p2_raw):
    overround = p1_raw + p2_raw
    if overround <= 0:
        return np.nan, np.nan
    return p1_raw / overround, p2_raw / overround

def is_mad_outlier(value, data_list, threshold=2.5):
    if len(data_list) < 3:
        return False
    data_array = np.array(data_list)
    median = np.median(data_array)
    mad = np.median(np.abs(data_array - median))
    if mad == 0:
        return False
    return abs(value - median) > threshold * mad

print('='*80)
print('BAM ADEBAYO REBOUNDS UNDER 9.5 - FIXED TRIM vs MAD COMPARISON')
print('='*80)
print()

# Collect all de-vigged
devig_by_rating = {
    '4⭐': {},
    '3⭐': {},
    '2⭐': {},
    '1⭐': {}
}

print('ALL BOOKS - De-vigged Probabilities:')
print('-'*80)
print(f"{'Book':<20} {'Rating':<6} De-vigged p(U)")
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
        
        print(f"{book:<20} {rating:<6} {p_under_devig:>14.6f}")

print()
print('='*80)
print('METHOD 1: FIXED 20% TRIM (Previous)')
print('='*80)
print()

all_probs = list(devig_by_rating['4⭐'].values()) + list(devig_by_rating['3⭐'].values()) + \
            list(devig_by_rating['2⭐'].values()) + list(devig_by_rating['1⭐'].values())
all_probs_sorted = sorted(all_probs)
trim_count = max(1, int(len(all_probs_sorted) * 0.2))
trimmed_fixed = all_probs_sorted[trim_count:-trim_count]

print(f"All de-vigged: {[f'{p:.6f}' for p in all_probs_sorted]}")
print(f"Trim 20% ({trim_count} books from each end):")
print(f"  Removed (low): {all_probs_sorted[:trim_count]}")
print(f"  Kept: {[f'{p:.6f}' for p in trimmed_fixed]}")
print(f"  Removed (high): {all_probs_sorted[-trim_count:]}")
print()

# For fixed trim, use median
fixed_median = np.median(trimmed_fixed)
fixed_fair = 1.0 / fixed_median
print(f"Median of trimmed: {fixed_median:.6f}")
print(f"Fair Odds: {fixed_fair:.4f} → Rounded: {round(fixed_fair, 2)}")
print()

print('='*80)
print('METHOD 2: MAD-BASED OUTLIER DETECTION (New)')
print('='*80)
print()

# 4⭐: Remove only if MAD outlier AND conflicts
probs_4 = list(devig_by_rating['4⭐'].values())
final_4star = {}

if len(probs_4) >= 3:
    for book, prob in devig_by_rating['4⭐'].items():
        is_mad = is_mad_outlier(prob, probs_4, threshold=2.5)
        consensus_all = np.median(probs_4 + list(devig_by_rating['3⭐'].values()))
        conflicts = abs(prob - consensus_all) > 0.03
        
        should_remove = is_mad and conflicts and len(probs_4) > 1
        
        print(f"4⭐ {book:<15} {prob:.6f}  MAD_outlier={is_mad}, conflicts_consensus={conflicts}, remove={should_remove}")
        if not should_remove:
            final_4star[book] = prob
else:
    print("4⭐ Less than 3 books - no MAD removal")
    final_4star = devig_by_rating['4⭐']

print()

# 3⭐: Remove only if MAD outlier
probs_3 = list(devig_by_rating['3⭐'].values())
final_3star = {}

if len(probs_3) >= 3:
    for book, prob in devig_by_rating['3⭐'].items():
        is_mad = is_mad_outlier(prob, probs_3, threshold=2.5)
        print(f"3⭐ {book:<15} {prob:.6f}  MAD_outlier={is_mad}, remove={is_mad}")
        if not is_mad:
            final_3star[book] = prob
else:
    print("3⭐ Less than 3 books - no MAD removal")
    final_3star = devig_by_rating['3⭐']

print()

# 2⭐: Remove if MAD outlier
probs_2 = list(devig_by_rating['2⭐'].values())
final_2star = {}

if len(probs_2) >= 3:
    for book, prob in devig_by_rating['2⭐'].items():
        is_mad = is_mad_outlier(prob, probs_2, threshold=2.5)
        print(f"2⭐ {book:<15} {prob:.6f}  MAD_outlier={is_mad}, remove={is_mad}")
        if not is_mad:
            final_2star[book] = prob
else:
    print("2⭐ Less than 3 books - no MAD removal")
    final_2star = devig_by_rating['2⭐']

print()

# 1⭐: Remove if MAD outlier
probs_1 = list(devig_by_rating['1⭐'].values())
final_1star = {}

if len(probs_1) >= 2:
    for book, prob in devig_by_rating['1⭐'].items():
        is_mad = is_mad_outlier(prob, probs_1, threshold=2.5)
        print(f"1⭐ {book:<15} {prob:.6f}  MAD_outlier={is_mad}, remove={is_mad}")
        if not is_mad:
            final_1star[book] = prob
else:
    print("1⭐ Less than 2 books - no MAD removal")
    final_1star = devig_by_rating['1⭐']

print()
print('-'*80)

all_final = {**final_4star, **final_3star, **final_2star, **final_1star}
print(f"Final books kept: {list(all_final.keys())}")

# Weighted average
BOOK_WEIGHTS = {**{b: 1.5 for b in SHARP_BOOKS_4STAR},
                **{b: 1.0 for b in SHARP_BOOKS_3STAR},
                **{b: 0.75 for b in SOFT_BOOKS_2STAR},
                **{b: 0.5 for b in SOFT_BOOKS_1STAR}}

weights_list = [BOOK_WEIGHTS[b] for b in all_final.keys()]
probs_list = list(all_final.values())

mad_fair_prob = np.average(probs_list, weights=weights_list)
mad_fair_odds = 1.0 / mad_fair_prob

print(f"Weighted average: {mad_fair_prob:.6f}")
print(f"Fair Odds: {mad_fair_odds:.4f} → Rounded: {round(mad_fair_odds, 2)}")
print()

print('='*80)
print('COMPARISON')
print('='*80)
print(f"FIXED TRIM:    Fair Odds {round(fixed_fair, 2)}  ({len(trimmed_fixed)} books)")
print(f"MAD-BASED:     Fair Odds {round(mad_fair_odds, 2)}  ({len(all_final)} books)")
print()
print(f"Books kept with MAD: {list(all_final.keys())}")
print(f"Books removed with FIXED: {[k for k, v in zip(all_probs_sorted, range(len(all_probs_sorted))) if v < trim_count or v >= len(all_probs_sorted) - trim_count]}")
