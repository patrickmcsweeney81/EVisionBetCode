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

import csv
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment - look for .env in project root
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # src/pipeline_v2 -> root/.env
    Path(__file__).parent.parent / ".env",  # fallback to src/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break
API_KEY = os.getenv("ODDS_API_KEY", "")


# File locations - use absolute paths for reliability
# Try multiple locations to support both local and Render deployments
def get_data_dir():
    """Find data directory - robust for Render and local dev."""
    cwd = Path.cwd()
    # Strip duplicate /src/src patterns (Render bug)
    cwd_str = str(cwd).replace("\\src\\src", "\\src").replace("/src/src", "/src")
    cwd = Path(cwd_str)

    # Priority 1: cwd/data
    data_path = cwd / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    if data_path.exists() and data_path.is_dir():
        return data_path

    # Priority 2: parent/data if cwd is /src
    if cwd.name == "src":
        data_path = cwd.parent / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        if data_path.exists() and data_path.is_dir():
            return data_path

    # Priority 3: script parent
    script_parent = Path(__file__).parent.parent
    data_path = script_parent / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    if data_path.exists() and data_path.is_dir():
        return data_path

    return cwd / "data"


DATA_DIR = get_data_dir()
RAW_CSV = DATA_DIR / "raw_odds_pure.csv"

# API Configuration
ODDS_API_HOST = "https://api.the-odds-api.com"
# Sports list - reads from SPORTS env var (comma-separated), or uses default
DEFAULT_SPORTS = "basketball_nba,basketball_nbl,americanfootball_nfl,americanfootball_ncaaf,icehockey_nhl,baseball_mlb,soccer_epl,soccer_uefa_champs_league,tennis_atp,tennis_wta,cricket_big_bash,cricket_ipl"
SPORTS = [s.strip() for s in os.getenv("SPORTS", DEFAULT_SPORTS).split(",")]
# Include EU to ensure Pinnacle is returned by The Odds API
# Cost note: adding EU increases credits vs au,us only
REGIONS = os.getenv("REGIONS", "au,us,eu")
ODDS_FORMAT = "decimal"  # Always decimal for calculations

# Time filtering for events (optimize credit usage)
EVENT_MIN_MINUTES = int(os.getenv("EVENT_MIN_MINUTES", "5"))  # Don't fetch events starting <X min from now
EVENT_MAX_HOURS = int(os.getenv("EVENT_MAX_HOURS", "24"))  # Don't fetch events >X hrs from now (24h = focus on today's games)

# Storage management
MAX_CSV_ROWS = int(os.getenv("MAX_CSV_ROWS", "50000"))  # Max rows before cleanup (50k ≈ 10MB)
MAX_DB_DAYS = int(os.getenv("MAX_DB_DAYS", "7"))  # Keep last N days in database

# Player props - REDUCED for credit efficiency (focus on most liquid markets)
# Enable/disable via env var: ENABLE_PROPS=true (default: false to save credits)
ENABLE_PROPS = os.getenv("ENABLE_PROPS", "false").lower() == "true"

NBA_PROPS = [
    "player_points",  # Points scored (most liquid)
    "player_rebounds",  # Rebounds
    "player_assists",  # Assists
    "player_points_rebounds_assists",  # PRA (most popular combo)
] if ENABLE_PROPS else []

NFL_PROPS = [
    "player_pass_yds",  # Passing yards (QB - most liquid)
    "player_rush_yds",  # Rushing yards (RB)
    "player_reception_yds",  # Reception yards (WR/TE)
    "player_anytime_td",  # Anytime TD (popular)
] if ENABLE_PROPS else []

NCAAF_PROPS = [
    "player_pass_yds",
    "player_rush_yds",
    "player_reception_yds",
] if ENABLE_PROPS else []

NHL_PROPS = [
    "player_points",  # Points (goals + assists) - most liquid
    "player_shots_on_goal",  # Shots on goal
    "player_assists",  # Assists
    "player_goals",  # Goals scored
    "player_blocked_shots",  # Blocked shots
    "player_power_play_points",  # Power play points
    "player_goal_scorer_anytime",  # Anytime goal scorer
    "player_goal_scorer_first",  # First goal scorer
    "player_goal_scorer_last",  # Last goal scorer
] if ENABLE_PROPS else []

EPL_PROPS = [
    "player_goals",  # Goals scored - most liquid
    "player_assists",  # Assists
    "player_shots",  # Total shots
    "player_shots_on_target",  # Shots on target
    "player_goal_scorer_anytime",  # Anytime goal scorer (popular)
    "player_first_goal_scorer",  # First goal scorer (API uses this key)
    "player_last_goal_scorer",  # Last goal scorer (API uses this key)
    "player_goalie_saves_alternate",  # Goalie saves (API uses _alternate)
    "player_tackles_alternate",  # Tackles (API uses _alternate)
    "player_to_receive_card",  # Yellow/red cards
] if ENABLE_PROPS else []

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

# Bookmaker column order: Sharp books first, then AU, then US/EU/UK
DEFAULT_BOOKMAKER_ORDER = [
    # Sharp books (fair price sources)
    "Pinnacle",
    "Betfair_EU",
    "Betfair_UK",
    "Betfair_AU",
    "Draftkings",
    "Fanduel",
    "Betmgm",
    "Betonline",
    "Bovada",
    "Lowvig",
    "Mybookie",
    "Betrivers",
    "Marathonbet",
    "Betsson",
    "Nordicbet",
    # AU books (primary target)
    "Sportsbet",
    "Pointsbet",
    "Tab",
    "Tabtouch",
    "Unibet_AU",
    "Ladbrokes_AU",
    "Neds",
    "Betr",
    "Boombet",
    # US books
    "Williamhill_US",
    "Sbk",
    "Fanatics",
    "Ballybet",
    "Betparx",
    "Espnbet",
    "Fliff",
    "Hardrockbet",
    "Rebet",
    # UK books
    "Williamhill_UK",
    "Betvictor",
    "Bwin",
    "Coral",
    "Skybet",
    "Paddypower",
    "Boylesports",
    "Betfred",
    # EU books
    "Williamhill_EU",
    "Codere",
    "Tipico",
    "Leovegas",
    "Parionssport",
    "Winamax_FR",
    "Winamax_DE",
    "Unibet_FR",
    "Unibet_NL",
    "Unibet_SE",
    "Betclic",
]


def parse_bookmaker_order() -> List[str]:
    """Allow overriding bookmaker column order via BOOKMAKER_ORDER env.

    Example: BOOKMAKER_ORDER="Pinnacle,Betfair_EU,Draftkings,Fanduel"
    """
    override = os.getenv("BOOKMAKER_ORDER", "")
    if not override:
        return DEFAULT_BOOKMAKER_ORDER

    parsed: List[str] = []
    for name in [p.strip() for p in override.split(",")]:
        if name and name not in parsed:
            parsed.append(name)

    if parsed:
        print(f"[CONFIG] BOOKMAKER_ORDER override ({len(parsed)}): {', '.join(parsed)}")
        return parsed

    return DEFAULT_BOOKMAKER_ORDER


BOOKMAKER_ORDER = parse_bookmaker_order()

CSV_HEADERS = BASE_HEADERS + BOOKMAKER_ORDER

# Mapping bookmaker keys to CSV column names
BOOKMAKER_TO_COLUMN = {
    # Sharp books
    "pinnacle": "Pinnacle",
    "betfair_ex_eu": "Betfair_EU",
    "betfair_ex_uk": "Betfair_UK",
    "betfair_ex_au": "Betfair_AU",
    "betfair": "Betfair_EU",
    "draftkings": "Draftkings",
    "fanduel": "Fanduel",
    "betmgm": "Betmgm",
    "betonlineag": "Betonline",
    "bovada": "Bovada",
    "lowvig": "Lowvig",
    "mybookieag": "Mybookie",
    "betrivers": "Betrivers",
    "marathonbet": "Marathonbet",
    "betsson": "Betsson",
    "nordicbet": "Nordicbet",
    # AU books
    "sportsbet": "Sportsbet",
    "pointsbetau": "Pointsbet",
    "tab": "Tab",
    "tabtouch": "Tabtouch",
    "unibet": "Unibet_AU",
    "unibet_au": "Unibet_AU",
    "ladbrokes_au": "Ladbrokes_AU",
    "neds": "Neds",
    "betr_au": "Betr",
    "boombet": "Boombet",
    # US books
    "williamhill_us": "Williamhill_US",
    "sbk": "Sbk",
    "fanatics": "Fanatics",
    "ballybet": "Ballybet",
    "betparx": "Betparx",
    "espnbet": "Espnbet",
    "fliff": "Fliff",
    "hardrockbet": "Hardrockbet",
    "rebet": "Rebet",
    # UK books
    "williamhill": "Williamhill_UK",
    "williamhill_uk": "Williamhill_UK",
    "betvictor": "Betvictor",
    "bwin": "Bwin",
    "coral": "Coral",
    "skybet": "Skybet",
    "paddypower": "Paddypower",
    "boylesports": "Boylesports",
    "betfred": "Betfred",
    # EU books
    "williamhill_eu": "Williamhill_EU",
    "codere_it": "Codere",
    "tipico_de": "Tipico",
    "leovegas_se": "Leovegas",
    "leovegas": "Leovegas",
    "parionssport_fr": "Parionssport",
    "winamax_fr": "Winamax_FR",
    "winamax_de": "Winamax_DE",
    "unibet_fr": "Unibet_FR",
    "unibet_nl": "Unibet_NL",
    "unibet_se": "Unibet_SE",
    "betclic_fr": "Betclic",
}


def is_event_in_time_window(commence_time: str) -> bool:
    """Check if event starts within [5 min, 48 hrs] from now."""
    try:
        event_time = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
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
    outcomes = market_data.get("outcomes", [])
    market_key = market_data.get("key", "")

    # Must have even number of outcomes (pairs)
    if len(outcomes) % 2 != 0:
        return False

    # CRITICAL: Core markets (h2h, h2h_lay, spreads, totals) must have EXACTLY 2 outcomes
    # This filters out 3-way markets with draws (Home/Away/Draw)
    if market_key in ["h2h", "h2h_lay", "spreads", "totals"]:
        return len(outcomes) == 2  # ONLY 2-way markets allowed

    # Player props: check if we have Over/Under pattern
    # Exclude Yes/No markets (1-way bets like double_double, first_basket)
    outcome_names = [o.get("name", "").lower() for o in outcomes]
    has_yes = any("yes" in name for name in outcome_names)
    has_no = any("no" in name for name in outcome_names)

    # Filter out Yes/No markets completely
    if has_yes or has_no:
        return False

    has_over = any("over" in name for name in outcome_names)
    has_under = any("under" in name for name in outcome_names)

    # If it has Over/Under structure, it's valid
    if has_over and has_under:
        return True

    # Reject anything else
    return False


def has_dk_and_fd_odds(bookmakers: List[Dict]) -> bool:
    """Check if this event/market has odds from BOTH Draftkings AND Fanduel.
    Filters to only markets with sharp book coverage to save API credits.
    """
    bookie_keys = {b.get("key", "").lower() for b in bookmakers}

    has_dk = "draftkings" in bookie_keys
    has_fd = "fanduel" in bookie_keys

    return has_dk and has_fd


def get_props_for_sport(sport_key: str) -> List[str]:
    """Return player prop markets for this sport."""
    if "nba" in sport_key.lower():
        return NBA_PROPS
    elif "nfl" in sport_key.lower():
        return NFL_PROPS
    elif "nhl" in sport_key.lower():
        return NHL_PROPS
    elif "soccer" in sport_key.lower():
        return EPL_PROPS  # Works for EPL, UEFA, etc.
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
        print(f"[!] No props defined for {sport_key} – returning original events")
        return events  # Return core market events when props disabled

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
                    orig_bm = next(
                        (b for b in orig_bookmakers if b.get("key") == prop_bm.get("key")), None
                    )
                    if orig_bm:
                        orig_markets = orig_bm.get("markets", [])
                        for m in prop_bm.get("markets", []):
                            if m.get("key") not in [
                                om.get("key") for om in orig_markets
                            ] and is_two_way_market(m):
                                orig_bm["markets"].append(m)
                    else:
                        filtered_markets = [
                            m for m in prop_bm.get("markets", []) if is_two_way_market(m)
                        ]
                        if filtered_markets:
                            prop_bm["markets"] = filtered_markets
                            orig_bookmakers.append(prop_bm)

                event["bookmakers"] = orig_bookmakers

                remaining = resp.headers.get("x-requests-remaining", "?")
                cost = resp.headers.get("x-requests-last", "?")
                print(
                    f"      Event {event_idx}/{len(events_in_window)}: Cost {cost}, Remaining: {remaining}"
                )

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
    """Write rows to CSV file (REPLACE mode to prevent bloat) and database."""
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

    csv_success = False
    try:
        # REPLACE mode - overwrite old data to prevent bloat
        with open(RAW_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=final_headers)
            writer.writeheader()
            writer.writerows(rows)
            print(f"[CSV] Wrote {len(rows)} rows (REPLACE mode - old data cleared)")
            print(f"[CSV] Headers ({len(final_headers)}): {', '.join(final_headers[:20])}...")
            csv_success = True

    except PermissionError as e:
        fallback = (
            DATA_DIR / f"raw_odds_pure_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"
        )
        try:
            with open(fallback, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=final_headers)
                writer.writeheader()
                writer.writerows(rows)
            print(f"[CSV] Primary file locked; wrote to {fallback}")
            csv_success = True
        except Exception as inner:
            print(f"[!] Error writing fallback CSV: {inner}")
    except Exception as e:
        print(f"[!] Error writing CSV: {e}")

    # =========================================================================
    # DATABASE WRITE with automatic cleanup (REPLACE mode to prevent bloat)
    # =========================================================================
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            from sqlalchemy import text
            
            df = pd.DataFrame(rows)
            engine = create_engine(db_url)
            
            # REPLACE strategy: Clear old data before inserting new
            with engine.connect() as conn:
                # Option 1: Truncate table (fastest - removes all data)
                try:
                    conn.execute(text("TRUNCATE TABLE raw_odds_pure"))
                    conn.commit()
                    print(f"[DB] Truncated old data from raw_odds_pure")
                except Exception:
                    # Option 2: Delete with timestamp filter (keep last N hours if truncate fails)
                    try:
                        conn.execute(text(
                            f"DELETE FROM raw_odds_pure WHERE timestamp < NOW() - INTERVAL '{MAX_DB_DAYS} days'"
                        ))
                        conn.commit()
                        print(f"[DB] Deleted data older than {MAX_DB_DAYS} days")
                    except Exception as del_err:
                        print(f"[DB] Cleanup failed (table may not exist yet): {del_err}")
            
            # Write new data
            df.to_sql(
                "raw_odds_pure",
                engine,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )
            print(f"[OK] {len(rows)} rows written to database (REPLACE mode)")
        except Exception as e:
            print(f"[!] Database write failed: {e}")
            if not csv_success:
                print(f"[!] WARNING: Data loss – neither CSV nor database write succeeded")
    else:
        if csv_success:
            print(f"[OK] DATABASE_URL not set – CSV output saved")
        else:
            print(f"[!] WARNING: No local storage AND no DATABASE_URL – data not persisted")


def process_sport(sport_key: str, timestamp: str) -> List[Dict]:
    """Fetch and process a single sport (for parallel execution)."""
    print(f"\n=== {sport_key.upper()} ===")

    core_markets = ["h2h", "spreads", "totals"]
    print(f"[API] Fetching core markets: {core_markets}")

    events = fetch_raw_odds(sport_key, core_markets)
    if not events:
        print(f"[!] No events for {sport_key}")
        return []

    print(f"[OK] Got {len(events)} core market events")

    print(f"[*] Fetching player props...")
    events_with_props = fetch_player_props(sport_key, events)

    rows = expand_to_rows(events_with_props, timestamp)
    print(f"[OK] Expanded to {len(rows)} rows")

    # Filter to only rows with DK+FD coverage
    rows_filtered = filter_rows_by_dk_fd(rows, verbose=True)
    removed = len(rows) - len(rows_filtered)
    print(f"[OK] Filtered to {len(rows_filtered)} rows (removed {removed} without DK+FD)")

    return rows_filtered


def main():
    """Main extraction flow with parallel sport fetching."""

    # Debug output
    print(f"[DEBUG] Script location: {Path(__file__).resolve()}")
    print(f"[DEBUG] Working directory: {Path.cwd()}")
    print(f"[DEBUG] Data directory: {DATA_DIR}")
    print(f"[DEBUG] Raw CSV path: {RAW_CSV}")
    print()

    if not API_KEY:
        print("[!] ODDS_API_KEY not set in .env")
        sys.exit(1)

    DATA_DIR.mkdir(exist_ok=True)
    print(f"[OK] Data directory ready: {DATA_DIR}")

    timestamp = datetime.now(timezone.utc).isoformat()
    all_rows = []

    # Fetch all sports in parallel (4-5 concurrent threads)
    print(f"\n[PARALLEL] Fetching {len(SPORTS)} sports concurrently...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all sports at once
        futures = {
            executor.submit(process_sport, sport_key, timestamp): sport_key for sport_key in SPORTS
        }

        # Collect results as they complete
        for future in as_completed(futures):
            sport_key = futures[future]
            try:
                rows = future.result()
                all_rows.extend(rows)
                print(f"[OK] {sport_key} complete: {len(rows)} rows added")
            except Exception as e:
                print(f"[!] {sport_key} failed: {e}")

    append_to_csv(all_rows)

    print(f"\n[DONE] Total rows: {len(all_rows)}")
    print(f"[FILE] {RAW_CSV}")


if __name__ == "__main__":
    main()
