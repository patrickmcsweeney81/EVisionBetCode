#!/usr/bin/env python3
"""Investigate suspicious soccer totals EV calculations"""
import sys
sys.path.insert(0, 'c:\\EV_ARB Bot VSCode')

from ev_arb_bot import fetch_h2h_events, build_fair_prices, master_fair_odds

# Fetch soccer events
resp_italy = fetch_h2h_events('soccer_italy_serie_a')
resp_turkey = fetch_h2h_events('soccer_turkey_super_league')

print("="*70)
print("INVESTIGATING SOCCER TOTALS FAIR PRICING")
print("="*70)

for events, label in [(resp_italy, "Serie A"), (resp_turkey, "Turkey Super League")]:
    if not events:
        continue
        
    e = events[0]
    print(f"\n{label}: {e['home_team']} vs {e['away_team']}")
    
    # Check what bookmakers have totals markets
    totals_books = []
    for bk in e.get('bookmakers', []):
        for m in bk.get('markets', []):
            if m['key'] == 'totals':
                totals_books.append(bk['key'])
                break
    
    print(f"Bookmakers with totals market: {len(totals_books)}")
    print(f"  {totals_books[:10]}")
    
    # Get fair prices for a common totals line
    lines = set()
    for bk in e.get('bookmakers', []):
        for m in bk.get('markets', []):
            if m['key'] == 'totals':
                outs = m.get('outcomes', [])
                if len(outs) == 2:
                    pt = outs[0].get('point')
                    if pt:
                        lines.add(float(pt))
    
    if lines:
        common_line = sorted(lines)[0]
        print(f"\nChecking line: {common_line}")
        
        fair = build_fair_prices(e, 'totals', line=common_line)
        print(f"Fair prices calculated for {len(fair)} outcomes:")
        
        for k, v in fair.items():
            pin = v.get('pinnacle')
            bf = v.get('betfair')
            med = v.get('median')
            master = master_fair_odds(v)
            print(f"  {k}:")
            print(f"    Pinnacle: {f'${pin:.2f}' if pin and pin > 0 else 'N/A'}")
            print(f"    Betfair:  {f'${bf:.2f}' if bf and bf > 0 else 'N/A'}")
            print(f"    Median:   {f'${med:.2f}' if med and med > 0 else 'N/A'}")
            print(f"    Master:   {f'${master:.2f}' if master > 0 else 'N/A'}")
        
        # Check actual AU bookmaker prices
        print(f"\nAU Bookmaker prices at line {common_line}:")
        au_books = ['sportsbet', 'pointsbetau', 'tab', 'unibet', 'tabtouch']
        for bk in e.get('bookmakers', []):
            if bk['key'] not in au_books:
                continue
            for m in bk.get('markets', []):
                if m['key'] == 'totals':
                    outs = m.get('outcomes', [])
                    if len(outs) == 2 and outs[0].get('point') == common_line:
                        print(f"  {bk['key']:15s} Over: ${outs[0]['price']:.2f}  Under: ${outs[1]['price']:.2f}")
