"""
Check BetRight API data for Chet Holmgren to see what The Odds API is actually returning
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ODDS_API_KEY')

# Fetch Sacramento vs OKC game
url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/events'
params = {
    'apiKey': api_key,
    'regions': 'au,us',
    'markets': 'player_assists,player_blocks,player_threes',
    'oddsFormat': 'decimal'
}

response = requests.get(url, params=params)
events = response.json()

print("Searching for Sacramento Kings @ Oklahoma City Thunder game...")
print("=" * 80)

for event in events:
    home = event.get('home_team', '')
    away = event.get('away_team', '')
    
    if 'Thunder' not in home and 'Thunder' not in away:
        continue
    
    print(f"\nFound: {away} @ {home}")
    print("=" * 80)
    
    # Find BetRight bookmaker
    for bookie in event.get('bookmakers', []):
        if bookie['key'] != 'betright':
            continue
        
        print(f"\nBetRight data:")
        
        for market in bookie.get('markets', []):
            market_key = market.get('key')
            
            if market_key not in ['player_assists', 'player_blocks', 'player_threes']:
                continue
            
            print(f"\n  Market: {market_key}")
            print(f"  {'='*76}")
            
            # Group by player
            players = {}
            for outcome in market.get('outcomes', []):
                player = outcome.get('description', '')
                point = outcome.get('point', 0)
                name = outcome.get('name', '')
                price = outcome.get('price', 0)
                
                if 'Holmgren' not in player:
                    continue
                
                key = f"{player} {point}"
                if key not in players:
                    players[key] = {}
                
                players[key][name] = price
            
            # Print Chet Holmgren specifically
            for player_line in sorted(players.keys()):
                if 'Holmgren' in player_line:
                    over = players[player_line].get('Over', 'N/A')
                    under = players[player_line].get('Under', 'N/A')
                    print(f"    {player_line:30s} Over: {over:6s} Under: {under:6s}")

print(f"\n\nAPI Requests remaining: {response.headers.get('x-requests-remaining')}")
