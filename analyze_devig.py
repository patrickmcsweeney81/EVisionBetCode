import pandas as pd
import glob

csv = sorted(glob.glob('data/v3/extracts/basketball_nba_outliers_devig_*.csv'))[-1]
df = pd.read_csv(csv)

print('=== DE-VIG METHOD RESULTS ===\n')
print('📊 SUMMARY:')
print(f'Total outlier lines found: {len(df)}')
print(f'Total outlier occurrences: {int(df["num_outliers"].sum())}')
print()

# Count devig usage
devig_yes = len(df[df['uses_devig'] == True])
devig_no = len(df[df['uses_devig'] != True])

print('🔬 DETECTION METHOD BREAKDOWN:')
print(f'  2-Way Markets (de-vig\'d): {devig_yes}')
print(f'  Single-outcome (direct prob): {devig_no}')
print()

# Get 2-way market details
if devig_yes > 0:
    print('📈 2-WAY MARKETS DETECTED WITH DE-VIG:')
    for idx, row in df[df['uses_devig'] == True].iterrows():
        print(f'  {row["market_type"]} | {row["event_name"]}')
        print(f'    Reference (de-vig\'d): {row["prob_ref"]:.4f}')
        print(f'    Outlier: {row["outlier_books"]}')
    print()

print('📚 OUTLIER BREAKDOWN BY MARKET TYPE:')
for market, count in df['market_type'].value_counts().items():
    print(f'  {market}: {count}')
