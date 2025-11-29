"""
Test all market handlers (h2h, spreads, totals) in isolation.
This validates the modular architecture works correctly.
"""
import os
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.h2h_handler import process_h2h_event
from core.spreads_handler import process_spread_event
from core.totals_handler import process_totals_event


def test_all_markets():
    """Test all market handlers with live API data."""
    api_key = os.getenv("ODDS_API_KEY", "")
    if not api_key:
        print("ERROR: ODDS_API_KEY not set")
        return
    
    # Fetch NBA with all markets
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
    params = {
        "apiKey": api_key,
        "regions": "eu,us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }
    
    print("Fetching NBA markets (h2h, spreads, totals)...\n")
    resp = requests.get(url, params=params, timeout=30)
    
    if resp.status_code != 200:
        print(f"API error: {resp.status_code}")
        return
    
    events = resp.json()
    print(f"Found {len(events)} events\n")
    
    # Test first 3 events
    h2h_success = 0
    spreads_success = 0
    totals_success = 0
    
    for event in events[:3]:
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        
        print(f"\n{'='*70}")
        print(f"Event: {away_team} @ {home_team}")
        print(f"{'='*70}")
        
        # Test H2H
        h2h_result = process_h2h_event(event, home_team, away_team)
        if h2h_result:
            fair = h2h_result.get("fair", {})
            pinnacle = h2h_result.get("pinnacle", {})
            print(f"\n[OK] H2H:")
            print(f"  Pinnacle: {pinnacle.get('home'):.3f} / {pinnacle.get('away'):.3f}")
            print(f"  Fair:     {fair.get('home'):.3f} / {fair.get('away'):.3f}")
            h2h_success += 1
        else:
            print(f"\n[FAIL] H2H: No result")
        
        # Test Spreads (try common lines)
        spread_found = False
        for target_line in [-6.5, -5.5, -4.5, -3.5, -2.5, -1.5, 1.5, 2.5]:
            spread_result = process_spread_event(event, target_line, home_team, away_team)
            if spread_result:
                fair = spread_result.get("fair", {})
                pinnacle = spread_result.get("pinnacle", {})
                keys = spread_result.get("keys", {})
                print(f"\n[OK] Spreads (line {target_line}):")
                print(f"  Keys:     {keys.get('home')} / {keys.get('away')}")
                print(f"  Pinnacle: {pinnacle.get('home'):.3f} / {pinnacle.get('away'):.3f}")
                print(f"  Fair:     {fair.get('home'):.3f} / {fair.get('away'):.3f}")
                spreads_success += 1
                spread_found = True
                break
        
        if not spread_found:
            print(f"\n[FAIL] Spreads: No result")
        
        # Test Totals (try common lines)
        totals_found = False
        for target_line in [205.5, 210.5, 215.5, 220.5, 225.5, 230.5]:
            totals_result = process_totals_event(event, target_line)
            if totals_result:
                fair = totals_result.get("fair", {})
                pinnacle = totals_result.get("pinnacle", {})
                line = totals_result.get("line")
                print(f"\n[OK] Totals (line {line}):")
                print(f"  Pinnacle: O {pinnacle.get('over'):.3f} / U {pinnacle.get('under'):.3f}")
                print(f"  Fair:     O {fair.get('over'):.3f} / U {fair.get('under'):.3f}")
                totals_success += 1
                totals_found = True
                break
        
        if not totals_found:
            print(f"\n[FAIL] Totals: No result")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY:")
    print(f"  H2H success:     {h2h_success}/3 ({h2h_success/3*100:.0f}%)")
    print(f"  Spreads success: {spreads_success}/3 ({spreads_success/3*100:.0f}%)")
    print(f"  Totals success:  {totals_success}/3 ({totals_success/3*100:.0f}%)")
    print(f"  Overall:         {h2h_success+spreads_success+totals_success}/9 ({(h2h_success+spreads_success+totals_success)/9*100:.0f}%)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    test_all_markets()
