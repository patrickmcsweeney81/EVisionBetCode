#!/usr/bin/env python3
import requests
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

resp = requests.get(
    'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds',
    params={
        'apiKey': ODDS_API_KEY,
        'regions': 'au,us',
        'markets': 'h2h,spreads,totals',
        'oddsFormat': 'decimal'
    },
    timeout=10
)

events = resp.json()
print(f'Found {len(events)} NFL events\n')

# Check first event for spreads/totals availability
if events:
    e = events[0]
    print(f"Event: {e['home_team']} vs {e['away_team']}\n")
    
    for bk in e.get('bookmakers', [])[:5]:  # Check first 5 bookmakers
        print(f"Bookmaker: {bk['key']}")
        for m in bk.get('markets', []):
            mk = m['key']
            outs = m.get('outcomes', [])
            if mk in ['spreads', 'totals']:
                print(f"  {mk}: {len(outs)} outcomes")
                for o in outs[:2]:
                    point = o.get('point', 'N/A')
                    print(f"    {o['name']} @ {point}: ${o['price']}")
        print()
