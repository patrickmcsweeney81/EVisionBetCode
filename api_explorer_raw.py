"""
VIEW RAW JSON - See exactly what the API returns
Usage: python api_explorer_raw.py
"""
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("ODDS_API_KEY", "")
API_HOST = "https://api.the-odds-api.com"

print("=" * 80)
print("  API EXPLORER - Raw JSON View")
print("=" * 80)

# Get one event
print("\n1️⃣  Fetching one NBA event...")
events_url = f"{API_HOST}/v4/sports/basketball_nba/events"
events_params = {"apiKey": API_KEY, "regions": "au,us,us2,eu"}
events_resp = requests.get(events_url, params=events_params, timeout=10)
events = events_resp.json()

if events:
    event = events[0]
    event_id = event["id"]
    
    print(f"   ✅ Found: {event['away_team']} @ {event['home_team']}")
    print(f"\n   RAW EVENT DATA:")
    print("   " + "-" * 76)
    print(json.dumps(event, indent=2)[:500] + "...")
    
    # Get odds for that event
    print(f"\n\n2️⃣  Fetching odds for {event['away_team']} @ {event['home_team']}...")
    odds_url = f"{API_HOST}/v4/sports/basketball_nba/events/{event_id}/odds"
    odds_params = {
        "apiKey": API_KEY,
        "regions": "au,us,us2,eu",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
    }
    odds_resp = requests.get(odds_url, params=odds_params, timeout=10)
    odds_data = odds_resp.json()
    
    print(f"   ✅ Got {len(odds_data.get('bookmakers', []))} bookmakers\n")
    
    # Show structure of one bookmaker
    if odds_data.get('bookmakers'):
        bm = odds_data['bookmakers'][0]
        print(f"   STRUCTURE: One Bookmaker ({bm['key']}):")
        print("   " + "-" * 76)
        print(json.dumps(bm, indent=2)[:800])
        print("\n   ...(truncated)")
    
    # List all books
    print(f"\n\n3️⃣  ALL BOOKMAKERS AVAILABLE:")
    print("   " + "-" * 76)
    for bm in odds_data.get('bookmakers', []):
        markets = [m['key'] for m in bm.get('markets', [])]
        print(f"   ✅ {bm['key']:20} - Markets: {', '.join(markets)}")
    
    # Save full JSON for reference
    output_file = "api_sample_response.json"
    with open(output_file, 'w') as f:
        json.dump(odds_data, f, indent=2)
    print(f"\n\n💾 Full response saved to: {output_file}")
    print(f"   (Open in VS Code to explore the complete structure)")

else:
    print("❌ No events found")
