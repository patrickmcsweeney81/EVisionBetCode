#!/usr/bin/env python3
"""Check what market keys AU bookmakers actually return"""
import requests
import os
from collections import defaultdict

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

# Collect ALL unique market keys per bookmaker
au_bookmaker_markets = defaultdict(set)

au_books = ['sportsbet', 'pointsbetau', 'ladbrokes_au', 'neds', 'tab', 'tabtouch', 
            'unibet', 'betr_au', 'bet365', 'dabble_au', 'boombet', 'playup', 
            'betright', 'betfair_ex_au']

print('='*70)
print('AU BOOKMAKER MARKET KEYS')
print('='*70)

for e in events:
    for bk in e.get('bookmakers', []):
        bkey = bk['key']
        if bkey in au_books or '_au' in bkey:
            for m in bk.get('markets', []):
                au_bookmaker_markets[bkey].add(m['key'])

print('\nAU Bookmakers and their market keys:\n')
for bkey in sorted(au_bookmaker_markets.keys()):
    markets = sorted(au_bookmaker_markets[bkey])
    print(f'{bkey:20s} {markets}')

# Now check if ANY AU book has markets other than h2h/spreads/totals
print('\n' + '='*70)
print('UNUSUAL MARKET KEYS (not h2h/spreads/totals)')
print('='*70)

for bkey in sorted(au_bookmaker_markets.keys()):
    unusual = [m for m in au_bookmaker_markets[bkey] if m not in ['h2h', 'spreads', 'totals']]
    if unusual:
        print(f'{bkey:20s} {unusual}')

# Check one event in detail to see actual market structure
print('\n' + '='*70)
print('DETAILED MARKET INSPECTION - First NFL Event')
print('='*70)

if events:
    e = events[0]
    print(f"\nEvent: {e['home_team']} vs {e['away_team']}\n")
    
    for bk in e.get('bookmakers', []):
        bkey = bk['key']
        if bkey in au_books or '_au' in bkey:
            print(f'\n{bkey}:')
            for m in bk.get('markets', []):
                mk = m['key']
                outs = m.get('outcomes', [])
                print(f'  Market: {mk} ({len(outs)} outcomes)')
                for o in outs[:2]:  # Show first 2 outcomes
                    point = o.get('point', 'N/A')
                    print(f'    {o["name"]} @ {point}: ${o["price"]}')
