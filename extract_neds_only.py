"""
Extract NBA Odds for Single Bookmaker (Neds) - Optimized
========================================================
Fetch all NBA markets from The Odds API focused on Neds odds only.

The correct approach:
1. Get list of events from /events endpoint
2. For each event, fetch odds from /odds endpoint with Neds filter
3. Extract all markets (h2h, spreads, totals, player props, etc.)

Usage:
    python extract_neds_only.py

Output:
    data/neds_only_YYYYMMDD_HHMMSS.csv  
"""

import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

if not ODDS_API_KEY:
    print("❌ ODDS_API_KEY not set in .env")
    exit(1)

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"

def fetch_neds_odds():
    """Fetch NBA odds with Neds focus."""
    
    print(f"🏀 NBA Neds Odds Extractor\n")
    
    # Step 1: Get events
    print("📋 Step 1: Fetching NBA events...")
    events_url = f"{BASE_URL}/sports/{SPORT}/events"
    events_params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'au,us,us2,eu'
    }
    
    try:
        resp = requests.get(events_url, params=events_params, timeout=20)
        resp.raise_for_status()
        events = resp.json()
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return
    
    if not events:
        print("❌ No events returned")
        return
    
    print(f"✅ Found {len(events)} events\n")
    
    # Step 2: For each event, fetch odds with Neds filter
    print("📊 Step 2: Fetching Neds odds for each event...\n")
    
    all_rows = []
    
    for idx, event in enumerate(events, 1):
        event_id = event.get('id')
        home = event.get('home_team', '')
        away = event.get('away_team', '')
        commence = event.get('commence_time', '')
        event_name = f"{away} @ {home}"
        
        # Fetch odds for this event with Neds filter
        odds_url = f"{BASE_URL}/sports/{SPORT}/events/{event_id}/odds"
        odds_params = {
            'apiKey': ODDS_API_KEY,
            'bookmakers': 'neds',  # Filter to just Neds
            'markets': 'h2h,spreads,totals,alternate_spreads,alternate_totals,player_points,player_assists,player_rebounds',
            'oddsFormat': 'decimal'
        }
        
        try:
            resp = requests.get(odds_url, params=odds_params, timeout=20)
            resp.raise_for_status()
            odds_data = resp.json()
        except Exception as e:
            print(f"⚠️  Error fetching odds for {event_name}: {e}")
            continue
        
        # Extract Neds odds
        bookmakers = odds_data.get('bookmakers', [])
        neds_book = None
        
        for bm in bookmakers:
            if bm.get('key') == 'neds':
                neds_book = bm
                break
        
        if not neds_book:
            print(f"  {idx}/{len(events)} {event_name:<50} ⚠️  No Neds odds")
            continue
        
        # Parse all markets for Neds
        markets = neds_book.get('markets', [])
        neds_count = 0
        
        for market in markets:
            market_key = market.get('key')
            outcomes = market.get('outcomes', [])
            
            for outcome in outcomes:
                row = {
                    'event_id': event_id,
                    'event_name': event_name,
                    'commence_time': commence,
                    'market': market_key,
                    'outcome': outcome.get('name', ''),
                    'odds_decimal': outcome.get('price', ''),
                    'point': outcome.get('point', '')
                }
                all_rows.append(row)
                neds_count += 1
        
        print(f"  {idx}/{len(events)} {event_name:<50} ✅ {neds_count} outcomes")
    
    if not all_rows:
        print("\n❌ No Neds odds found across all events")
        return
    
    print(f"\n✅ Extracted {len(all_rows):,} Neds odds\n")
    
    # Create DataFrame
    df = pd.DataFrame(all_rows)
    
    # Summary
    print("📊 SUMMARY:")
    print(f"  Total outcomes: {len(df):,}")
    print(f"  Events with Neds: {df['event_name'].nunique()}")
    print(f"  Markets: {', '.join(df['market'].unique())}\n")
    
    # Save CSV
    os.makedirs("data", exist_ok=True)
    output_csv = "data/neds_only.csv"
    df.to_csv(output_csv, index=False)
    
    print(f"✅ Saved to: {output_csv}\n")
    
    # Display sample
    print("📋 Sample (first 10 outcomes):\n")
    sample_cols = ['event_name', 'market', 'outcome', 'odds_decimal', 'point']
    print(df[sample_cols].head(10).to_string(index=False))
    
    return output_csv

if __name__ == "__main__":
    fetch_neds_odds()
