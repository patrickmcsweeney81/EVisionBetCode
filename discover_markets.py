"""
Discover available betting markets for each sport from The Odds API.
Uses the /events and /markets endpoints to find what prop markets exist.
"""

import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment
load_dotenv()
API_KEY = os.getenv("ODDS_API_KEY", "")

# Sports to check (from main list)
SPORTS_TO_CHECK = [
    "basketball_nba",
    "basketball_nbl",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "icehockey_nhl",
    "baseball_mlb",
    "soccer_epl",
    "soccer_uefa_champs_league",
]

REGIONS = "us,au"  # Check US and AU regions for market availability


def get_events(sport_key):
    """Get upcoming events for a sport."""
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events"
    params = {"apiKey": API_KEY}
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        events = resp.json()
        return events
    except Exception as e:
        print(f"  [!] Error fetching events for {sport_key}: {e}")
        return []


def get_markets_for_event(sport_key, event_id):
    """Get available markets for a specific event."""
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/markets"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract unique market keys across all bookmakers
        all_markets = set()
        for bookmaker in data.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                all_markets.add(market.get("key"))
        
        return sorted(all_markets)
    except Exception as e:
        print(f"  [!] Error fetching markets for event {event_id}: {e}")
        return []


def main():
    """Discover markets for all sports."""
    print("=" * 80)
    print("MARKET DISCOVERY FOR ALL SPORTS")
    print("=" * 80)
    print()
    
    if not API_KEY:
        print("[!] ODDS_API_KEY not set in .env")
        return
    
    results = {}
    
    for sport_key in SPORTS_TO_CHECK:
        print(f"\n{'='*80}")
        print(f"SPORT: {sport_key.upper()}")
        print(f"{'='*80}")
        
        # Get events
        events = get_events(sport_key)
        if not events:
            print(f"  [!] No events found for {sport_key}")
            results[sport_key] = {"error": "No events found"}
            continue
        
        print(f"  [OK] Found {len(events)} events")
        
        # Get markets for first event (sample)
        event = events[0]
        event_id = event.get("id")
        home_team = event.get("home_team", "Unknown")
        away_team = event.get("away_team", "Unknown")
        
        print(f"  [*] Checking markets for: {away_team} @ {home_team}")
        
        markets = get_markets_for_event(sport_key, event_id)
        
        if not markets:
            print(f"  [!] No markets found")
            results[sport_key] = {"error": "No markets returned"}
            continue
        
        # Categorize markets
        core_markets = [m for m in markets if m in ["h2h", "h2h_lay", "spreads", "totals"]]
        prop_markets = [m for m in markets if m.startswith("player_") or m.startswith("batter_") or m.startswith("pitcher_")]
        alternate_markets = [m for m in markets if "alternate" in m]
        period_markets = [m for m in markets if any(x in m for x in ["_q1", "_q2", "_q3", "_q4", "_h1", "_h2", "_period"])]
        other_markets = [m for m in markets if m not in core_markets + prop_markets + alternate_markets + period_markets]
        
        print(f"\n  [SUMMARY] Total markets: {len(markets)}")
        print(f"    Core markets ({len(core_markets)}): {', '.join(core_markets)}")
        print(f"    Player props ({len(prop_markets)}): {', '.join(prop_markets[:10])}{' ...' if len(prop_markets) > 10 else ''}")
        print(f"    Alternate lines ({len(alternate_markets)}): {', '.join(alternate_markets[:5])}{' ...' if len(alternate_markets) > 5 else ''}")
        print(f"    Period/Quarter ({len(period_markets)}): {', '.join(period_markets[:5])}{' ...' if len(period_markets) > 5 else ''}")
        print(f"    Other ({len(other_markets)}): {', '.join(other_markets[:5])}{' ...' if len(other_markets) > 5 else ''}")
        
        results[sport_key] = {
            "total_events": len(events),
            "sample_event": f"{away_team} @ {home_team}",
            "total_markets": len(markets),
            "core_markets": core_markets,
            "player_props": prop_markets,
            "alternate_markets": alternate_markets,
            "period_markets": period_markets,
            "other_markets": other_markets,
        }
    
    # Save results to JSON
    output_file = Path("data/market_discovery.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"RESULTS SAVED TO: {output_file}")
    print("=" * 80)
    
    # Print summary
    print("\n" + "=" * 80)
    print("PROP MARKET SUMMARY (for extract_odds.py)")
    print("=" * 80)
    
    for sport_key, data in results.items():
        if "error" in data:
            continue
        props = data.get("player_props", [])
        if props:
            print(f"\n{sport_key.upper()}_PROPS = [")
            for prop in props[:15]:  # Top 15 most likely liquid
                print(f'    "{prop}",')
            if len(props) > 15:
                print(f"    # ... +{len(props)-15} more markets")
            print("]")


if __name__ == "__main__":
    main()
