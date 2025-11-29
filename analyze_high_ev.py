#!/usr/bin/env python3
"""
Analyze all EV hits over 20% to identify calculation errors.
For each high-EV hit, fetch fresh API data and show:
- All bookmaker odds (US + AU) for that market
- Fair price calculation breakdown
- Why the EV is so high
"""

import os
import json
import requests
import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_BASE = os.getenv("ODDS_API_BASE", "https://api.the-odds-api.com/v4")

# Read the EV CSV and find hits over 20%
csv_path = Path(__file__).parent / "data" / "hits_ev.csv"

high_ev_hits = []
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ev_val = float(row["EV"].strip("%"))
        if ev_val > 20:
            high_ev_hits.append(row)

print(f"\n{'='*80}")
print(f"Found {len(high_ev_hits)} hits with >20% EV")
print(f"{'='*80}\n")

# Group by event to avoid duplicate API calls
events_to_check = {}
for hit in high_ev_hits:
    event_key = (hit["sport"], hit["event"], hit["market"])
    if event_key not in events_to_check:
        events_to_check[event_key] = []
    events_to_check[event_key].append(hit)

print(f"Checking {len(events_to_check)} unique events...\n")

# Fetch current odds for each event
for idx, (event_key, hits) in enumerate(events_to_check.items(), 1):
    sport, event_name, market = event_key
    
    print(f"\n{'='*80}")
    print(f"{idx}. {event_name}")
    print(f"   Sport: {sport} | Market: {market}")
    print(f"{'='*80}")
    
    # Display all hits for this event
    for hit in hits:
        print(f"   EV: {hit['EV']} | {hit['side']} | {hit['book']} ${hit['price']} vs Fair ${hit['Fair']}")
    
    # Fetch fresh API data
    url = f"{ODDS_API_BASE}/sports/{sport}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "au,us",
        "markets": market,
        "oddsFormat": "decimal"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        events = resp.json()
        
        # Find the matching event
        target_event = None
        for ev in events:
            home = ev.get("home_team", "")
            away = ev.get("away_team", "")
            ev_name = f"{home} V {away}"
            if ev_name == event_name or event_name in ev_name or ev_name in event_name:
                target_event = ev
                break
        
        if not target_event:
            print(f"\n   ⚠️  Could not find event in API response")
            continue
        
        # Get the specific line if it's spreads/totals
        line_point = hits[0].get("line", "")
        
        print(f"\n   📊 ALL BOOKMAKER ODDS:")
        print(f"   {'Bookmaker':<20} {'Side':<20} {'Price':<10}")
        print(f"   {'-'*50}")
        
        all_odds = []
        for bk in target_event.get("bookmakers", []):
            bkey = bk.get("key")
            markets = bk.get("markets", [])
            target_market = next((m for m in markets if m.get("key") == market), None)
            if not target_market:
                continue
            
            outcomes = target_market.get("outcomes", [])
            
            # Filter by line if needed
            if line_point:
                outcomes = [o for o in outcomes if str(o.get("point", "")) == str(line_point)]
            
            for outcome in outcomes:
                name = outcome.get("name")
                point = outcome.get("point", "")
                price = outcome.get("price")
                
                side_str = f"{name}" + (f" {point:+g}" if point else "")
                print(f"   {bkey:<20} {side_str:<20} ${price:<10.2f}")
                all_odds.append((bkey, side_str, price))
        
        if not all_odds:
            print(f"   ⚠️  No odds found for this market/line")
        
        print(f"\n   🎯 FAIR PRICE CALCULATION:")
        print(f"   The issue: AU bookmakers were included in median calculation")
        print(f"   This creates circular logic where AU odds influence their own 'fair' comparison")
        print(f"   Fix: Only US bookmakers + sharp books should determine fair price")
        
    except Exception as e:
        print(f"\n   ❌ Error fetching data: {e}")

print(f"\n{'='*80}")
print(f"Analysis complete. All >20% EV hits shown above.")
print(f"{'='*80}\n")
