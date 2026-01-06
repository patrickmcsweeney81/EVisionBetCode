"""
Research All Available Markets for Neds
========================================
Investigate what markets Neds actually offers on The Odds API.

This script:
1. Fetches all NBA events
2. For each event, gets Neds odds with ALL markets
3. Reports which markets Neds actually has data for
4. Shows market distribution

Usage:
    python research_neds_markets.py

Output:
    Shows market availability + sample odds
"""

import os
import requests
import pandas as pd
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

if not ODDS_API_KEY:
    print("❌ ODDS_API_KEY not set in .env")
    exit(1)

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"

def research_neds_markets():
    """Research all available markets for Neds."""
    
    print("🔬 NEDS MARKET RESEARCH\n")
    print("=" * 70)
    
    # Step 1: Get events
    print("\n📋 Step 1: Fetching NBA events...")
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
    
    # Step 2: For each event, fetch ALL markets for Neds
    print("📊 Step 2: Researching Neds markets...")
    print("=" * 70 + "\n")
    
    all_markets = defaultdict(list)  # market_key -> list of outcomes
    market_counts = defaultdict(int)  # market_key -> count
    
    for idx, event in enumerate(events, 1):
        event_id = event.get('id')
        home = event.get('home_team', '')
        away = event.get('away_team', '')
        event_name = f"{away} @ {home}"
        
        # Fetch odds for this event with NO market filter (get everything)
        odds_url = f"{BASE_URL}/sports/{SPORT}/events/{event_id}/odds"
        odds_params = {
            'apiKey': ODDS_API_KEY,
            'bookmakers': 'neds',
            # Don't specify markets - get all
            'oddsFormat': 'decimal'
        }
        
        try:
            resp = requests.get(odds_url, params=odds_params, timeout=20)
            resp.raise_for_status()
            odds_data = resp.json()
        except Exception as e:
            print(f"⚠️  Error for {event_name}: {e}")
            continue
        
        # Extract Neds data
        bookmakers = odds_data.get('bookmakers', [])
        neds_book = None
        
        for bm in bookmakers:
            if bm.get('key') == 'neds':
                neds_book = bm
                break
        
        if not neds_book:
            print(f"  {idx}/{len(events)} {event_name:<50} ⚠️  No Neds data")
            continue
        
        # Analyze markets
        markets = neds_book.get('markets', [])
        event_markets = []
        
        for market in markets:
            market_key = market.get('key')
            outcomes = market.get('outcomes', [])
            
            if market_key not in market_counts:
                market_counts[market_key] = 0
            
            market_counts[market_key] += 1
            
            # Store sample outcomes
            for outcome in outcomes:
                all_markets[market_key].append({
                    'event': event_name,
                    'outcome': outcome.get('name', ''),
                    'odds': outcome.get('price', ''),
                    'point': outcome.get('point', '')
                })
            
            event_markets.append(f"{market_key}({len(outcomes)})")
        
        print(f"  {idx}/{len(events)} {event_name:<50} ✅ {len(markets)} markets")
        if event_markets:
            print(f"           → {', '.join(event_markets)}\n")
    
    # Step 3: Summarize findings
    print("\n" + "=" * 70)
    print("📊 MARKET SUMMARY\n")
    
    print(f"Total unique markets found: {len(market_counts)}\n")
    
    print("Markets offered by Neds (by frequency across events):\n")
    for market, count in sorted(market_counts.items(), key=lambda x: x[1], reverse=True):
        pct = int(100 * count / len(events))
        print(f"  {market:<30} : {count:>2} events ({pct}%)")
    
    # Step 4: Show sample data for each market
    print("\n" + "=" * 70)
    print("📋 SAMPLE DATA BY MARKET\n")
    
    for market_key in sorted(market_counts.keys()):
        samples = all_markets[market_key][:3]  # First 3 outcomes
        print(f"\n{market_key.upper()}:")
        for sample in samples:
            point_str = f"({sample['point']})" if sample['point'] else ""
            print(f"  {sample['event']:<40} {sample['outcome']:<25} {sample['odds']:>6} {point_str}")
    
    # Step 5: Export comprehensive CSV
    print("\n" + "=" * 70)
    print("\n📁 Exporting comprehensive Neds data...\n")
    
    all_rows = []
    for market_key, outcomes in all_markets.items():
        for outcome in outcomes:
            all_rows.append({
                'market': market_key,
                'event': outcome['event'],
                'outcome': outcome['outcome'],
                'odds_decimal': outcome['odds'],
                'point': outcome['point']
            })
    
    df = pd.DataFrame(all_rows)
    
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/neds_all_markets_{timestamp}.csv"
    df.to_csv(output_csv, index=False)
    
    print(f"✅ Full data saved: {output_csv}")
    print(f"   Rows: {len(df):,}")
    print(f"   Markets: {df['market'].nunique()}")
    
    return output_csv

if __name__ == "__main__":
    research_neds_markets()
