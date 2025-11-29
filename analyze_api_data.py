#!/usr/bin/env python3
"""
Comprehensive API response analyzer - understand ALL data received
"""
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
print(f'='*70)
print(f'NFL EVENTS ANALYSIS - Total: {len(events)} events')
print(f'='*70)

# Categorize bookmakers by type
sharp_books = {'pinnacle', 'betfair', 'betfair_ex_au', 'betfair_ex_uk'}
au_books = set()
us_books = set()
other_books = set()

# Collect all unique bookmaker keys across all events
all_bookmakers = set()
bookmaker_market_count = defaultdict(lambda: {'h2h': 0, 'spreads': 0, 'totals': 0})

for e in events:
    for bk in e.get('bookmakers', []):
        bkey = bk['key']
        all_bookmakers.add(bkey)
        
        # Categorize
        if '_au' in bkey or bkey in ['sportsbet', 'neds', 'tab', 'playup', 'betright', 'boombet', 'ladbrokes']:
            au_books.add(bkey)
        elif '_us' in bkey or bkey in ['draftkings', 'fanduel', 'betmgm', 'williamhill', 'bovada', 'mybookieag', 'betrivers', 'espnbet', 'fliff', 'sisportsbook', 'wynnbet']:
            us_books.add(bkey)
        elif bkey in sharp_books:
            pass  # Will list separately
        else:
            other_books.add(bkey)
        
        # Count markets
        for m in bk.get('markets', []):
            mk = m['key']
            if mk in ['h2h', 'spreads', 'totals']:
                bookmaker_market_count[bkey][mk] += 1

print(f'\n{"BOOKMAKER CATEGORIZATION":^70}')
print(f'{"-"*70}')
print(f'\nSHARP BOOKS ({len(sharp_books & all_bookmakers)}):')
for bk in sorted(sharp_books & all_bookmakers):
    counts = bookmaker_market_count[bk]
    print(f'  {bk:25s} h2h:{counts["h2h"]:3d}  spreads:{counts["spreads"]:3d}  totals:{counts["totals"]:3d}')

print(f'\nAUSTRALIAN BOOKS ({len(au_books)}):')
for bk in sorted(au_books):
    counts = bookmaker_market_count[bk]
    print(f'  {bk:25s} h2h:{counts["h2h"]:3d}  spreads:{counts["spreads"]:3d}  totals:{counts["totals"]:3d}')

print(f'\nUS BOOKS ({len(us_books)}):')
for bk in sorted(us_books):
    counts = bookmaker_market_count[bk]
    print(f'  {bk:25s} h2h:{counts["h2h"]:3d}  spreads:{counts["spreads"]:3d}  totals:{counts["totals"]:3d}')

if other_books:
    print(f'\nOTHER BOOKS ({len(other_books)}):')
    for bk in sorted(other_books):
        counts = bookmaker_market_count[bk]
        print(f'  {bk:25s} h2h:{counts["h2h"]:3d}  spreads:{counts["spreads"]:3d}  totals:{counts["totals"]:3d}')

# Analyze one event in detail
print(f'\n{"DETAILED EVENT ANALYSIS":^70}')
print(f'{"-"*70}')
if events:
    e = events[0]
    print(f'\nEvent: {e["home_team"]} vs {e["away_team"]}')
    print(f'Sport: {e["sport_key"]}')
    print(f'Commence: {e["commence_time"]}')
    
    print(f'\nBookmakers present: {len(e.get("bookmakers", []))}')
    
    sharp_present = []
    au_present = []
    us_present = []
    
    for bk in e.get('bookmakers', []):
        bkey = bk['key']
        if bkey in sharp_books:
            sharp_present.append(bkey)
        elif bkey in au_books:
            au_present.append(bkey)
        elif bkey in us_books:
            us_present.append(bkey)
    
    print(f'  Sharp: {len(sharp_present)} - {sorted(sharp_present)}')
    print(f'  AU: {len(au_present)} - {sorted(au_present)}')
    print(f'  US: {len(us_present)} - {sorted(us_present)}')
    
    # Sample odds for h2h
    print(f'\nH2H ODDS COMPARISON:')
    print(f'{"Bookmaker":25s} {"Home":>8s} {"Away":>8s}')
    print(f'{"-"*45}')
    for bk in e.get('bookmakers', [])[:8]:
        bkey = bk['key']
        h2h = next((m for m in bk.get('markets', []) if m['key'] == 'h2h'), None)
        if h2h and len(h2h.get('outcomes', [])) == 2:
            outs = {o['name']: o['price'] for o in h2h['outcomes']}
            home_price = outs.get(e['home_team'], 0)
            away_price = outs.get(e['away_team'], 0)
            marker = '  [SHARP]' if bkey in sharp_books else ('  [AU]' if bkey in au_books else '')
            print(f'{bkey:25s} ${home_price:7.2f} ${away_price:7.2f}{marker}')

print(f'\n{"RECOMMENDATION":^70}')
print(f'{"-"*70}')
print(f'\n1. Use ALL bookmakers (AU + US + Sharp) to compute fair prices')
print(f'   - More data = better fair price accuracy')
print(f'   - Sharp books (Pinnacle, Betfair) are most important')
print(f'\n2. Only evaluate AU bookmakers for actual betting opportunities')
print(f'   - These are the books you can actually place bets with')
print(f'\n3. Current setup should:')
print(f'   - Collect odds from {len(all_bookmakers)} bookmakers')
print(f'   - Compute fair prices using sharp + median of all books')
print(f'   - Find EV edges by comparing AU book odds to fair prices')
