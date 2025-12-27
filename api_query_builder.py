"""
API QUERY BUILDER - Test custom queries
Modify params below and run to see what data you get
"""
import os
import json
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("ODDS_API_KEY", "")
API_HOST = "https://api.the-odds-api.com"

# ============================================================================
# CUSTOMIZE THESE PARAMETERS
# ============================================================================

SPORT = "basketball_nba"           # Or: "americanfootball_nfl", "icehockey_nhl", etc.
REGIONS = "au,us,us2,eu"           # Comma-separated: au, us, us2, eu, uk, br, in
MARKETS = "h2h,spreads,totals"     # What markets to fetch
ODDS_FORMAT = "decimal"             # Or: "american", "fractional"

# ============================================================================

print("=" * 80)
print("  API QUERY BUILDER")
print("=" * 80)

print(f"\n📋 QUERY PARAMS:")
print(f"   Sport:     {SPORT}")
print(f"   Regions:   {REGIONS}")
print(f"   Markets:   {MARKETS}")
print(f"   Format:    {ODDS_FORMAT}")

# Get events
print(f"\n🔄 Fetching events...")
events_url = f"{API_HOST}/v4/sports/{SPORT}/events"
events_params = {
    "apiKey": API_KEY,
    "regions": REGIONS,
}

try:
    events_resp = requests.get(events_url, params=events_params, timeout=10)
    events = events_resp.json()
    print(f"   ✅ Found {len(events)} events")
    
    if events:
        # Show first event
        event = events[0]
        print(f"\n📌 FIRST EVENT:")
        print(f"   {event['away_team']} @ {event['home_team']}")
        print(f"   Start: {event['commence_time']}")
        print(f"   ID: {event['id']}")
        
        # Get odds
        event_id = event['id']
        print(f"\n🔄 Fetching odds for this event...")
        odds_url = f"{API_HOST}/v4/sports/{SPORT}/events/{event_id}/odds"
        odds_params = {
            "apiKey": API_KEY,
            "regions": REGIONS,
            "markets": MARKETS,
            "oddsFormat": ODDS_FORMAT,
        }
        
        odds_resp = requests.get(odds_url, params=odds_params, timeout=10)
        odds_data = odds_resp.json()
        
        bookmakers = odds_data.get('bookmakers', [])
        print(f"   ✅ Got {len(bookmakers)} bookmakers with odds\n")
        
        # Create summary table
        print("📊 BOOKMAKERS & MARKET COVERAGE:")
        print("-" * 80)
        
        bm_data = []
        for bm in bookmakers:
            markets_list = [m['key'] for m in bm.get('markets', [])]
            outcome_count = sum(len(m.get('outcomes', [])) for m in bm.get('markets', []))
            
            bm_data.append({
                'Bookmaker': bm['key'],
                'Title': bm['title'][:25],
                'Markets': ', '.join(markets_list),
                'Outcomes': outcome_count
            })
        
        df = pd.DataFrame(bm_data)
        print(df.to_string(index=False))
        
        # Show one bookmaker's full structure
        print(f"\n\n📄 DETAILED VIEW - {bookmakers[0]['key']}:")
        print("-" * 80)
        bm = bookmakers[0]
        
        for market in bm.get('markets', []):
            print(f"\n  Market: {market['key']}")
            for outcome in market.get('outcomes', []):
                point = outcome.get('point', '')
                price = outcome.get('price', '')
                pt_str = f"({point})" if point else ""
                print(f"    - {outcome['name']:20} {pt_str:10} @ {price}")
        
        # Save JSON for inspection
        output_file = "query_result.json"
        with open(output_file, 'w') as f:
            json.dump(odds_data, f, indent=2)
        
        print(f"\n\n💾 Full JSON saved: {output_file}")
        print(f"   (Right-click and 'Open in VS Code' to explore)")
        
        # Stats
        print(f"\n\n📈 STATISTICS:")
        print(f"   Total bookmakers: {len(bookmakers)}")
        print(f"   Total markets: {sum(len(bm.get('markets', [])) for bm in bookmakers)}")
        print(f"   Total outcomes: {sum(len(o) for bm in bookmakers for m in bm.get('markets', []) for o in m.get('outcomes', []))}")
    
    else:
        print("❌ No events found for this query")
        print("\nTry different SPORT or REGIONS values")

except requests.exceptions.RequestException as e:
    print(f"❌ API Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
