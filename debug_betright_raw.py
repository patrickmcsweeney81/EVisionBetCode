#!/usr/bin/env python3
"""
Check raw BetRight data from API for Chet Holmgren to see if API returns
same 4.33 odds on multiple markets or if it's our parsing.
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_BASE = os.getenv("ODDS_API_BASE", "https://api.the-odds-api.com/v4")

# Get upcoming NBA games
sport = "basketball_nba"
regions = "au"
markets = "player_assists,player_blocks,player_threes"

url = f"{ODDS_API_BASE}/sports/{sport}/events/"
params = {
    "apiKey": ODDS_API_KEY,
    "regions": regions,
    "markets": markets,
    "oddsFormat": "decimal",
    "bookmakers": "betright"
}

print(f"Fetching BetRight odds for NBA player props...")
print(f"Markets: {markets}")
print()

response = requests.get(url, params=params, timeout=30)
print(f"Status: {response.status_code}")
print(f"Remaining requests: {response.headers.get('x-requests-remaining', 'N/A')}")
print()

if response.status_code != 200:
    print(f"Error: {response.text}")
    exit(1)

events = response.json()
print(f"Found {len(events)} events")
print()

# Find Chet Holmgren
for event in events:
    home = event.get("home_team", "")
    away = event.get("away_team", "")
    
    # Look for OKC game
    if "Thunder" not in home and "Thunder" not in away:
        continue
    
    print(f"{'='*80}")
    print(f"Event: {away} @ {home}")
    print(f"ID: {event.get('id')}")
    print(f"Commence: {event.get('commence_time')}")
    print(f"{'='*80}")
    
    bookmakers = event.get("bookmakers", [])
    
    for bk in bookmakers:
        bk_key = bk.get("key", "")
        if bk_key != "betright":
            continue
        
        print(f"\n{bk_key.upper()}:")
        markets = bk.get("markets", [])
        
        for market in markets:
            market_key = market.get("key", "")
            print(f"\n  Market: {market_key}")
            
            outcomes = market.get("outcomes", [])
            for out in outcomes:
                desc = out.get("description", "")
                if "Chet" not in desc and "Holmgren" not in desc:
                    continue
                
                name = out.get("name", "")
                point = out.get("point", "")
                price = out.get("price", "")
                
                print(f"    {desc:30s} {name:5s} {point:4} @ {price}")
        
        print()

print("\n" + "="*80)
print("Raw JSON for BetRight bookmaker (Chet Holmgren only):")
print("="*80)

for event in events:
    home = event.get("home_team", "")
    away = event.get("away_team", "")
    
    if "Thunder" not in home and "Thunder" not in away:
        continue
    
    for bk in event.get("bookmakers", []):
        if bk.get("key") != "betright":
            continue
        
        # Filter to only Chet Holmgren outcomes
        filtered_markets = []
        for market in bk.get("markets", []):
            filtered_outcomes = []
            for out in market.get("outcomes", []):
                if "Chet" in out.get("description", "") or "Holmgren" in out.get("description", ""):
                    filtered_outcomes.append(out)
            
            if filtered_outcomes:
                filtered_market = {
                    "key": market.get("key"),
                    "outcomes": filtered_outcomes
                }
                filtered_markets.append(filtered_market)
        
        print(json.dumps(filtered_markets, indent=2))
