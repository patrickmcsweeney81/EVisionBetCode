"""
Simple check: What does The Odds API actually return?
"""
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ODDS_API_KEY')

print('Testing what The Odds API returns by default...\n')

# Test 1: events endpoint with no markets specified
url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/events'
params = {'apiKey': api_key}

response = requests.get(url, params=params)
events = response.json()

if events and len(events) > 0:
    event = events[0]
    print(f'Sample event: {event.get("away_team")} @ {event.get("home_team")}')
    print(f'Bookmakers: {len(event.get("bookmakers", []))}')
    
    if event.get('bookmakers'):
        bookie = event['bookmakers'][0]
        print(f'\nFirst bookmaker: {bookie.get("key")}')
        
        markets = bookie.get('markets', [])
        print(f'Number of markets: {len(markets)}')
        
        if markets:
            print('\nMarket keys available:')
            for m in markets:
                key = m.get('key')
                num_outcomes = len(m.get('outcomes', []))
                print(f'  - {key}: {num_outcomes} outcomes')

print(f'\n\nNow checking with explicit markets parameter...\n')

# Test 2: Specify all known markets
all_markets = 'h2h,spreads,totals,player_points,player_rebounds,player_assists,player_threes,player_blocks,player_steals,player_blocks_steals,player_points_rebounds_assists,player_points_rebounds,player_points_assists,player_rebounds_assists'

params2 = {
    'apiKey': api_key,
    'regions': 'au,us',
    'markets': all_markets
}

response2 = requests.get(url, params=params2)
events2 = response2.json()

if events2 and len(events2) > 0:
    event2 = events2[0]
    
    all_market_keys = set()
    for bookie in event2.get('bookmakers', []):
        for market in bookie.get('markets', []):
            all_market_keys.add(market.get('key'))
    
    print(f'Markets returned with explicit request:')
    for key in sorted(all_market_keys):
        print(f'  - {key}')

print(f'\n\nAPI Requests remaining: {response.headers.get("x-requests-remaining")}')
