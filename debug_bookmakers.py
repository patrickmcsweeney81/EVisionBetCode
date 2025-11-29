#!/usr/bin/env python3
import requests
import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

resp = requests.get(
    'https://api.the-odds-api.com/v4/sports/basketball_nba/odds',
    params={
        'apiKey': ODDS_API_KEY,
        'regions': 'au,us,eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    },
    timeout=10
)

events = resp.json()
print(f'Found {len(events)} NBA events\n')

for e in events[:1]:
    print(f"Event: {e['home_team']} vs {e['away_team']}")
    bookmakers = [b['key'] for b in e.get('bookmakers', [])]
    print(f"\nAll bookmakers in API ({len(bookmakers)}):")
    for bk in bookmakers:
        print(f"  - {bk}")
    
    print(f"\n🔍 SHARP BOOKMAKERS CHECK:")
    sharp_books = ["pinnacle", "betfair_ex_eu", "betfair_ex_au"]
    for bk in sharp_books:
        status = "✓ PRESENT" if bk in bookmakers else "✗ MISSING"
        print(f"  {bk:20s} {status}")
    
    print(f"\n🎯 AU BOOKMAKERS CHECK:")
    au_books = ["sportsbet", "pointsbetau", "ladbrokes_au", "neds", "tab", 
                "unibet", "boombet", "playup", "betright", "bluebet", "topsport"]
    for bk in au_books:
        status = "✓ PRESENT" if bk in bookmakers else "✗ MISSING"
        print(f"  {bk:20s} {status}")
    
    print(f"\nSample odds from first bookmaker ({e['bookmakers'][0]['key']}):")
    first_bm = e['bookmakers'][0]
    h2h = next((m for m in first_bm.get('markets', []) if m['key'] == 'h2h'), None)
    if h2h:
        for out in h2h.get('outcomes', []):
            print(f"  {out['name']}: ${out['price']}")
