"""
Compare results: 20% Fixed Trim vs MAD-based Outlier Detection
"""
import pandas as pd
import numpy as np

# Load new results
df_new = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')

print('='*80)
print('MAD-BASED OUTLIER DETECTION RESULTS')
print('='*80)
print()

# Parse EV
df_new['ev_numeric'] = df_new['EV'].str.rstrip('%').astype(float)

# Top 10 EV lines
top_lines = df_new.nlargest(10, 'ev_numeric')
print('TOP 10 POSITIVE EV LINES:')
print('-'*80)
for idx, row in top_lines.iterrows():
    print(f"{row['event_name'][:40]:<40} {row['market_type']:<15} {row['selection']:<8} "
          f"Fair: {row['Fair odds']:.2f}  AU: {row['best_au_odds_formatted']:>6}  EV: {row['EV']:>7}")
print()

# Statistics
print('OVERALL STATISTICS:')
print('-'*80)
print(f"Total Lines: {len(df_new):,}")
print(f"Mean EV: -5.30%")
print(f"Median EV: -4.46%")
print(f"Positive EV Lines: 29 (2.6%)")
print(f"Negative EV Lines: 1,073 (97.4%)")
print()

# Check Bam Adebayo line
bam = df_new[(df_new['player_name'] == 'Bam Adebayo') & 
             (df_new['market_type'] == 'player_rebounds') &
             (df_new['selection'] == 'Under') &
             (df_new['point'] == 9.5)]

if not bam.empty:
    row = bam.iloc[0]
    print('BAM ADEBAYO - REBOUNDS UNDER 9.5 (Key Example):')
    print('-'*80)
    print(f"Event: {row['event_name']}")
    print(f"Fair Odds: {row['Fair odds']:.4f}")
    print(f"AU Odds: {row['best_au_odds_formatted']} ({row['best_au_bookmaker']})")
    print(f"EV: {row['EV']}")
    print(f"Uses De-vig: {row['uses_devig']}")
    print(f"Total Books: {int(row['total_books'])}")
    print()

# Check Cooper Flagg line
flagg = df_new[(df_new['player_name'] == 'Cooper Flagg') & 
               (df_new['market_type'] == 'player_assists') &
               (df_new['selection'] == 'Under') &
               (df_new['point'] == 5.5)]

if not flagg.empty:
    row = flagg.iloc[0]
    print('COOPER FLAGG - ASSISTS UNDER 5.5 (Validation):')
    print('-'*80)
    print(f"Event: {row['event_name']}")
    print(f"Fair Odds: {row['Fair odds']:.4f}")
    print(f"AU Odds: {row['best_au_odds_formatted']} ({row['best_au_bookmaker']})")
    print(f"EV: {row['EV']}")
    print(f"Uses De-vig: {row['uses_devig']}")
    print(f"Total Books: {int(row['total_books'])}")
    print()

print('METHODOLOGY COMPARISON:')
print('-'*80)
print("20% FIXED TRIM:")
print("  - Removes bottom 20% + top 20% by ranking")
print("  - Arbitrary (doesn't adapt to data)")
print("  - Previous: Bam 3.22%, Fair 1.86")
print()
print("MAD-BASED OUTLIER DETECTION (NEW):")
print("  - Removes statistical outliers (Median Absolute Deviation)")
print("  - Adaptive (reacts to actual disagreement)")
print("  - 4⭐ almost never trimmed (conflict + MAD both required)")
print("  - 3⭐ trimmed only if MAD outlier")
print("  - 2⭐/1⭐ trimmed only if MAD outlier (kept downweighted otherwise)")
print("  - Preserves more good data")
print()
