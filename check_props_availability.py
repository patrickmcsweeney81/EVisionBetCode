"""
Check which NBA games currently have player props available
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ODDS_API_KEY')

url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/events'
params = {
    'apiKey': api_key,
    'regions': 'au,us',
    'markets': 'player_points,player_assists,player_rebounds,player_threes'
}

response = requests.get(url, params=params)
events = response.json()

print(f'Total NBA events: {len(events)}')
print('=' * 100)

events_with_props = 0

for event in events:
    away = event.get('away_team', '')
    home = event.get('home_team', '')
    commence = event.get('commence_time', '')
    bookmakers = event.get('bookmakers', [])
    
    prop_count = sum(1 for b in bookmakers if b.get('markets'))
    
    if prop_count > 0:
        events_with_props += 1
        print(f'✓ {away:25s} @ {home:25s} | {commence} | {prop_count} bookmakers with props')
    else:
        print(f'✗ {away:25s} @ {home:25s} | {commence} | No props')

print('=' * 100)
print(f'\nSummary: {events_with_props}/{len(events)} events have player props')
print(f'\nAPI Requests remaining: {response.headers.get("x-requests-remaining")}')

# If no props, check what markets ARE available
if events_with_props == 0:
    print('\n\nChecking what markets ARE available...\n')
    
    params2 = {'apiKey': api_key, 'regions': 'au,us', 'markets': 'h2h,spreads,totals'}
    response2 = requests.get(url, params=params2)
    events2 = response2.json()
    
    if events2 and len(events2) > 0:
        event = events2[0]
        print(f'Sample: {event.get("away_team")} @ {event.get("home_team")}')
        print(f'Bookmakers for h2h/spreads/totals: {len(event.get("bookmakers", []))}')
        
        if event.get('bookmakers'):
            markets = set()
            for b in event['bookmakers']:
                for m in b.get('markets', []):
                    markets.add(m.get('key'))
            print(f'Available markets: {sorted(markets)}')
