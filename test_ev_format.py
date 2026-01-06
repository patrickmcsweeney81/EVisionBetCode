import pandas as pd

df = pd.read_csv('data/v3/extracts/basketball_nba_ev_full_20260106_124439.csv')
row = df.iloc[0]

print('Sample Row:')
print(f'Event: {row["event_name"]}')
print(f'Market: {row["market_type"]} {row["selection"]} @ {row["point"]}')
print(f'Best AU Book: {row["best_au_bookmaker"]}')
print(f'Best AU Odds: {row["best_au_odds_formatted"]}')
print(f'EV: {row["ev_percent_formatted"]}')
print(f'Total Books: {int(row["total_books"])}')
print(f'Fair Odds: {row["fair_odds_decimal"]:.2f}')
