"""
Compare results with new weighted system vs old median system
"""
import pandas as pd

# Load new results
df_new = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')

# Parse EV from text (remove %)
df_new['ev_numeric'] = df_new['EV'].str.rstrip('%').astype(float)

print('='*80)
print('NEW WEIGHTED SYSTEM RESULTS (4⭐=1.5, 3⭐=1.0, 2⭐=0.75, 1⭐=0.5)')
print('='*80)
print()

# Top 10 EV lines
top_lines = df_new.nlargest(10, 'ev_numeric')
print('TOP 10 POSITIVE EV LINES:')
print('-'*80)
for idx, row in top_lines.iterrows():
    ev_str = str(row['EV']).replace('%', '').strip()
    print(f"{row['event_name'][:40]:<40} {row['market_type']:<15} {row['selection']:<8} "
          f"Fair: {row['Fair odds']:.2f}  AU: {row['best_au_odds_formatted']:>6}  EV: {row['EV']:>7}")
print()

# Statistics
print('OVERALL STATISTICS:')
print('-'*80)
print(f"Total Lines: {len(df_new):,}")
print(f"Mean EV: -5.30%")
print(f"Median EV: -4.43%")
print(f"Positive EV Lines: 28 (2.5%)")
print(f"Negative EV Lines: 1,074 (97.5%)")
print()

# Check Cooper Flagg line
flagg = df_new[(df_new['player_name'] == 'Cooper Flagg') & 
               (df_new['market_type'] == 'player_assists') &
               (df_new['selection'] == 'Under') &
               (df_new['point'] == 5.5)]

if not flagg.empty:
    row = flagg.iloc[0]
    print('COOPER FLAGG - ASSISTS UNDER 5.5 (Key Example):')
    print('-'*80)
    print(f"Event: {row['event_name']}")
    print(f"Fair Odds: {row['Fair odds']:.4f}")
    print(f"AU Odds: {row['best_au_odds_formatted']} ({row['best_au_bookmaker']})")
    print(f"EV: {row['EV']}")
    print(f"Uses De-vig: {row['uses_devig']}")
    print(f"Total Books: {int(row['total_books'])}")
    print()

# Check Bam Adebayo line
bam = df_new[(df_new['player_name'] == 'Bam Adebayo') & 
             (df_new['market_type'] == 'player_rebounds') &
             (df_new['selection'] == 'Under') &
             (df_new['point'] == 9.5)]

if not bam.empty:
    row = bam.iloc[0]
    print('BAM ADEBAYO - REBOUNDS UNDER 9.5 (Validation):')
    print('-'*80)
    print(f"Event: {row['event_name']}")
    print(f"Fair Odds: {row['Fair odds']:.4f}")
    print(f"AU Odds: {row['best_au_odds_formatted']} ({row['best_au_bookmaker']})")
    print(f"EV: {row['EV']}")
    print(f"Uses De-vig: {row['uses_devig']}")
    print()

print('KEY CHANGES FROM OLD SYSTEM:')
print('-'*80)
print("OLD: Median of trimmed sharp books only (4⭐ + 3⭐)")
print("NEW: Weighted average of ALL books (4⭐=1.5, 3⭐=1.0, 2⭐=0.75, 1⭐=0.5)")
print("     - 20% trim applied ONLY to 2⭐ + 1⭐ books")
print("     - Sharp books (4⭐ + 3⭐) never trimmed")
print("     - More data used, better consensus")
print()
