"""
Deep Research: Test all possible market types for Neds
======================================================
Try requesting specific markets one at a time to see what Neds actually offers.

Usage:
    python deep_research_neds.py
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"

# All possible market types
ALL_MARKET_TYPES = [
    'h2h',
    'spreads',
    'totals',
    'alternate_spreads',
    'alternate_totals',
    'player_points',
    'player_assists',
    'player_rebounds',
    'player_passes',
    'player_threes',
    'player_field_goals',
    'player_turnovers',
    'player_steals',
    'player_blocks',
    'player_fouls',
]

def test_market(event_id, market_type):
    """Test if Neds offers a specific market."""
    url = f"{BASE_URL}/sports/{SPORT}/events/{event_id}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'bookmakers': 'neds',
        'markets': market_type,
        'oddsFormat': 'decimal'
    }
    
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        
        bookmakers = data.get('bookmakers', [])
        for bm in bookmakers:
            if bm.get('key') == 'neds':
                markets = bm.get('markets', [])
                if markets:
                    outcomes_count = sum(len(m.get('outcomes', [])) for m in markets)
                    return True, outcomes_count
        return False, 0
    except:
        return False, 0

def deep_research():
    """Deep research into Neds market availability."""
    
    print("🔬 DEEP NEDS MARKET RESEARCH\n")
    print("Testing all possible market types...\n")
    
    # Get first event
    events_url = f"{BASE_URL}/sports/{SPORT}/events"
    events_params = {'apiKey': ODDS_API_KEY, 'regions': 'au,us,us2,eu'}
    
    resp = requests.get(events_url, params=events_params, timeout=20)
    events = resp.json()
    
    if not events:
        print("No events found")
        return
    
    event_id = events[0]['id']
    event_name = f"{events[0]['away_team']} @ {events[0]['home_team']}"
    
    print(f"Testing against: {event_name}\n")
    print("Market Type                    Available  Outcomes")
    print("-" * 55)
    
    available_markets = []
    
    for market in ALL_MARKET_TYPES:
        found, count = test_market(event_id, market)
        status = "✅ YES" if found else "❌ NO"
        outcome_str = f"({count})" if found else ""
        print(f"  {market:<28} {status:<10} {outcome_str}")
        
        if found:
            available_markets.append((market, count))
    
    print("\n" + "=" * 55)
    print(f"\n✅ SUMMARY: Neds offers {len(available_markets)} market type(s)\n")
    
    if available_markets:
        print("Available markets:")
        for market, count in available_markets:
            print(f"  • {market:<28} ({count} outcomes)")
    else:
        print("⚠️  Only H2H market is available on The Odds API for Neds")
    
    print("\n" + "=" * 55)
    print("\n💡 NOTE: This is API availability, not Neds limitation.")
    print("   The Odds API may only provide H2H for Neds.")
    print("   Check The Odds API documentation for Neds coverage.")

if __name__ == "__main__":
    deep_research()
