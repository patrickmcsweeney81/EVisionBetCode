#!/usr/bin/env python3
import requests
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Check multiple sports to see where bet365/dabble/tabtouch appear
sports = ['americanfootball_nfl', 'basketball_nba', 'icehockey_nhl']

for sport in sports:
    print(f"\n{'='*60}")
    print(f"Sport: {sport}")
    print(f"{'='*60}")
    
    resp = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{sport}/odds',
        params={
            'apiKey': ODDS_API_KEY,
            'regions': 'au',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        },
        timeout=10
    )
    
    events = resp.json()
    if not events or len(events) == 0:
        print("No events found")
        continue
        
    # Collect all unique bookmaker keys across all events
    all_bookmakers = set()
    for e in events:
        for b in e.get('bookmakers', []):
            all_bookmakers.add(b['key'])
    
    print(f"Found {len(events)} events")
    print(f"Unique bookmakers across all events ({len(all_bookmakers)}):")
    for bk in sorted(all_bookmakers):
        print(f"  - {bk}")
    
    # Check for our target books
    targets = ['bet365', 'dabble', 'tabtouch']
    print(f"\nTarget AU bookmakers:")
    for t in targets:
        status = "✓ FOUND" if t in all_bookmakers else "✗ NOT FOUND"
        print(f"  {t:15s} {status}")
