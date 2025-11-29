#!/usr/bin/env python3
"""Test fair price calculation with updated logic"""
import sys
sys.path.insert(0, 'c:\\EV_ARB Bot VSCode')

from ev_arb_bot import fetch_h2h_events, build_fair_prices, master_fair_odds

events = fetch_h2h_events('americanfootball_nfl')
print(f'Fetched {len(events)} NFL events\n')

if events:
    e = events[0]
    print(f'Event: {e["home_team"]} vs {e["away_team"]}\n')
    
    # H2H fair prices
    fair = build_fair_prices(e, 'h2h')
    print(f'H2H Fair prices calculated for {len(fair)} outcomes:')
    for k, v in fair.items():
        pin = v.get('pinnacle')
        bf = v.get('betfair')
        med = v.get('median')
        master = master_fair_odds(v)
        print(f'  {k}:')
        print(f'    Pinnacle: {f"{pin:.2f}" if pin and pin > 0 else "N/A"}')
        print(f'    Betfair:  {f"{bf:.2f}" if bf and bf > 0 else "N/A"}')
        print(f'    Median:   {f"{med:.2f}" if med and med > 0 else "N/A"}')
        print(f'    Master:   {f"{master:.2f}" if master > 0 else "N/A"}')
    
    # Try spreads
    print(f'\nSpreads fair prices:')
    fair_spreads = build_fair_prices(e, 'spreads', line=6.5)
    if fair_spreads:
        print(f'  Found {len(fair_spreads)} outcomes at line 6.5')
        for k, v in list(fair_spreads.items())[:2]:
            med = v.get('median')
            master = master_fair_odds(v)
            print(f'  {k}: median={med:.2f if med else "N/A"}, master={master:.2f if master > 0 else "N/A"}')
    else:
        print('  No fair prices calculated')
    
    # Try totals
    print(f'\nTotals fair prices:')
    fair_totals = build_fair_prices(e, 'totals', line=45.5)
    if fair_totals:
        print(f'  Found {len(fair_totals)} outcomes at line 45.5')
        for k, v in list(fair_totals.items())[:2]:
            med = v.get('median')
            master = master_fair_odds(v)
            print(f'  {k}: median={med:.2f if med else "N/A"}, master={master:.2f if master > 0 else "N/A"}')
    else:
        print('  No fair prices calculated')
