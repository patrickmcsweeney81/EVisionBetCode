"""
RAW ODDS EXTRACTOR - Pure Data Only
Fetches odds from Odds API v4 with decimal format.
ONE ROW = ONE BOOKMAKER/MARKET/SELECTION combination.
Zero calculations - just raw facts.

Configuration:
- Sports: NBA, NFL
- Markets: h2h, spreads, totals (via /odds endpoint) + player props (per-event)
- Regions: AU, US (optimized for cost)
- Format: Decimal odds (oddsFormat=decimal)
- Time filter: Events starting >5min from now, <48hrs from now
- Filters: 2-way markets only (Over/Under), DK+FD coverage required
"""
import os
import sys
import csv
import json
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment - look for .env in parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("ODDS_API_KEY", "")
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_CSV = DATA_DIR / "raw_odds_pure.csv"

# API Configuration
ODDS_API_HOST = "https://api.the-odds-api.com"
SPORTS = ["basketball_nba", "americanfootball_nfl", "icehockey_nhl"]  # Can add more
# Include EU to ensure Pinnacle is returned by The Odds API
# Cost note: adding EU increases credits vs au,us only
REGIONS = os.getenv("REGIONS", "au,us,eu")
ODDS_FORMAT = "decimal"  # Always decimal for calculations

# Time filtering for events
EVENT_MIN_MINUTES = 5   # Don't fetch events starting <5 min from now
EVENT_MAX_HOURS = 48    # Don't fetch events starting >48 hrs from now

# Most common player props for each sport
NBA_PROPS = [
    "player_points",           # Points scored
    "player_rebounds",         # Rebounds
    "player_assists",          # Assists
    "player_threes",           # 3-pointers made
    "player_blocks",           # Blocks
    "player_steals",           # Steals
    "player_turnovers",        # Turnovers
    "player_blocks_steals",    # Blocks + Steals combined
    "player_points_rebounds_assists",  # PRA (triple combo)
    "player_points_assists",   # PA combo
    "player_points_rebounds",  # PR combo
    "player_rebounds_assists", # RA combo
]

NFL_PROPS = [
    # Passing (QB)
    "player_pass_yds",         # Passing yards
    "player_pass_tds",         # Passing TDs
    "player_pass_completions", # Completions
    "player_pass_attempts",    # Pass attempts
    "player_pass_interceptions", # Interceptions
    # Rushing (RB/QB)
    "player_rush_yds",         # Rushing yards
    "player_rush_attempts",    # Rush attempts
    # Receiving (WR/TE/RB)
    "player_receptions",       # Receptions
    "player_reception_yds",    # Reception yards
    # Combo stats
    "player_pass_rush_yds",    # Pass + Rush yards
    "player_rush_reception_yds", # Rush + Reception yards
    # Touchdown markets
    "player_anytime_td",       # Anytime TD scored
    "player_1st_td",           # First TD scorer
    # Defense
    "player_tackles_assists",  # Tackles + Assists
    "player_sacks",            # Sacks
    "player_defensive_interceptions", # DEF interceptions
    # Kicking
    "player_kicking_points",   # FG/XP points
]

NCAAF_PROPS = [
    # Passing (QB)
    "player_pass_yds",         # Passing yards
    "player_pass_tds",         # Passing TDs
    "player_pass_completions", # Completions
    # Rushing (RB/QB)
    "player_rush_yds",         # Rushing yards
    "player_rush_attempts",    # Rush attempts
    # Receiving (WR/TE/RB)
    "player_receptions",       # Receptions
    "player_reception_yds",    # Reception yards
    # Combo stats
    "player_pass_rush_yds",    # Pass + Rush yards
    # Touchdown markets
    "player_anytime_td",       # Anytime TD scored
    "player_1st_td",           # First TD scorer
]

NHL_PROPS = [
    # Scoring
    "player_goals",            # Goals scored
    "player_assists",          # Assists
    "player_points",           # Points (goals + assists)
    # Shooting
    "player_shots_on_goal",    # Shots on goal
    # Plus/Minus
    "player_plus_minus",       # Plus/Minus rating
    # Penalty
    "player_penalties",        # Penalty minutes
    # Combo
    "player_goals_assists",    # Goals + Assists combo
]

# Base columns (same for all rows)
BASE_HEADERS = [
    "timestamp",
    "sport",
    "event_id",
    "away_team",
    "home_team",
    "commence_time",
    "market",
    "point",
    "selection",
]

# Bookmaker column order: Sharp books first, then AU, then others
BOOKMAKER_ORDER = [
    # Sharp books (fair price sources)
    "Pinnacle",
    "Betfair_EU",
    "Betfair_AU",
    "Draftkings",
    "Fanduel",
    "Betmgm",
    "Betonline",
    "Bovada",
    "Marathonbet",
    "Matchbook",
    "Lowvig",
    "Mybookie",
    "Betus",
    # AU books (primary target)
    "Sportsbet",
    "Bet365",
    "Pointsbet",
    "Betright",
    "Tab",
    "Dabble",
    "Unibet",
    "Ladbrokes",
    "Playup",
    "Tabtouch",
    "Betr",
    "Neds",
    "Boombet",
    # US books
    "Caesars",
    "Betrivers",
    "Sugarhouse",
    "Superbook",
    "Twinspires",
    "Wynnbet",
    "Williamhill",
]

CSV_HEADERS = BASE_HEADERS + BOOKMAKER_ORDER

# Mapping bookmaker keys to CSV column names
BOOKMAKER_TO_COLUMN = {
    "pinnacle": "Pinnacle",
    "betfair_ex_eu": "Betfair_EU",
    "betfair_ex_au": "Betfair_AU",
    "betfair": "Betfair_EU",
    "draftkings": "Draftkings",
    "fanduel": "Fanduel",
    "betmgm": "Betmgm",
    "betonlineag": "Betonline",
    "bovada": "Bovada",
    "betus": "Betus",
    "lowvig": "Lowvig",
    "mybookieag": "Mybookie",
    "marathonbet": "Marathonbet",
    "matchbook": "Matchbook",
    "sportsbet": "Sportsbet",
    "bet365_au": "Bet365",
    "bet365": "Bet365",
    "pointsbetau": "Pointsbet",
    "pointsbetus": "Pointsbet",
    "betright": "Betright",
    "tab": "Tab",
    "dabble_au": "Dabble",
    "unibet": "Unibet",
    "ladbrokes_au": "Ladbrokes",
    "playup": "Playup",
    "tabtouch": "Tabtouch",
    "betr_au": "Betr",
    "neds": "Neds",
    "boombet": "Boombet",
    "caesars": "Caesars",
    "betrivers": "Betrivers",
    "sugarhouse": "Sugarhouse",
    "superbook": "Superbook",
    "twinspires": "Twinspires",
    "wynnbet": "Wynnbet",
    "williamhill_us": "Williamhill",
}


def is_event_in_time_window(commence_time: str) -> bool:
    """Check if event starts within [5 min, 48 hrs] from now."""
    try:
        event_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        min_time = now + timedelta(minutes=EVENT_MIN_MINUTES)
        max_time = now + timedelta(hours=EVENT_MAX_HOURS)
        
        return min_time <= event_time <= max_time
    except Exception as e:
        print(f"[!] Error parsing time {commence_time}: {e}")
        return False


def is_two_way_market(market_data: Dict) -> bool:
    """Check if market is properly structured with Over/Under pairs.
    Player prop markets have multiple players, each with Over/Under.
    We verify outcomes come in pairs (even count) and have Over/Under structure.
    Filters out Yes/No markets and 3-way markets.
    Note: h2h_lay (Betfair exchange) is kept in data but will be filtered at EV stage
    when we can't find adequate sharp coverage for fair odds calculation.
    """
    outcomes = market_data.get('outcomes', [])
    market_key = market_data.get('key', '')
    
    # Must have even number of outcomes (pairs)
    if len(outcomes) % 2 != 0:
        return False
    
    # Core markets (h2h, h2h_lay, spreads, totals) should have 2-3 outcomes max
    if market_key in ['h2h', 'h2h_lay', 'spreads', 'totals']:
        return len(outcomes) in [2, 3]  # Allow 2-way or 3-way for core
    
    # Player props: check if we have Over/Under pattern
    # Exclude Yes/No markets (1-way bets like double_double, first_basket)
    outcome_names = [o.get('name', '').lower() for o in outcomes]
    has_yes = any('yes' in name for name in outcome_names)
    has_no = any('no' in name for name in outcome_names)
    
    # Filter out Yes/No markets completely
    if has_yes or has_no:
        return False
    
    has_over = any('over' in name for name in outcome_names)
    has_under = any('under' in name for name in outcome_names)
    
    # If it has Over/Under structure, it's valid
    if has_over and has_under:
        return True
    
    # Reject anything else
    return False


def has_dk_and_fd_odds(bookmakers: List[Dict]) -> bool:
    """Check if this event/market has odds from BOTH Draftkings AND Fanduel.
    Filters to only markets with sharp book coverage to save API credits.
    """
    bookie_keys = {b.get('key', '').lower() for b in bookmakers}
    
    has_dk = 'draftkings' in bookie_keys
    has_fd = 'fanduel' in bookie_keys
    
    return has_dk and has_fd


def get_props_for_sport(sport_key: str) -> List[str]:
    """Return player prop markets for this sport."""
    if "nba" in sport_key.lower():
        return NBA_PROPS
    elif "nfl" in sport_key.lower():
        return NFL_PROPS
    elif "nhl" in sport_key.lower():
        return []  # NHL props not supported by Odds API (422 errors)
    return []


def fetch_raw_odds(sport_key: str, markets: List[str]) -> List[Dict]:
    """
    Fetch raw odds from API with decimal format.
    Returns list of raw event data (one per event, not expanded).
    """
    stable_markets = ["h2h", "spreads", "totals"]
    markets_to_fetch = [m for m in stable_markets if m in markets]
    
    if not markets_to_fetch:
        print(f"[!] No stable markets available")
        return []
    
    print(f"[API] Fetching {len(markets_to_fetch)} stable markets: {markets_to_fetch}")
    
    all_events = {}
    
    try:
        markets_str = ",".join(markets_to_fetch)
        
        url = f"{ODDS_API_HOST}/v4/sports/{sport_key}/odds"
        params = {
            "apiKey": API_KEY,
            "regions": REGIONS,
            "markets": markets_str,
            "oddsFormat": ODDS_FORMAT,
        }
        
        print(f"[API] Requesting: {markets_str}")
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        
        events = resp.json()
        
        for event in events:
            all_events[event.get("id")] = event
        
        remaining = resp.headers.get("x-requests-remaining", "?")
        cost = resp.headers.get("x-requests-last", "?")
        print(f"[API] Got {len(events)} events, Cost: {cost}, Remaining: {remaining}")
        
        return list(all_events.values())
        
    except Exception as e:
        print(f"[!] Error fetching odds: {e}")
        return list(all_events.values())


def fetch_player_props(sport_key: str, events: List[Dict]) -> List[Dict]:
    """
    Fetch player props for events within time window.
    Uses per-event /events/{eventId}/odds endpoint.
    Filters to only events with DK+FD coverage for cost optimization.
    """
    props_markets = get_props_for_sport(sport_key)
    if not props_markets:
        print(f"[!] No props defined for {sport_key}")
        return []
    
    events_in_window = [e for e in events if is_event_in_time_window(e.get("commence_time", ""))]
    
    if not events_in_window:
        print(f"[API] No events in time window for {sport_key}")
        return []
    
    print(f"[API] Found {len(events_in_window)} events in time window for props")
    
    markets_str = ",".join(props_markets)
    
    try:
        for event_idx, event in enumerate(events_in_window, 1):
            event_id = event.get("id", "")
            
            url = f"{ODDS_API_HOST}/v4/sports/{sport_key}/events/{event_id}/odds"
            params = {
                "apiKey": API_KEY,
                "regions": REGIONS,
                "markets": markets_str,
                "oddsFormat": ODDS_FORMAT,
            }
            
            try:
                resp = requests.get(url, params=params, timeout=60)
                resp.raise_for_status()
                
                prop_event = resp.json()
                orig_bookmakers = event.get("bookmakers", [])
                prop_bookmakers = prop_event.get("bookmakers", [])
                
                # Merge prop bookmakers (filter rows with DK+FD will happen later)
                for prop_bm in prop_bookmakers:
                    orig_bm = next((b for b in orig_bookmakers if b.get("key") == prop_bm.get("key")), None)
                    if orig_bm:
                        orig_markets = orig_bm.get("markets", [])
                        for m in prop_bm.get("markets", []):
                            if m.get("key") not in [om.get("key") for om in orig_markets] and is_two_way_market(m):
                                orig_bm["markets"].append(m)
                    else:
                        filtered_markets = [m for m in prop_bm.get("markets", []) if is_two_way_market(m)]
                        if filtered_markets:
                            prop_bm["markets"] = filtered_markets
                            orig_bookmakers.append(prop_bm)
                
                event["bookmakers"] = orig_bookmakers
                
                remaining = resp.headers.get("x-requests-remaining", "?")
                cost = resp.headers.get("x-requests-last", "?")
                print(f"      Event {event_idx}/{len(events_in_window)}: Cost {cost}, Remaining: {remaining}")
                
            except Exception as e:
                print(f"      [!] Error fetching props for event {event_id}: {e}")
                continue
        
        return events_in_window
        
    except Exception as e:
        print(f"[!] Error in prop fetching: {e}")
        return events_in_window


def expand_to_rows(events: List[Dict], timestamp: str) -> List[Dict]:
    """Expand raw API events into one row per market/selection."""
    rows = []
    
    for event in events:
        event_id = event.get("id", "")
        sport_key = event.get("sport_key", "")
        away_team = event.get("away_team", "")
        home_team = event.get("home_team", "")
        commence_time = event.get("commence_time", "")
        
        bookmakers = event.get("bookmakers", [])
        market_data = {}
        
        for bookie in bookmakers:
            bookie_key = bookie.get("key", "").lower()
            col_name = BOOKMAKER_TO_COLUMN.get(bookie_key, bookie_key.title())
            
            markets = bookie.get("markets", [])
            
            for market in markets:
                market_key = market.get("key", "")
                outcomes = market.get("outcomes", [])
                
                for outcome in outcomes:
                    outcome_name = outcome.get("name", "")
                    odds_decimal = outcome.get("price", 0)
                    point = outcome.get("point")
                    description = outcome.get("description", "")
                    
                    if odds_decimal <= 1:
                        continue
                    
                    # Build selection string
                    if description:  # Player prop
                        selection = f"{description} {outcome_name}"
                    elif point is not None:  # Spread/Total
                        if outcome_name in ["Over", "Under"]:
                            selection = f"{outcome_name} {point:+.1f}"
                        else:
                            selection = outcome_name
                    else:  # H2H
                        selection = outcome_name
                    
                    key = (market_key, point if point is not None else "", selection)
                    
                    if key not in market_data:
                        market_data[key] = {
                            "market": market_key,
                            "point": point if point is not None else "",
                            "selection": selection,
                            "timestamp": timestamp,
                            "sport": sport_key,
                            "event_id": event_id,
                            "away_team": away_team,
                            "home_team": home_team,
                            "commence_time": commence_time,
                        }
                    
                    market_data[key][col_name] = f"{odds_decimal:.3f}"
        
        for row in market_data.values():
            rows.append(row)
    
    return rows



def filter_rows_by_dk_fd(rows: List[Dict], verbose: bool = False) -> List[Dict]:
    """
    DISABLED: Filter removed - keep all rows for manual filtering.
    User will filter DK+FD themselves in downstream analysis.
    """
    if verbose:
        print(f"[FILTER] DK+FD row filter DISABLED - returning all {len(rows)} rows")
    return rows


def append_to_csv(rows: List[Dict]):
    """Append rows to CSV file."""
    if not rows:
        print("[!] No rows to write")
        return
    
    # Always include Pinnacle column even if not returned (user request)
    bookie_cols_in_data = {"Pinnacle"}
    for row in rows:
        for key in row.keys():
            if key not in BASE_HEADERS:
                bookie_cols_in_data.add(key)
    
    ordered_bookies = []
    for bookie in BOOKMAKER_ORDER:
        if bookie in bookie_cols_in_data:
            ordered_bookies.append(bookie)
    
    unknown_bookies = sorted(bookie_cols_in_data - set(BOOKMAKER_ORDER))
    ordered_bookies.extend(unknown_bookies)
    
    final_headers = BASE_HEADERS + ordered_bookies
    file_exists = RAW_CSV.exists()
    
    try:
        with open(RAW_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=final_headers)
            
            if not file_exists:
                writer.writeheader()
                print(f"[CSV] Created {RAW_CSV}")
                print(f"[CSV] Headers ({len(final_headers)}): {', '.join(final_headers[:20])}...")
            
            writer.writerows(rows)
            print(f"[CSV] Appended {len(rows)} rows")
            
    except PermissionError as e:
        fallback = DATA_DIR / f"raw_odds_pure_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"
        try:
            with open(fallback, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=final_headers)
                writer.writeheader()
                writer.writerows(rows)
            print(f"[CSV] Primary file locked; wrote to {fallback}")
        except Exception as inner:
            print(f"[!] Error writing fallback CSV: {inner}")
    except Exception as e:
        print(f"[!] Error writing CSV: {e}")


def main():
    """Main extraction flow."""
    if not API_KEY:
        print("[!] ODDS_API_KEY not set in .env")
        sys.exit(1)
    
    DATA_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    all_rows = []
    
    for sport_key in SPORTS:
        print(f"\n=== {sport_key.upper()} ===")
        
        core_markets = ['h2h', 'spreads', 'totals']
        print(f"[API] Fetching core markets: {core_markets}")
        
        events = fetch_raw_odds(sport_key, core_markets)
        if not events:
            print(f"[!] No events for {sport_key}")
            continue
        
        print(f"[OK] Got {len(events)} core market events")
        
        print(f"[*] Fetching player props...")
        events_with_props = fetch_player_props(sport_key, events)
        
        rows = expand_to_rows(events_with_props, timestamp)
        print(f"[OK] Expanded to {len(rows)} rows")
        
        # Filter to only rows with DK+FD coverage
        rows_filtered = filter_rows_by_dk_fd(rows, verbose=True)
        removed = len(rows) - len(rows_filtered)
        print(f"[OK] Filtered to {len(rows_filtered)} rows (removed {removed} without DK+FD)")
        
        all_rows.extend(rows_filtered)
    
    append_to_csv(all_rows)
    
    print(f"\n[DONE] Total rows: {len(all_rows)}")
    print(f"[FILE] {RAW_CSV}")


if __name__ == "__main__":
    main()
