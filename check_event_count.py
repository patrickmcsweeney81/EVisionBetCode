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
    'https://api.the-odds-api.com/v4/sports/upcoming/odds',
    params={
        'apiKey': ODDS_API_KEY,
        'regions': 'au,us',
        'markets': 'h2h,spreads,totals',
        'oddsFormat': 'decimal'
    },
    timeout=10
)

events = resp.json()
print(f'Total events returned: {len(events)}')

sports = {}
for e in events:
    sk = e.get('sport_key')
    sports[sk] = sports.get(sk, 0) + 1

print('\nEvents by sport:')
for k, v in sorted(sports.items()):
    print(f'  {k}: {v}')
    
# Check how many have h2h vs spreads/totals markets
h2h_count = 0
spreads_count = 0
totals_count = 0

for e in events:
    for bk in e.get('bookmakers', []):
        for m in bk.get('markets', []):
            mk = m.get('key')
            if mk == 'h2h':
                h2h_count += 1
                break
        for m in bk.get('markets', []):
            mk = m.get('key')
            if mk == 'spreads':
                spreads_count += 1
                break
        for m in bk.get('markets', []):
            mk = m.get('key')
            if mk == 'totals':
                totals_count += 1
                break

print(f'\nMarket availability (bookmaker instances):')
print(f'  h2h: {h2h_count}')
print(f'  spreads: {spreads_count}')
print(f'  totals: {totals_count}')
