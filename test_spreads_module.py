"""
Test spreads handler in isolation.
This script tests ONLY the spreads logic without touching the monolithic bot.
"""
import os
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.spreads_handler import process_spread_event


def test_spreads():
    """Test spreads handler with live API data."""
    api_key = os.getenv("ODDS_API_KEY", "")
    if not api_key:
        print("ERROR: ODDS_API_KEY not set")
        return
    
    # Fetch NBA spreads
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
    params = {
        "apiKey": api_key,
        "regions": "eu,us",  # Pinnacle in EU region
        "markets": "spreads",
        "oddsFormat": "decimal"
    }
    
    print("Fetching NBA spreads...")
    resp = requests.get(url, params=params, timeout=30)
    
    if resp.status_code != 200:
        print(f"API error: {resp.status_code}")
        return
    
    events = resp.json()
    print(f"Found {len(events)} events\n")
    
    # Process first 3 events
    success_count = 0
    zero_fair_count = 0
    
    for event in events[:5]:
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        
        print(f"\n{'='*60}")
        print(f"Event: {away_team} @ {home_team}")
        
        # Try common spread lines
        for target_line in [-6.5, -5.5, -4.5, -3.5, -2.5, -1.5]:
            result = process_spread_event(
                event,
                target_line,
                home_team,
                away_team,
                betfair_commission=0.06
            )
            
            if result:
                fair = result.get("fair", {})
                pinnacle = result.get("pinnacle", {})
                
                fair_home = fair.get("home", 0)
                fair_away = fair.get("away", 0)
                
                if fair_home > 0 and fair_away > 0:
                    print(f"  Line {target_line}:")
                    print(f"    Pinnacle: {pinnacle.get('home'):.3f} / {pinnacle.get('away'):.3f}")
                    print(f"    Fair:     {fair_home:.3f} / {fair_away:.3f}")
                    success_count += 1
                else:
                    print(f"  Line {target_line}: ZERO FAIR (fair_home={fair_home}, fair_away={fair_away})")
                    zero_fair_count += 1
                
                break  # Found valid line, move to next event
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Success: {success_count} events with non-zero fair prices")
    print(f"  Zero-fair: {zero_fair_count} events")
    print(f"  Success rate: {success_count / max(1, success_count + zero_fair_count) * 100:.1f}%")


if __name__ == "__main__":
    test_spreads()
