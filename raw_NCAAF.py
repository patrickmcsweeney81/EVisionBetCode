"""
Extract raw NCAAF (College Football) market data from Odds API
Fetches current NCAAF odds, outputs one row per market.
Includes half-point normalization for spreads and totals.
"""

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("ODDS_API_KEY", "")

# Data paths
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = DATA_DIR / "raw_NCAAF.csv"

# API Configuration
ODDS_API_HOST = "https://api.the-odds-api.com"
SPORT_KEY = "americanfootball_ncaaf"
REGIONS = "au,us,eu"
ODDS_FORMAT = "decimal"

# Event time filtering
EVENT_MIN_MINUTES = 5
EVENT_MAX_HOURS = 48


def parse_float(s) -> float:
    """Parse string/float to float, return 0 on error."""
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return float(str(s).strip())
    except (ValueError, AttributeError):
        return 0.0


def normalize_to_half_point(value: float) -> float:
    """Normalize spread/total to nearest half-point increment."""
    if value == 0:
        return 0.0
    # Round to nearest 0.5, always rounding 0.25 up to 0.5 and 0.75 up to 1.0
    import math
    return math.floor(value * 2 + 0.5) / 2


def is_event_in_window(commence_time_str: str) -> bool:
    """Check if event start time is within the window."""
    try:
        event_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = event_time - now
        
        min_seconds = EVENT_MIN_MINUTES * 60
        max_seconds = EVENT_MAX_HOURS * 3600
        
        return min_seconds <= delta.total_seconds() <= max_seconds
    except:
        return True


def fetch_ncaaf_odds() -> List[Dict]:
    """Fetch NCAAF odds from Odds API (base markets only - player props limited for college)."""
    if not API_KEY:
        print("❌ ODDS_API_KEY not set in .env")
        sys.exit(1)

    all_events = {}

    # Fetch base markets (college sports typically have fewer player props)
    base_markets = ["h2h", "spreads", "totals"]
    url = f"{ODDS_API_HOST}/v4/sports/{SPORT_KEY}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": ",".join(base_markets),
        "oddsFormat": ODDS_FORMAT,
    }

    print(f"[API] Fetching NCAAF base markets: {', '.join(base_markets)}")
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        events = resp.json()
        for e in events:
            all_events[e.get("id")] = e
        remaining = resp.headers.get("x-requests-remaining", "?")
        cost = resp.headers.get("x-requests-last", "?")
        print(f"[API] Got {len(events)} events, Cost: {cost}, Remaining: {remaining}")
    except Exception as e:
        print(f"[!] Base markets error: {e}")
        return list(all_events.values())

    return list(all_events.values())


def extract_rows(events: List[Dict]) -> List[Dict]:
    """Parse API events into rows (one per market with normalization)."""
    rows = []
    timestamp = datetime.now(timezone.utc).isoformat()

    for event in events:
        commence_time = event.get("commence_time", "")
        if not is_event_in_window(commence_time):
            continue

        event_id = event.get("id", "")
        away_team = event.get("away_team", "")
        home_team = event.get("home_team", "")
        teams = f"{away_team} V {home_team}" if away_team and home_team else ""

        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            continue

        all_bookie_keys = set()
        for bm in bookmakers:
            all_bookie_keys.add(bm.get("key", ""))

        for bm in bookmakers:
            bookie_key = bm.get("key", "")
            markets = bm.get("markets", [])

            for market_data in markets:
                market_key = market_data.get("key", "")
                outcomes = market_data.get("outcomes", [])

                for outcome in outcomes:
                    selection = outcome.get("name", "")
                    price = parse_float(outcome.get("price", "0"))

                    if price <= 1:
                        continue

                    point = ""
                    if "point" in outcome:
                        raw_point = parse_float(outcome.get("point", "0"))
                        if market_key in ["spreads", "totals"]:
                            normalized_point = normalize_to_half_point(raw_point)
                            point = str(normalized_point)
                        else:
                            point = str(raw_point)

                    row_key = (event_id, market_key, point, selection, "")
                    
                    existing = next((r for r in rows if (r["event_id"], r["market"], r["line"], r["selection"], r.get("player", "")) == row_key), None)
                    if existing:
                        existing[bookie_key] = f"{price:.2f}"
                    else:
                        row = {
                            "timestamp": timestamp,
                            "sport": SPORT_KEY,
                            "event_id": event_id,
                            "commence_time": commence_time,
                            "teams": teams,
                            "market": market_key,
                            "line": point,
                            "selection": selection,
                            "player": "",
                        }
                        for bk in all_bookie_keys:
                            row[bk] = ""
                        row[bookie_key] = f"{price:.2f}"
                        rows.append(row)

    return rows


def main():
    print("[RAW NCAAF] Fetch NCAAF odds from Odds API")
    print("=" * 70)

    events = fetch_ncaaf_odds()
    print(f"[OK] Fetched {len(events)} NCAAF events")

    if not events:
        print("⚠️  No NCAAF events found")
        return

    rows = extract_rows(events)
    print(f"[OK] Extracted {len(rows)} market rows")

    if not rows:
        print("⚠️  No market data found")
        return

    all_bookies = set()
    for row in rows:
        for key in row.keys():
            if key not in ["timestamp", "sport", "event_id", "commence_time", "teams", "market", "line", "selection", "player"]:
                all_bookies.add(key)

    all_bookies = sorted(all_bookies)
    headers = ["timestamp", "sport", "event_id", "commence_time", "teams", "market", "line", "selection", "player"] + all_bookies

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            for bk in all_bookies:
                if bk not in row:
                    row[bk] = ""
            writer.writerow(row)

    print(f"✅ Wrote {len(rows)} NCAAF markets to {OUTPUT_FILE}")
    print(f"   Bookmakers: {len(all_bookies)}")
    print("[DONE]")


if __name__ == "__main__":
    main()
