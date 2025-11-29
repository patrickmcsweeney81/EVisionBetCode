"""
Minimal test to debug spread key duplication issue.
Tests actual API data to see what Pinnacle provides.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
# Try different region combinations
REGIONS_TO_TRY = ["us", "us,au", "eu", "uk", "au"]
MARKETS = "spreads"
SPORT = "basketball_nba"

# Try each region to find Pinnacle
pinnacle_found_in_region = None
events = None

for region in REGIONS_TO_TRY:
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": region,
        "markets": MARKETS,
        "oddsFormat": "decimal",
    }
    
    print(f"\nTrying region: {region}...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    events = response.json()
    
    # Check if Pinnacle is in any event
    has_pinnacle = False
    for event in events:
        for bk in event.get("bookmakers", []):
            if bk['key'] == 'pinnacle':
                has_pinnacle = True
                pinnacle_found_in_region = region
                break
        if has_pinnacle:
            break
    
    if has_pinnacle:
        print(f"[OK] PINNACLE FOUND in region: {region}")
        break
    else:
        print(f"[NO] No Pinnacle in region: {region}")

if not pinnacle_found_in_region:
    print(f"\n{'='*80}")
    print("PINNACLE NOT AVAILABLE FOR NBA SPREADS IN ANY REGION")
    print(f"{'='*80}")
    print("This explains why spreads have zero fair prices.")
    print("Pinnacle data is required for fair price calculation.")
    exit()

print(f"\nUsing region: {pinnacle_found_in_region}")
print(f"Found {len(events)} events")

# Analyze first event
if events:
    event = events[0]
    print(f"\n{'='*80}")
    print(f"Event: {event['home_team']} vs {event['away_team']}")
    print(f"{'='*80}")
    
    bookmakers = event.get("bookmakers", [])
    print(f"\nTotal bookmakers: {len(bookmakers)}")
    
    # Find Pinnacle
    pinnacle = None
    for bk in bookmakers:
        if bk['key'] == 'pinnacle':
            pinnacle = bk
            break
    
    if pinnacle:
        print(f"\n✓ PINNACLE FOUND")
        spreads_market = None
        for market in pinnacle.get('markets', []):
            if market['key'] == 'spreads':
                spreads_market = market
                break
        
        if spreads_market:
            print(f"✓ Pinnacle has spreads market")
            outcomes = spreads_market.get('outcomes', [])
            print(f"✓ Pinnacle spreads has {len(outcomes)} outcomes:\n")
            
            for outcome in outcomes:
                name = outcome['name']
                point = outcome['point']
                price = outcome['price']
                print(f"   {name:30} point={point:6.1f}  price={price:.2f}")
                
            # Test key creation logic
            print(f"\n{'='*80}")
            print("KEY CREATION TEST")
            print(f"{'='*80}")
            
            home = event['home_team']
            away = event['away_team']
            
            print(f"\nHome: {home}")
            print(f"Away: {away}\n")
            
            # Show what keys would be created with absolute value approach
            print("Current approach (abs value for target line):")
            for outcome in outcomes:
                name = outcome['name']
                point = abs(outcome['point'])  # This is the problem!
                key = f"{name}_{point}"
                print(f"   {key}")
            
            print("\nProposed fix (canonicalize based on home/away):")
            for outcome in outcomes:
                name = outcome['name']
                point = outcome['point']
                
                # Canonicalize: home gets negative, away gets positive
                abs_pt = abs(point)
                if name == home:
                    canonical_key = f"{name}_{-abs_pt}"
                else:
                    canonical_key = f"{name}_{abs_pt}"
                
                print(f"   Raw: {name}_{point} → Canonical: {canonical_key}")
        else:
            print("✗ Pinnacle has NO spreads market")
    else:
        print("✗ PINNACLE NOT FOUND")
    
    # Check other bookmakers
    print(f"\n{'='*80}")
    print("OTHER BOOKMAKERS WITH SPREADS")
    print(f"{'='*80}\n")
    
    for bk in bookmakers:
        bk_key = bk['key']
        if bk_key == 'pinnacle':
            continue
            
        spreads_market = None
        for market in bk.get('markets', []):
            if market['key'] == 'spreads':
                spreads_market = market
                break
        
        if spreads_market:
            outcomes = spreads_market.get('outcomes', [])
            print(f"{bk_key:20} {len(outcomes)} outcomes:")
            for outcome in outcomes:
                print(f"   {outcome['name']:30} point={outcome['point']:6.1f}")

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)
print("""
If Pinnacle shows 2 outcomes with opposite-signed points (e.g., Team A: -6.0, Team B: +6.0),
but other bookmakers show different combinations (e.g., both positive or both negative),
then the key creation logic needs canonicalization to handle these sign variations.

The fix: Always assign consistent signs based on home/away team, regardless of what
each bookmaker reports.
""")
