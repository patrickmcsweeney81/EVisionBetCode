"""
ODDS API MARKET DIAGNOSTIC
Check what markets and alternative lines are available from The Odds API
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

def check_api_markets():
    """Check what markets are available in The Odds API"""
    
    print(f"\n{'='*80}")
    print(f"ODDS API - AVAILABLE MARKETS")
    print(f"{'='*80}\n")
    
    # Fetch one event to inspect structure
    url = f"{API_HOST}/v4/sports/basketball_nba/events"
    params = {
        "apiKey": API_KEY,
        "regions": "au,us,us2,eu",
    }
    
    print(f"Fetching events...")
    resp = requests.get(url, params=params, timeout=10)
    events = resp.json()
    
    if not events:
        print("❌ No events found")
        return
    
    # Get first event for inspection
    first_event = events[0]
    event_id = first_event['id']
    event_name = f"{first_event['away_team']} @ {first_event['home_team']}"
    
    print(f"Inspecting event: {event_name}")
    print(f"Event ID: {event_id}\n")
    
    # Fetch odds for this event
    url = f"{API_HOST}/v4/sports/basketball_nba/events/{event_id}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "au,us,us2,eu",
        "oddsFormat": "decimal",
        "markets": "h2h,spreads,totals",  # Request all markets
    }
    
    print(f"Fetching odds with markets: {params['markets']}")
    resp = requests.get(url, params=params, timeout=10)
    odds_data = resp.json()
    
    if not odds_data or 'bookmakers' not in odds_data:
        print("❌ No odds data found")
        return
    
    bookmakers = odds_data['bookmakers']
    print(f"Found {len(bookmakers)} bookmakers\n")
    
    print(f"{'='*80}")
    print(f"MARKET STRUCTURE ANALYSIS")
    print(f"{'='*80}\n")
    
    # Analyze markets
    all_markets = {}
    
    for bm in bookmakers:
        book_name = bm['key']
        
        for market in bm.get('markets', []):
            market_type = market['key']
            
            if market_type not in all_markets:
                all_markets[market_type] = {
                    'points': set(),
                    'selections': set(),
                    'outcomes': []
                }
            
            for outcome in market.get('outcomes', []):
                selection = outcome.get('name', '')
                point = outcome.get('point')
                price = outcome.get('price')
                
                all_markets[market_type]['selections'].add(selection)
                if point is not None:
                    all_markets[market_type]['points'].add(float(point))
                
                all_markets[market_type]['outcomes'].append({
                    'book': book_name,
                    'selection': selection,
                    'point': point,
                    'price': price
                })
    
    # Print analysis
    for market_type, data in sorted(all_markets.items()):
        print(f"\nMARKET TYPE: {market_type.upper()}")
        print(f"  Unique point values: {len(data['points'])}")
        if data['points']:
            points_sorted = sorted(data['points'])
            print(f"    Points: {points_sorted}")
        
        print(f"  Unique selections: {len(data['selections'])}")
        if data['selections']:
            for sel in sorted(data['selections']):
                print(f"    - {sel}")
        
        print(f"  Total outcomes: {len(data['outcomes'])}")
        
        # Show point distribution
        point_dist = {}
        for outcome in data['outcomes']:
            point = outcome['point']
            if point not in point_dist:
                point_dist[point] = 0
            point_dist[point] += 1
        
        print(f"\n  Point distribution:")
        for point in sorted([p for p in point_dist.keys() if p is not None]):
            print(f"    {point:6.1f}: {point_dist[point]:2} books")
    
    print(f"\n{'='*80}")
    print(f"BOOKMAKER SPREAD VARIATIONS")
    print(f"{'='*80}\n")
    
    # Show how many different points each book offers per market
    if 'spreads' in all_markets:
        spreads_outcomes = all_markets['spreads']['outcomes']
        
        # Group by book
        book_spreads = {}
        for outcome in spreads_outcomes:
            book = outcome['book']
            if book not in book_spreads:
                book_spreads[book] = {'points': set(), 'selections': {}}
            
            selection = outcome['selection']
            point = outcome['point']
            
            book_spreads[book]['points'].add(point)
            if selection not in book_spreads[book]['selections']:
                book_spreads[book]['selections'][selection] = []
            book_spreads[book]['selections'][selection].append(point)
        
        print("Top 15 bookmakers - spread point variations:\n")
        for book in sorted(book_spreads.keys())[:15]:
            data = book_spreads[book]
            points_list = sorted([p for p in data['points'] if p is not None])
            print(f"  {book:20} {len(points_list)} point values: {points_list}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    check_api_markets()
