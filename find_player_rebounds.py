"""
Find player name for highest EV line and check for Over counterpart
"""
import pandas as pd

# Load EV data
df = pd.read_csv('data/v3/extracts/basketball_nba_ev_full.csv')

# Find the specific line
target = df[(df['event_name'] == 'Miami Heat @ Minnesota Timberwolves') & 
            (df['market_type'] == 'player_rebounds') & 
            (df['selection'] == 'Under') & 
            (df['point'] == 9.5)]

if not target.empty:
    row = target.iloc[0]
    player = row['player_name']
    event_name = row['event_name']
    
    print('UNDER 9.5 REBOUNDS')
    print('='*60)
    print(f'Player: {player}')
    print(f'Event: {event_name}')
    print(f'Market: {row["market_type"]}')
    print(f'Selection: {row["selection"]} {row["point"]}')
    print(f'Fair Odds: {row["fair_odds_decimal"]:.4f}')
    print(f'Best AU Odds: {row["best_au_odds_decimal"]:.4f} ({row["best_au_bookmaker"]})')
    print(f'EV: {row["ev_percent"]:.2f}%')
    print()
    
    # Now find Over for same player
    print('SEARCHING FOR OPPOSITE (OVER 9.5)...')
    print('='*60)
    over_line = df[(df['event_name'] == event_name) & 
                   (df['market_type'] == 'player_rebounds') & 
                   (df['player_name'] == player) & 
                   (df['selection'] == 'Over') & 
                   (df['point'] == 9.5)]
    
    if not over_line.empty:
        over_row = over_line.iloc[0]
        print(f'Player: {over_row["player_name"]}')
        print(f'Event: {event_name}')
        print(f'Market: {over_row["market_type"]}')
        print(f'Selection: {over_row["selection"]} {over_row["point"]}')
        print(f'Fair Odds: {over_row["fair_odds_decimal"]:.4f}')
        print(f'Best AU Odds: {over_row["best_au_odds_decimal"]:.4f} ({over_row["best_au_bookmaker"]})')
        print(f'EV: {over_row["ev_percent"]:.2f}%')
    else:
        print('❌ Over 9.5 NOT found in filtered data')
        print()
        print('All player_rebounds lines for this event:')
        all_rebounds = df[(df['event_name'] == event_name) & 
                         (df['market_type'] == 'player_rebounds')]
        for _, r in all_rebounds.iterrows():
            print(f'  {r["player_name"]:20s} {r["selection"]:6s} {r["point"]:5.1f} - EV: {r["ev_percent"]:6.2f}%')
else:
    print('❌ Line not found')
