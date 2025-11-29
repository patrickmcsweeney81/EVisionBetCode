"""
Check all available player prop markets for NBA from The Odds API
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ODDS_API_KEY')

# Use events endpoint for player props
url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/events'

# All possible player prop markets
player_markets = [
    'player_points',
    'player_rebounds', 
    'player_assists',
    'player_threes',
    'player_blocks',
    'player_steals',
    'player_blocks_steals',
    'player_points_rebounds_assists',
    'player_points_rebounds',
    'player_points_assists',
    'player_rebounds_assists',
    'player_double_double',
    'player_triple_double',
    'player_first_basket',
    'player_first_field_goal'
]

print('Checking NBA Player Prop Markets')
print('=' * 80)

available_markets = []

for market in player_markets:
    params = {
        'apiKey': api_key,
        'regions': 'au,us',
        'markets': market,
        'oddsFormat': 'decimal'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        events = response.json()
        
        if events and len(events) > 0:
            event = events[0]
            bookmakers = event.get('bookmakers', [])
            
            if bookmakers:
                has_market = False
                num_books = 0
                num_players = 0
                
                for bookie in bookmakers:
                    markets_data = bookie.get('markets', [])
                    for m in markets_data:
                        if m.get('key') == market:
                            has_market = True
                            num_books += 1
                            outcomes = m.get('outcomes', [])
                            players = set([o.get('description', '') for o in outcomes])
                            num_players = max(num_players, len(players))
                
                if has_market:
                    available_markets.append(market)
                    print(f'✓ {market:40s} - {num_books:2d} bookmakers, ~{num_players:3d} players')
                else:
                    print(f'✗ {market:40s} - No data')
            else:
                print(f'✗ {market:40s} - No bookmakers')
        else:
            print(f'✗ {market:40s} - No events')
    else:
        print(f'✗ {market:40s} - Error {response.status_code}')

print('\n' + '=' * 80)
print(f'\nAVAILABLE NBA MARKETS ({len(available_markets)}):\n')
print('Main Markets:')
print('  - h2h')
print('  - spreads')
print('  - totals')
print('\nPlayer Props:')
for market in available_markets:
    print(f'  - {market}')

print(f'\n\nAPI Requests remaining: {response.headers.get("x-requests-remaining", "Unknown")}')
print(f'Requests used: ~{len(player_markets)}')
