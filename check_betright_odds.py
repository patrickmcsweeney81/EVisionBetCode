"""
Quick script to check BetRight's actual odds from The Odds API
to verify if they're returning bad data for Max Christie and Brandon Ingram
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ODDS_API_KEY')

# Fetch NBA events with player props
url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/events'
params = {
    'apiKey': api_key,
    'regions': 'au',
    'markets': 'player_threes',
    'oddsFormat': 'decimal'
}

print("Fetching odds from The Odds API...")
response = requests.get(url, params=params)
events = response.json()

print(f"Found {len(events)} events\n")

# Look for games with Knicks or Raptors
for event in events:
    home = event.get('home_team', '')
    away = event.get('away_team', '')
    
    if not (('Knicks' in home or 'Knicks' in away) or ('Raptors' in home or 'Raptors' in away)):
        continue
    
    print(f"{'='*80}")
    print(f"Event: {away} @ {home}")
    print(f"{'='*80}\n")
    
    # Find BetRight bookmaker
    betright_found = False
    for bookie in event.get('bookmakers', []):
        if bookie['key'] != 'betright':
            continue
        
        betright_found = True
        print("BetRight data:")
        
        for market in bookie.get('markets', []):
            if market['key'] != 'player_threes':
                continue
            
            # Organize by player and line
            players = {}
            for outcome in market.get('outcomes', []):
                player = outcome.get('description', '')
                point = outcome.get('point', 0)
                name = outcome.get('name', '')
                price = outcome.get('price', 0)
                
                if player not in players:
                    players[player] = {}
                if point not in players[player]:
                    players[player][point] = {}
                
                players[player][point][name] = price
            
            # Print Max Christie and Brandon Ingram specifically
            target_players = ['Max Christie', 'Brandon Ingram']
            
            for player_name in target_players:
                if player_name in players:
                    print(f"\n  {player_name}:")
                    for line in sorted(players[player_name].keys()):
                        over = players[player_name][line].get('Over', 'N/A')
                        under = players[player_name][line].get('Under', 'N/A')
                        print(f"    Line {line}: Over={over}, Under={under}")
                else:
                    print(f"\n  {player_name}: NO DATA FROM BETRIGHT")
    
    if not betright_found:
        print("BetRight: NOT AVAILABLE FOR THIS EVENT")
    
    print()

print(f"\nAPI Requests remaining: {response.headers.get('x-requests-remaining', 'Unknown')}")
