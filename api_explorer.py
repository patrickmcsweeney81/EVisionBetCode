"""
API EXPLORER - View all available data efficiently
Run this to explore what The Odds API has available
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

class APIExplorer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = API_HOST
    
    def get_sports(self):
        """List all available sports (FREE call, no usage)"""
        url = f"{self.host}/v4/sports"
        params = {"apiKey": self.api_key}
        resp = requests.get(url, params=params, timeout=10)
        return resp.json()
    
    def get_event_sample(self, sport="basketball_nba", regions="au,us,us2,eu"):
        """Get ONE event to inspect structure"""
        url = f"{self.host}/v4/sports/{sport}/events"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
        }
        resp = requests.get(url, params=params, timeout=10)
        return resp.json()
    
    def get_odds_for_event(self, sport, event_id, regions="au,us,us2,eu", markets="h2h,spreads,totals"):
        """Get odds for ONE event"""
        url = f"{self.host}/v4/sports/{sport}/events/{event_id}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal",
        }
        resp = requests.get(url, params=params, timeout=10)
        return resp.json()
    
    def explore_bookmakers_by_region(self, sport="basketball_nba", market="h2h"):
        """See which books are in which regions"""
        results = {}
        
        for region in ["au", "us", "us2", "eu"]:
            url = f"{self.host}/v4/sports/{sport}/events"
            params = {
                "apiKey": self.api_key,
                "regions": region,
            }
            events = requests.get(url, params=params, timeout=10).json()
            
            if events:
                event_id = events[0]["id"]
                odds_url = f"{self.host}/v4/sports/{sport}/events/{event_id}/odds"
                odds_params = {
                    "apiKey": self.api_key,
                    "regions": region,
                    "markets": market,
                    "oddsFormat": "decimal",
                }
                odds = requests.get(odds_url, params=odds_params, timeout=10).json()
                
                books = [bm["key"] for bm in odds.get("bookmakers", [])]
                results[region] = books
        
        return results

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

# Main
try:
    explorer = APIExplorer(API_KEY)
    
    print_section("1. AVAILABLE SPORTS")
    sports = explorer.get_sports()
    for sport in sports[:10]:  # First 10
        print(f"  {sport['key']:30} - {sport['title']}")
    print(f"  ... and {len(sports)-10} more")
    
    print_section("2. SAMPLE NBA EVENT")
    events = explorer.get_event_sample("basketball_nba")
    if events:
        event = events[0]
        print(f"  Game: {event['away_team']} @ {event['home_team']}")
        print(f"  Event ID: {event['id']}")
        print(f"  Start: {event['commence_time']}")
        
        print_section("3. BOOKMAKERS & ODDS FOR THIS EVENT")
        odds = explorer.get_odds_for_event("basketball_nba", event['id'])
        
        print(f"  Total Bookmakers: {len(odds.get('bookmakers', []))}\n")
        
        for bm in odds.get('bookmakers', [])[:5]:  # First 5 books
            print(f"  📌 {bm['key']:20} ({bm['title']})")
            for market in bm.get('markets', [])[:2]:  # First 2 markets
                outcomes = market.get('outcomes', [])
                print(f"     {market['key']:15} -> {len(outcomes)} outcomes")
                for outcome in outcomes[:2]:  # First 2 outcomes
                    pt = outcome.get('point', '')
                    price = outcome.get('price', '')
                    print(f"        {outcome['name']:15} pt:{pt:>6} odds:{price:>6}")
        
        if len(odds.get('bookmakers', [])) > 5:
            print(f"\n  ... and {len(odds.get('bookmakers', []))-5} more bookmakers")
        
        print_section("4. BOOKMAKERS BY REGION")
        regions = explorer.explore_bookmakers_by_region("basketball_nba", "h2h")
        for region, books in sorted(regions.items()):
            print(f"  Region '{region}': {len(books)} books")
            for book in sorted(books)[:5]:
                print(f"    - {book}")
            if len(books) > 5:
                print(f"    ... and {len(books)-5} more")
    
    print_section("5. USAGE TIPS")
    print("""
  ✅ EFFICIENT QUERIES:
     - Use one region per call if you only need one region
     - Specify only markets you need: h2h, spreads, totals
     - Get one event sample to understand structure
     - Cache event data (games don't change often)
  
  ❌ AVOID (wastes credits):
     - Getting all events + all odds (use filters)
     - Calling same event/region twice
     - Requesting unwanted markets/regions
  
  💡 API CREDIT TIPS:
     - 1 call per event = 1 credit (usually)
     - Request only what you display
     - Batch same-region requests
  
  📊 RECOMMENDED FLOW:
     1. Get events list (1 call)
     2. For each event, get odds (1 call each)
     3. Cache/store results
     4. Run every 30-60 minutes max
    """)

except Exception as e:
    print(f"❌ Error: {e}")
