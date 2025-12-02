# --- CSV Formatting Helpers ---
from datetime import datetime

def format_local_time(utc_time_str):
    """Convert UTC ISO time string to local time, format as 'hh:mm am/pm dd/mm/yyyy'"""
    try:
        utc_dt = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
        # Use system local timezone
        local_tz = datetime.now().astimezone().tzinfo
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime('%I:%M %p %d/%m/%Y')
    except Exception:
        return utc_time_str

def abbreviate_sport(sport_key):
    mapping = {
        'basketball_nba': 'NBA',
        'basketball_ncaab': 'NCAAB',
        'basketball_euroleague': 'Euro',
        'americanfootball_nfl': 'NFL',
        'americanfootball_ncaaf': 'NCAAF',
        'baseball_mlb': 'MLB',
        'icehockey_nhl': 'NHL',
        'soccer_epl': 'EPL',
        'soccer_uefa_champs_league': 'UCL',
        'tennis_atp': 'ATP',
        'tennis_wta': 'WTA',
        # Add more as needed
    }
    return mapping.get(sport_key, sport_key.split('_')[-1].upper())

def abbreviate_event(away, home):
    def short_team(name):
        # Use last word if multi-word, else as is
        return name.split()[-1] if ' ' in name else name
    return f"{short_team(away)} v {short_team(home)}"

def abbreviate_market(market_key):
    mapping = {
        'player_points': 'Points',
        'player_rebounds': 'Rebounds',
        'player_assists': 'Assists',
        'player_threes': '3PT Made',
        'player_blocks': 'Blocks',
        'player_steals': 'Steals',
        'player_turnovers': 'Turnovers',
        'player_points_rebounds_assists': 'Points, Rebounds, Assists',
        'player_points_assists': 'Points, Assists',
        'player_points_rebounds': 'Points, Rebounds',
        'player_assists_rebounds': 'Assists, Rebounds',
        'player_double_double': 'Double Double',
        'player_first_basket': 'First Basket',
        # Add more as needed
    }
    # Remove 'player_' prefix and underscores if not mapped
    return mapping.get(market_key, market_key.replace('player_', '').replace('_', ' ').title())
"""
EV Arbitrage Bot - MODULAR VERSION
Uses clean handler modules from core/ directory.

This is a streamlined rewrite focusing on:
1. NO AU BOOKS in fair price calculation
2. Clean separation of market logic
3. Easy to debug and maintain
"""
import os
import sys
import json
import csv
import hashlib
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Import our clean handlers
from core.h2h_handler import process_h2h_event_v2
from core.spreads_handler import process_spread_event
from core.totals_handler import process_totals_event
from core.player_props_handler_NEW import process_player_props_event
from core.nfl_props_handler import process_nfl_props_event
from core.utils import kelly_stake
from core.logging import log_all_odds
from core.config import (
    AU_BOOKIES, SHARP_BOOKIES, US_BOOKIES, ALL_BOOKIES_ORDERED,
    EV_MIN_EDGE as DEFAULT_EV_MIN_EDGE,
    MIN_PROB as DEFAULT_MIN_PROB,
    MIN_STAKE as DEFAULT_MIN_STAKE,
    BANKROLL as DEFAULT_BANKROLL,
    KELLY_FRACTION as DEFAULT_KELLY_FRACTION,
    BETFAIR_COMMISSION as DEFAULT_BETFAIR_COMMISSION,
    MIN_TIME_TO_START_MINUTES as DEFAULT_MIN_TIME_TO_START,
    MAX_TIME_TO_START_HOURS as DEFAULT_MAX_TIME_TO_START,
    DATA_DIR_NAME, DEDUP_FILE_NAME, ALL_ODDS_CSV_NAME,
    ENABLE_EV_FILTER, ENABLE_PROB_FILTER,
    SPORT_PROP_MARKETS
)
from core.exotics_logger import log_exotic_value

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration (env vars override config defaults)
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = os.getenv("ODDS_API_BASE", "https://api.the-odds-api.com/v4")
REGIONS = os.getenv("REGIONS", "au,us")
# Disable player props for this run
MARKETS = "h2h,spreads,totals"
SPORTS = os.getenv("SPORTS", "basketball_nba")
API_TIER = os.getenv("API_TIER", "medium").lower()  # low|medium|high
INCLUDE_US_BOOKS = os.getenv("INCLUDE_US_BOOKS", "0").lower() in ("1", "true", "yes", "y")

def parse_float(key: str, default: float) -> float:
    """Parse float from env, handling inline comments."""
    env_val = os.getenv(key)
    if env_val:
        val = env_val.split("#")[0].strip()
        return float(val)
    return default

EV_MIN_EDGE = parse_float("EV_MIN_EDGE", DEFAULT_EV_MIN_EDGE)
MIN_PROB = parse_float("MIN_PROB", DEFAULT_MIN_PROB)
MIN_STAKE = parse_float("MIN_STAKE", DEFAULT_MIN_STAKE)
BANKROLL = parse_float("BANKROLL", DEFAULT_BANKROLL)
KELLY_FRACTION = parse_float("KELLY_FRACTION", DEFAULT_KELLY_FRACTION)
BETFAIR_COMMISSION = parse_float("BETFAIR_COMMISSION", DEFAULT_BETFAIR_COMMISSION)
MIN_TIME_TO_START_MINUTES = parse_float("MIN_TIME_TO_START_MINUTES", DEFAULT_MIN_TIME_TO_START)
# Cap far-future event window to 48 hours max
MAX_TIME_TO_START_HOURS = parse_float("MAX_TIME_TO_START_HOURS", DEFAULT_MAX_TIME_TO_START)
if MAX_TIME_TO_START_HOURS <= 0 or MAX_TIME_TO_START_HOURS > 48:
    MAX_TIME_TO_START_HOURS = 48.0
STALE_EVENT_HOURS = parse_float("STALE_EVENT_HOURS", 24.0)  # Skip events older than this window
REFRESH_EVENT_MINUTES = parse_float("REFRESH_EVENT_MINUTES", 30.0)  # Do not re-log events within this recency window

# Data files (using config constants)
DATA_DIR = Path(__file__).parent / DATA_DIR_NAME
DATA_DIR.mkdir(exist_ok=True)
DEDUP_FILE = DATA_DIR / DEDUP_FILE_NAME
# EV_CSV removed - use filter_ev_hits.py to generate hits from all_odds_analysis.csv
ALL_ODDS_CSV = DATA_DIR / ALL_ODDS_CSV_NAME

# Allowed CSV outputs (enforced cleanup): only comprehensive analysis and filtered EV summary
ALLOWED_CSV_FILES = {ALL_ODDS_CSV.name, "all_odds.csv"}

# Simple in-memory caches for this run
SESSION_EVENT_CACHE = {}
SESSION_PROPS_CACHE = {}

# Active bookmaker sets (AU only by default, optionally include US mass-market books)
if INCLUDE_US_BOOKS:
    ACTIVE_BOOKIES = set(AU_BOOKIES + US_BOOKIES)
else:
    ACTIVE_BOOKIES = set(AU_BOOKIES)

# Ordered subset for CSV columns (respect master ordering)
CSV_BOOKIES = [b for b in ALL_BOOKIES_ORDERED if b in ACTIVE_BOOKIES]

# API usage counters (per run)
API_USAGE = {
    "sports_calls": 0,
    "props_calls": 0,
    "events_processed": 0,
    "events_skipped_time": 0,
    "events_skipped_cache": 0,
    "events_skipped_stale": 0,
}

def cleanup_data_directory():
    """Purge previous run CSVs.
    - Remove any non-allowed CSV artifacts.
    - Also delete the allowed CSVs (all_odds_analysis.csv, all_odds.csv) so each run starts fresh.
    This prevents stale / past games persisting across runs.
    """
    try:
        for fp in DATA_DIR.glob("*.csv"):
            # Always remove allowed + extraneous; raw logger will recreate headers as needed.
            try:
                fp.unlink()
                print(f"[clean] Purged CSV: {fp.name}")
            except Exception as e:
                print(f"[clean] Could not remove {fp.name}: {e}")
    except Exception as e:
        print(f"[clean] Directory cleanup error: {e}")

def save_api_usage():
    """Persist API usage counters to data/api_usage.json (append/merge per run)."""
    try:
        usage_path = DATA_DIR / "api_usage.json"
        existing = {}
        if usage_path.exists():
            try:
                existing = json.load(open(usage_path, "r", encoding="utf-8"))
            except Exception:
                existing = {}
        # Merge: keep a small history with timestamp key
        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        existing[ts] = API_USAGE
        with open(usage_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"[api-usage] Save error: {e}")


EVENT_CACHE_FILE = DATA_DIR / "cache_events.json"
EVENT_CACHE: Dict[str, str] = {}

def load_event_cache() -> None:
    """Load disk-backed event cache of last processed timestamps."""
    global EVENT_CACHE
    if EVENT_CACHE_FILE.exists():
        try:
            EVENT_CACHE = json.load(open(EVENT_CACHE_FILE, "r", encoding="utf-8"))
        except Exception:
            EVENT_CACHE = {}

def save_event_cache() -> None:
    """Persist event cache."""
    try:
        with open(EVENT_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(EVENT_CACHE, f, indent=2)
    except Exception as e:
        print(f"[cache] Save error: {e}")


def load_dedupe() -> Dict[str, bool]:
    """Load seen hits from JSON."""
    if DEDUP_FILE.exists():
        try:
            with open(DEDUP_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_dedupe(seen: Dict[str, bool]):
    """Save seen hits to JSON."""
    try:
        with open(DEDUP_FILE, "w") as f:
            json.dump(seen, f, indent=2)
    except Exception as e:
        print(f"[!] Error saving dedupe: {e}")


def make_hash(event_id: str, market: str, selection: str, bookmaker: str) -> str:
    """Create deduplication hash."""
    key = f"{event_id}|{market}|{selection}|{bookmaker}"
    return hashlib.sha1(key.encode()).hexdigest()


# Logging functions moved to core/logging.py for clean architecture


def calculate_edge(book_odds: float, fair_odds: float) -> float:
    """Calculate EV edge percentage."""
    if fair_odds <= 0:
        return 0.0
    fair_prob = 1.0 / fair_odds
    book_prob = 1.0 / book_odds if book_odds > 0 else 1.0
    edge = (fair_prob * book_odds - 1.0)
    return edge


def process_h2h_market(event: Dict, seen: Dict[str, bool]) -> int:
    """Process h2h market for one event."""
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    sport_key = event.get("sport_key", "")
    event_id = event.get("id", "")
    commence_time = event.get("commence_time", "")
    
    # Get fair prices using unified handler (v2 with book_weights)
    result = process_h2h_event_v2(event, home_team, away_team, sport_key, BETFAIR_COMMISSION)
    
    if not result:
        return 0
    
    fair_prices = result.get("fair", {})
    bookmakers_data = result.get("bookmakers", {})
    
    fair_home = fair_prices.get("home", 0)
    fair_away = fair_prices.get("away", 0)
    
    if fair_home <= 0 or fair_away <= 0:
        return 0
    
    # Get Pinnacle/Betfair for analysis logging
    pinnacle_data = result.get("pinnacle", {})
    betfair_data = result.get("betfair", {})
    pin_home = pinnacle_data.get("home", 0)
    pin_away = pinnacle_data.get("away", 0)
    bf_home = betfair_data.get("home", 0)
    bf_away = betfair_data.get("away", 0)
    
    # Note: ALL raw odds logging now happens in main loop via raw_odds_logger
    # This avoids duplication and ensures logging even when fair calc fails
    
    hits = 0
    
    # Collect all edges for home and away teams
    home_opportunities = []
    away_opportunities = []
    
    for bkey, bk_odds in bookmakers_data.items():
        if bkey not in ACTIVE_BOOKIES:
            continue
        
        # Check home team
        home_odds = bk_odds.get(home_team, 0)
        if home_odds and home_odds > 0:
            edge = calculate_edge(home_odds, fair_home)
            fair_prob = 1.0 / fair_home
            
            edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
            prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
            
            if edge_check and prob_check:
                home_opportunities.append((bkey, home_odds, edge, fair_prob))
        
        # Check away team
        away_odds = bk_odds.get(away_team, 0)
        if away_odds and away_odds > 0:
            edge = calculate_edge(away_odds, fair_away)
            fair_prob = 1.0 / fair_away
            
            edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
            prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
            
            if edge_check and prob_check:
                away_opportunities.append((bkey, away_odds, edge, fair_prob))
    
    # Process home team - log only max edge
    if home_opportunities:
        max_edge = max(opp[2] for opp in home_opportunities)
        max_edge_opps = [opp for opp in home_opportunities if opp[2] == max_edge]
        
        # Combine bookmakers with same max edge
        bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
        first_opp = max_edge_opps[0]
        bkey, home_odds, edge, fair_prob = first_opp
        
        # Check filters before logging
        if ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
            # Calculate stake only if edge is positive
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_home, home_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            hit_hash = make_hash(event_id, "h2h", home_team, bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Start Time": format_local_time(commence_time),
                    "Sport": abbreviate_sport(sport_key),
                    "Event": abbreviate_event(away_team, home_team),
                    "Market": "H2H",
                    "Selection": home_team,
                    "O/U + Y/N": "",
                    "Book": bookmakers_str,
                    "Price": f"{home_odds:.3f}",
                    "Pinnacle": f"{pin_home:.3f}" if pin_home > 0 else "",
                    "Betfair": f"{bf_home:.3f}" if bf_home > 0 else "",
                }
                
                # Add bookmaker odds (AU + optional US)
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        team_odds = bookmakers_data[bk_key].get(home_team, 0)
                        if team_odds > 0:
                            ev_row[bk_key] = f"{team_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} {home_team:30s} {home_odds:.3f} (fair={fair_home:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
    
    # Process away team - log only max edge
    if away_opportunities:
        max_edge = max(opp[2] for opp in away_opportunities)
        max_edge_opps = [opp for opp in away_opportunities if opp[2] == max_edge]
        
        # Combine bookmakers with same max edge
        bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
        first_opp = max_edge_opps[0]
        bkey, away_odds, edge, fair_prob = first_opp
        
        # Check filters before logging
        if ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
            # Calculate stake only if edge is positive
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_away, away_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            hit_hash = make_hash(event_id, "h2h", away_team, bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Time": commence_time,
                    "sport": sport_key,
                    "event": f"{away_team} @ {home_team}",
                    "market": "h2h",
                    "selection": away_team,
                    "bookmaker": bookmakers_str,
                    "Odds": f"{away_odds:.3f}",
                    "Fair": f"{fair_away:.3f}",
                    "EV": f"{edge*100:.2f}%",
                    "prob": f"{fair_prob*100:.1f}%",
                    "Stake": stake_str,
                    "pinnacle": f"{pin_away:.3f}" if pin_away > 0 else "",
                    "betfair": f"{bf_away:.3f}" if bf_away > 0 else "",
                }
                
                # Add bookmaker odds (AU + optional US)
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        team_odds = bookmakers_data[bk_key].get(away_team, 0)
                        if team_odds > 0:
                            ev_row[bk_key] = f"{team_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} {away_team:30s} {away_odds:.3f} (fair={fair_away:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
    
    return hits


def process_spreads_market(event: Dict, seen: Dict[str, bool]) -> int:
    """Process spreads market for an event using max-edge logic."""
    sport_key = event.get("sport_key", "")
    event_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time = event.get("commence_time", "")
    
    if not all([sport_key, event_id, home_team, away_team]):
        return 0
    
    # Get available spread lines from Pinnacle
    bookmakers = event.get("bookmakers", [])
    pinnacle_lines = set()
    
    for bk in bookmakers:
        if bk.get("key") == "pinnacle":
            for market in bk.get("markets", []):
                if market.get("key") == "spreads":
                    for outcome in market.get("outcomes", []):
                        point = outcome.get("point")
                        if point is not None:
                            pinnacle_lines.add(abs(float(point)))
    
    if not pinnacle_lines:
        return 0  # No Pinnacle spreads available
    
    hits = 0
    
    # Process each spread line
    for line in pinnacle_lines:
        result = process_spread_event(event, line, home_team, away_team, BETFAIR_COMMISSION, sport=sport_key)
        
        if not result:
            continue
        
        fair_data = result.get("fair", {})
        fair_home = fair_data.get("home", 0)
        fair_away = fair_data.get("away", 0)
        
        if fair_home <= 0 or fair_away <= 0:
            continue
        
        bookmakers_data = result.get("bookmakers", {})
        keys = result.get("keys", {})
        home_key = keys.get("home", "")
        away_key = keys.get("away", "")
        
        # Get Pinnacle/Betfair for CSV
        pinnacle_data = result.get("pinnacle", {}) or {}
        betfair_data = result.get("betfair", {}) or {}
        pin_home = pinnacle_data.get("home", 0) or 0
        pin_away = pinnacle_data.get("away", 0) or 0
        bf_home = betfair_data.get("home", 0) or 0
        bf_away = betfair_data.get("away", 0) or 0
        
        # Collect all edges for home and away
        home_opportunities = []
        away_opportunities = []
        
        for bkey, bk_spread_odds in bookmakers_data.items():
            if bkey not in ACTIVE_BOOKIES:
                continue
            
            # Check home team spread
            home_odds = bk_spread_odds.get(home_key, 0)
            if home_odds and home_odds > 0:
                edge = calculate_edge(home_odds, fair_home)
                fair_prob = 1.0 / fair_home
                
                edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
                prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
                
                if edge_check and prob_check:
                    home_opportunities.append((bkey, home_odds, edge, fair_prob))
            
            # Check away team spread
            away_odds = bk_spread_odds.get(away_key, 0)
            if away_odds and away_odds > 0:
                edge = calculate_edge(away_odds, fair_away)
                fair_prob = 1.0 / fair_away
                
                edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
                prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
                
                if edge_check and prob_check:
                    away_opportunities.append((bkey, away_odds, edge, fair_prob))
        
        # Process home spread - log only max edge
        if home_opportunities:
            max_edge = max(opp[2] for opp in home_opportunities)
            max_edge_opps = [opp for opp in home_opportunities if opp[2] == max_edge]
            
            bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
            first_opp = max_edge_opps[0]
            bkey, home_odds, edge, fair_prob = first_opp
            
            # Check filters before logging
            if not ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
                continue
            
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_home, home_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            hit_hash = make_hash(event_id, f"spread_{line}", home_key, bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Time": commence_time,
                    "sport": sport_key,
                    "event": f"{away_team} @ {home_team}",
                    "market": f"spread_{line}",
                    "selection": home_key,
                    "bookmaker": bookmakers_str,
                    "Odds": f"{home_odds:.3f}",
                    "Fair": f"{fair_home:.3f}",
                    "EV": f"{edge*100:.2f}%",
                    "prob": f"{fair_prob*100:.1f}%",
                    "Stake": stake_str,
                    "pinnacle": f"{pin_home:.3f}" if pin_home > 0 else "",
                    "betfair": f"{bf_home:.3f}" if bf_home > 0 else "",
                }
                
                # Add bookmaker odds
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        spread_odds = bookmakers_data[bk_key].get(home_key, 0)
                        if spread_odds > 0:
                            ev_row[bk_key] = f"{spread_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} {home_key:30s} {home_odds:.3f} (fair={fair_home:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
        
        # Process away spread - log only max edge
        if away_opportunities:
            max_edge = max(opp[2] for opp in away_opportunities)
            max_edge_opps = [opp for opp in away_opportunities if opp[2] == max_edge]
            
            bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
            first_opp = max_edge_opps[0]
            bkey, away_odds, edge, fair_prob = first_opp
            
            # Check filters before logging
            if not ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
                continue
            
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_away, away_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            hit_hash = make_hash(event_id, f"spread_{line}", away_key, bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Time": commence_time,
                    "sport": sport_key,
                    "event": f"{away_team} @ {home_team}",
                    "market": f"spread_{line}",
                    "selection": away_key,
                    "bookmaker": bookmakers_str,
                    "Odds": f"{away_odds:.3f}",
                    "Fair": f"{fair_away:.3f}",
                    "EV": f"{edge*100:.2f}%",
                    "prob": f"{fair_prob*100:.1f}%",
                    "Stake": stake_str,
                    "pinnacle": f"{pin_away:.3f}" if pin_away > 0 else "",
                    "betfair": f"{bf_away:.3f}" if bf_away > 0 else "",
                }
                
                # Add bookmaker odds
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        spread_odds = bookmakers_data[bk_key].get(away_key, 0)
                        if spread_odds > 0:
                            ev_row[bk_key] = f"{spread_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} {away_key:30s} {away_odds:.3f} (fair={fair_away:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
    
    return hits


def process_totals_market(event: Dict, seen: Dict[str, bool]) -> int:
    """Process totals (over/under) market for an event using max-edge logic."""
    sport_key = event.get("sport_key", "")
    event_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time = event.get("commence_time", "")
    
    if not all([sport_key, event_id, home_team, away_team]):
        return 0
    
    # Get available total lines from Pinnacle
    bookmakers = event.get("bookmakers", [])
    pinnacle_lines = set()
    
    for bk in bookmakers:
        if bk.get("key") == "pinnacle":
            for market in bk.get("markets", []):
                if market.get("key") == "totals":
                    for outcome in market.get("outcomes", []):
                        point = outcome.get("point")
                        if point is not None:
                            pinnacle_lines.add(float(point))
    
    if not pinnacle_lines:
        return 0  # No Pinnacle totals available
    
    hits = 0
    
    # Process each total line
    for line in pinnacle_lines:
        result = process_totals_event(event, line, BETFAIR_COMMISSION, sport=sport_key)
        
        if not result:
            continue
        
        fair_data = result.get("fair", {})
        fair_over = fair_data.get("over", 0)
        fair_under = fair_data.get("under", 0)
        
        if fair_over <= 0 or fair_under <= 0:
            continue
        
        bookmakers_data = result.get("bookmakers", {})
        
        # Get Pinnacle/Betfair for CSV
        pinnacle_data = result.get("pinnacle", {}) or {}
        betfair_data = result.get("betfair", {}) or {}
        pin_over = pinnacle_data.get("Over", 0) or 0
        pin_under = pinnacle_data.get("Under", 0) or 0
        bf_over = betfair_data.get("Over", 0) or 0
        bf_under = betfair_data.get("Under", 0) or 0
        
        # Collect all edges for over and under
        over_opportunities = []
        under_opportunities = []
        
        for bkey, bk_totals_odds in bookmakers_data.items():
            if bkey not in ACTIVE_BOOKIES:
                continue
            
            # Check Over
            over_odds = bk_totals_odds.get("Over", 0)
            if over_odds and over_odds > 0:
                edge = calculate_edge(over_odds, fair_over)
                fair_prob = 1.0 / fair_over
                
                edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
                prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
                
                if edge_check and prob_check:
                    over_opportunities.append((bkey, over_odds, edge, fair_prob))
            
            # Check Under
            under_odds = bk_totals_odds.get("Under", 0)
            if under_odds and under_odds > 0:
                edge = calculate_edge(under_odds, fair_under)
                fair_prob = 1.0 / fair_under
                
                edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
                prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
                
                if edge_check and prob_check:
                    under_opportunities.append((bkey, under_odds, edge, fair_prob))
        
        # Process Over - log only max edge
        if over_opportunities:
            max_edge = max(opp[2] for opp in over_opportunities)
            max_edge_opps = [opp for opp in over_opportunities if opp[2] == max_edge]
            
            bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
            first_opp = max_edge_opps[0]
            bkey, over_odds, edge, fair_prob = first_opp
            
            # Check filters before logging
            if not ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
                continue
            
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_over, over_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            hit_hash = make_hash(event_id, f"total_{line}", f"Over_{line}", bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Time": commence_time,
                    "sport": sport_key,
                    "event": f"{away_team} @ {home_team}",
                    "market": f"total_{line}",
                    "selection": f"Over_{line}",
                    "bookmaker": bookmakers_str,
                    "Odds": f"{over_odds:.3f}",
                    "Fair": f"{fair_over:.3f}",
                    "EV": f"{edge*100:.2f}%",
                    "prob": f"{fair_prob*100:.1f}%",
                    "Stake": stake_str,
                    "pinnacle": f"{pin_over:.3f}" if pin_over > 0 else "",
                    "betfair": f"{bf_over:.3f}" if bf_over > 0 else "",
                }
                
                # Add bookmaker odds
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        total_odds = bookmakers_data[bk_key].get("Over", 0)
                        if total_odds > 0:
                            ev_row[bk_key] = f"{total_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} Over_{line:5.1f} {over_odds:28.3f} (fair={fair_over:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
        
        # Process Under - log only max edge
        if under_opportunities:
            max_edge = max(opp[2] for opp in under_opportunities)
            max_edge_opps = [opp for opp in under_opportunities if opp[2] == max_edge]
            
            bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
            first_opp = max_edge_opps[0]
            bkey, under_odds, edge, fair_prob = first_opp
            
            # Check filters before logging
            if not ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
                continue
            
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_under, under_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            hit_hash = make_hash(event_id, f"total_{line}", f"Under_{line}", bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Time": commence_time,
                    "sport": sport_key,
                    "event": f"{away_team} @ {home_team}",
                    "market": f"total_{line}",
                    "selection": f"Under_{line}",
                    "bookmaker": bookmakers_str,
                    "Odds": f"{under_odds:.3f}",
                    "Fair": f"{fair_under:.3f}",
                    "EV": f"{edge*100:.2f}%",
                    "prob": f"{fair_prob*100:.1f}%",
                    "Stake": stake_str,
                    "pinnacle": f"{pin_under:.3f}" if pin_under > 0 else "",
                    "betfair": f"{bf_under:.3f}" if bf_under > 0 else "",
                }
                
                # Add bookmaker odds
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        total_odds = bookmakers_data[bk_key].get("Under", 0)
                        if total_odds > 0:
                            ev_row[bk_key] = f"{total_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} Under_{line:5.1f} {under_odds:27.3f} (fair={fair_under:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
    
    return hits


def process_player_props_market(event: Dict, seen: Dict[str, bool], prop_markets: Optional[List[str]] = None) -> int:
    """Process player props markets for an event using max-edge logic."""
    sport_key = event.get("sport_key", "")
    event_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time = event.get("commence_time", "")
    
    if not all([sport_key, event_id, home_team, away_team]):
        return 0
    
    # Default prop markets if none specified
    if prop_markets is None:
        prop_markets = [
            "player_points", "player_rebounds", "player_assists", "player_threes",
            "player_blocks", "player_steals", "player_turnovers",
            "player_points_rebounds_assists", "player_points_assists", 
            "player_points_rebounds", "player_assists_rebounds",
            "player_double_double", "player_first_basket"
        ]
    
    results = process_player_props_event(event, prop_markets)
    
    if not results:
        return 0
    
    hits = 0
    
    for prop in results:
        market_key = prop.get("market", "")
        player_name = prop.get("player", "")
        line = prop.get("line", 0)
        
        # New structure has flat fair prices
        fair_over = prop.get("fair_over", 0)
        fair_under = prop.get("fair_under", 0)
        
        if fair_over <= 0 or fair_under <= 0:
            continue
        
        bookmakers_data = prop.get("bookmakers", {})
        
        # Get Pinnacle for CSV
        pinnacle_data = prop.get("pinnacle", {})
        pin_over = pinnacle_data.get("Over", 0)
        pin_under = pinnacle_data.get("Under", 0)
        
        # Collect all edges for over and under
        over_opportunities = []
        under_opportunities = []
        
        for bkey, bk_prop_odds in bookmakers_data.items():
            if bkey not in ACTIVE_BOOKIES:
                continue
            
            # Check Over
            over_odds = bk_prop_odds.get("Over", 0)
            if over_odds and over_odds > 0:
                edge = calculate_edge(over_odds, fair_over)
                fair_prob = 1.0 / fair_over
                
                # Sanity check: Skip if edge > 100% (API data quality issue - wrong market/line)
                if edge > 1.0:
                    continue
                
                edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
                prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
                
                if edge_check and prob_check:
                    over_opportunities.append((bkey, over_odds, edge, fair_prob))
            
            # Check Under
            under_odds = bk_prop_odds.get("Under", 0)
            if under_odds and under_odds > 0:
                edge = calculate_edge(under_odds, fair_under)
                fair_prob = 1.0 / fair_under
                
                # Sanity check: Skip if edge > 100% (API data quality issue - wrong market/line)
                if edge > 1.0:
                    continue
                
                edge_check = (not ENABLE_EV_FILTER) or (edge >= EV_MIN_EDGE)
                prob_check = (not ENABLE_PROB_FILTER) or (fair_prob >= MIN_PROB)
                
                if edge_check and prob_check:
                    under_opportunities.append((bkey, under_odds, edge, fair_prob))
        
        # Process Over - log only max edge
        if over_opportunities:
            max_edge = max(opp[2] for opp in over_opportunities)
            max_edge_opps = [opp for opp in over_opportunities if opp[2] == max_edge]
            
            bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
            first_opp = max_edge_opps[0]
            bkey, over_odds, edge, fair_prob = first_opp
            
            # Check filters before logging
            if not ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
                continue
            
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_over, over_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            # Market format: player_points_25.5, selection: Player Name Over
            market_display = f"{market_key}_{line}"
            selection_display = f"{player_name} Over"
            
            hit_hash = make_hash(event_id, market_display, selection_display, bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Start Time": format_local_time(commence_time),
                    "Sport": abbreviate_sport(sport_key),
                    "Event": abbreviate_event(away_team, home_team),
                    "Market": abbreviate_market(market_key),
                    "Selection": player_name,
                    "O/U + Y/N": f"Over {line}" if "Over" in selection_display else f"Under {line}",
                    "Book": bookmakers_str,
                    "Price": f"{over_odds:.3f}",
                    "Pinnacle": f"{pin_over:.3f}" if pin_over > 0 else "",
                    "Betfair": "",
                }
                
                # Add bookmaker odds
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        prop_odds = bookmakers_data[bk_key].get("Over", 0)
                        if prop_odds > 0:
                            ev_row[bk_key] = f"{prop_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} {player_name[:20]:20s} O{line:4.1f} {over_odds:.3f} (fair={fair_over:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
        
        # Process Under - log only max edge
        if under_opportunities:
            max_edge = max(opp[2] for opp in under_opportunities)
            max_edge_opps = [opp for opp in under_opportunities if opp[2] == max_edge]
            
            bookmakers_str = ", ".join([opp[0] for opp in max_edge_opps])
            first_opp = max_edge_opps[0]
            bkey, under_odds, edge, fair_prob = first_opp
            
            # Check filters before logging
            if not ((not ENABLE_EV_FILTER or edge >= EV_MIN_EDGE) and (not ENABLE_PROB_FILTER or fair_prob >= MIN_PROB)):
                continue
            
            if edge > 0:
                stake = kelly_stake(BANKROLL, fair_under, under_odds, KELLY_FRACTION)
                stake_rounded = round(stake / 5) * 5
                stake_str = f"${stake_rounded:.0f}"
            else:
                stake_str = ""
            
            market_display = f"{market_key}_{line}"
            selection_display = f"{player_name} Under"
            
            hit_hash = make_hash(event_id, market_display, selection_display, bookmakers_str)
            if hit_hash not in seen:
                seen[hit_hash] = True
                
                ev_row = {
                    "Time": commence_time,
                    "sport": sport_key,
                    "event": f"{away_team} @ {home_team}",
                    "market": market_display,
                    "selection": selection_display,
                    "bookmaker": bookmakers_str,
                    "Odds": f"{under_odds:.3f}",
                    "Fair": f"{fair_under:.3f}",
                    "EV": f"{edge*100:.2f}%",
                    "prob": f"{fair_prob*100:.1f}%",
                    "Stake": stake_str,
                    "pinnacle": f"{pin_under:.3f}" if pin_under > 0 else "",
                    "betfair": "",
                }
                
                # Add bookmaker odds
                for bk_key in CSV_BOOKIES:
                    if bk_key in bookmakers_data:
                        prop_odds = bookmakers_data[bk_key].get("Under", 0)
                        if prop_odds > 0:
                            ev_row[bk_key] = f"{prop_odds:.3f}"
                
                # log_ev_hit(EV_CSV, ev_row)  # Disabled - use filter_ev_hits.py instead
                
                stake_display = stake_str if stake_str else "$0"
                # print(f"[EV] {bookmakers_str:20s} {player_name[:20]:20s} U{line:4.1f} {under_odds:.3f} (fair={fair_under:.3f}, edge={edge*100:.1f}%, stake={stake_display})")
                hits += 1
        
        # --- One-sided/exotic market filter ---
                # If only Over or only Under odds are available, log to exotics_value.csv and skip main EV logging
                has_over = any('Over' in odds and odds['Over'] > 0 for odds in bookmakers_data.values())
                has_under = any('Under' in odds and odds['Under'] > 0 for odds in bookmakers_data.values())
                if not (has_over and has_under):
                    exotics_csv = DATA_DIR / "exotics_value.csv"
                    exotics_row = {
                        "Start Time": format_local_time(commence_time),
                        "Sport": abbreviate_sport(sport_key),
                        "Event": abbreviate_event(away_team, home_team),
                        "Market": abbreviate_market(market_key),
                        "Selection": player_name,
                        "O/U + Y/N": f"Over {line}" if has_over else f"Under {line}",
                        "Book": bookmakers_str,
                        "Price": f"{over_odds if has_over else under_odds:.3f}",
                        "Pinnacle": f"{pin_over if has_over else pin_under:.3f}" if (pin_over > 0 or pin_under > 0) else "",
                        "Betfair": "",
                    }
                    for bk_key in CSV_BOOKIES:
                        if bk_key in bookmakers_data:
                            prop_odds = bookmakers_data[bk_key].get("Over" if has_over else "Under", 0)
                            if prop_odds > 0:
                                exotics_row[bk_key] = f"{prop_odds:.3f}"
                    log_exotic_value(exotics_csv, exotics_row)
                    continue
                # --- End one-sided/exotic market filter ---
    
    return hits


def scan_sport(sport_key: str, seen: Dict[str, bool]) -> Dict[str, int]:
    """Scan one sport for EV opportunities."""
    # Separate main markets from player props
    all_markets = [m.strip() for m in MARKETS.split(",") if m.strip()]
    main_markets = [m for m in all_markets if not m.startswith("player_")]
    
    # Get sport-specific prop markets from config (or fallback to MARKETS if specified)
    user_prop_markets = [m for m in all_markets if m.startswith("player_")]
    if user_prop_markets:
        # User explicitly specified prop markets in .env
        prop_markets = user_prop_markets
    else:
        # Use sport-specific default prop markets from config
        prop_markets = SPORT_PROP_MARKETS.get(sport_key, [])

    # Apply API_TIER policy
    # low: props disabled, regions au only
    # medium: props enabled, regions au,us (default)
    # high: props enabled, regions au,us,eu
    tier = API_TIER
    regions_effective = REGIONS
    props_enabled = True
    if tier == "low":
        regions_effective = "au"
        props_enabled = False
    elif tier == "high":
        regions_effective = "au,us,eu"
        props_enabled = True
    else:
        regions_effective = REGIONS or "au,us"
        props_enabled = True
    
    # Debug: show prop markets being used
    if prop_markets:
        print(f"[DEBUG] Will fetch {len(prop_markets)} prop markets for {sport_key}")
    
    url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": regions_effective,
        "markets": ",".join(main_markets) if main_markets else "h2h",
        "oddsFormat": "decimal",
    }
    
    print(f"\n[API] Fetching {sport_key}: regions={REGIONS}, markets={','.join(main_markets)}")
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        events = resp.json()
    except Exception as e:
        print(f"[!] API error: {e}")
        return {"total": 0, "ev": 0}

    API_USAGE["sports_calls"] += 1
    
    print(f"[scan] Processing {len(events)} events")
    
    # Filter events by time before logging to CSV
    filtered_events = []
    skipped_too_soon = 0
    skipped_too_far = 0
    
    for event in events:
        commence_time = event.get("commence_time")
        if commence_time:
            try:
                commence_dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                now_utc = datetime.now(timezone.utc)
                time_to_start = commence_dt - now_utc
                minutes_to_start = time_to_start.total_seconds() / 60
                # Always skip events starting in less than 1 minute
                if minutes_to_start < 1.0:
                    skipped_too_soon += 1
                    continue
                # Configurable filter for <3min (MIN_TIME_TO_START_MINUTES)
                if MIN_TIME_TO_START_MINUTES > 0 and minutes_to_start < MIN_TIME_TO_START_MINUTES:
                    skipped_too_soon += 1
                    continue
                # Configurable filter for >72hr (MAX_TIME_TO_START_HOURS)
                if MAX_TIME_TO_START_HOURS > 0 and minutes_to_start > MAX_TIME_TO_START_HOURS * 60:
                    skipped_too_far += 1
                    continue
            except Exception:
                pass
        
        # Disk-backed cache & staleness checks
        eid = event.get("id")
        commence_time = event.get("commence_time")
        if eid and commence_time:
            try:
                commence_dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                now_utc = datetime.now(timezone.utc)
                # Skip stale (already started long ago) events beyond window
                if (now_utc - commence_dt).total_seconds() / 3600 > STALE_EVENT_HOURS:
                    API_USAGE["events_skipped_stale"] += 1
                    continue
                last_seen_str = EVENT_CACHE.get(eid)
                if last_seen_str:
                    last_seen_dt = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                    if (now_utc - last_seen_dt).total_seconds() / 60 < REFRESH_EVENT_MINUTES:
                        API_USAGE["events_skipped_cache"] += 1
                        continue
            except Exception:
                pass
        filtered_events.append(event)
    
    if skipped_too_soon > 0 or skipped_too_far > 0:
        print(f"[filter] Skipped {skipped_too_soon} starting <{MIN_TIME_TO_START_MINUTES}min, {skipped_too_far} starting >{MAX_TIME_TO_START_HOURS}hrs")
    print(f"[filter] Processing {len(filtered_events)} events after time filter")
    
    # Log ALL filtered raw odds to all_odds_analysis.csv (with fair prices calculated)
    from core.raw_odds_logger import log_raw_event_odds
    # Cache by event.id + main_markets to avoid duplicate processing within a run
    cache_key_sport = f"{sport_key}|{','.join(main_markets)}"
    cached_event_ids = SESSION_EVENT_CACHE.get(cache_key_sport, set())
    for event in filtered_events:
        eid = event.get("id")
        if eid and eid in cached_event_ids:
            continue
        log_raw_event_odds(event, ALL_ODDS_CSV, list(ACTIVE_BOOKIES), BANKROLL, KELLY_FRACTION, BETFAIR_COMMISSION)
        if eid:
            EVENT_CACHE[eid] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            cached_event_ids.add(eid)
    SESSION_EVENT_CACHE[cache_key_sport] = cached_event_ids
    print(f"[OK] Logged all raw odds with fair prices to {ALL_ODDS_CSV.name}")
    
    ev_hits = 0
    
    for event in filtered_events:
        
        # Process h2h market
        if "h2h" in MARKETS:
            ev_hits += process_h2h_market(event, seen)
        
        # Process spreads market
        if "spreads" in MARKETS:
            ev_hits += process_spreads_market(event, seen)
        
        # Process totals market
        if "totals" in MARKETS:
            ev_hits += process_totals_market(event, seen)
        
        # Process player props (tier-controlled)
        if props_enabled and prop_markets:
            # Need to fetch event with player props separately
            try:
                event_id = event.get("id")
                prop_url = f"{ODDS_API_BASE}/sports/{sport_key}/events/{event_id}/odds"
                # Batch all markets into single API call (already optimized!)
                prop_params = {
                    "apiKey": ODDS_API_KEY,
                    "regions": regions_effective,
                    "markets": ",".join(prop_markets),
                    "oddsFormat": "decimal",
                }
                # Cache props by event.id + prop_markets
                cache_key_props = f"{event_id}|{','.join(prop_markets)}|{regions_effective}"
                if cache_key_props in SESSION_PROPS_CACHE:
                    prop_event = SESSION_PROPS_CACHE[cache_key_props]
                else:
                    resp = requests.get(prop_url, params=prop_params, timeout=30)
                    resp.raise_for_status()
                    prop_event = resp.json()
                    SESSION_PROPS_CACHE[cache_key_props] = prop_event
                    API_USAGE["props_calls"] += 1
                
                # Merge prop data into event
                event_with_props = event.copy()
                event_with_props["bookmakers"] = prop_event.get("bookmakers", [])
                
                # Log player props to all_odds_analysis.csv
                from core.raw_odds_logger import log_raw_event_odds
                log_raw_event_odds(event_with_props, ALL_ODDS_CSV, list(ACTIVE_BOOKIES), BANKROLL, KELLY_FRACTION, BETFAIR_COMMISSION)
                # (Removed all other CSV exports except all_odds_analysis.csv and all_odds.csv)
                
                # Use sport-specific handler for NFL
                if sport_key == "americanfootball_nfl":
                    # prop_hits = process_nfl_props_market(event_with_props, seen, prop_markets)  # Function not defined, skip for now
                    prop_hits = 0
                else:
                    prop_hits = process_player_props_market(event_with_props, seen, prop_markets)
                
                if prop_hits > 0:
                    print(f"[PROPS] Found {prop_hits} prop hits for {event.get('home_team', '')}")
                ev_hits += prop_hits
            except Exception as e:
                print(f"[!] Props API error for {event.get('home_team', '')}: {e}")
                pass
    
    API_USAGE["events_processed"] += len(filtered_events)
    API_USAGE["events_skipped_time"] += (skipped_too_soon + skipped_too_far)
    return {"total": ev_hits, "ev": ev_hits}


def main() -> int:
    """Main entry point."""
    # Pre-run cleanup to enforce two-CSV policy (always purge stale CSVs)
    cleanup_data_directory()
    if not ODDS_API_KEY:
        print("[X] ODDS_API_KEY missing.")
        return 1
    
    seen = load_dedupe()
    sports = [s.strip() for s in SPORTS.split(",") if s.strip()]
    
    print(f"{'='*80}")
    print(f"EV BOT - MODULAR VERSION")
    print(f"{'='*80}")
    print(f"Sports: {', '.join(sports)}")
    print(f"Markets: {MARKETS}")
    print(f"Min Edge: {EV_MIN_EDGE*100:.1f}%")
    print(f"Bankroll: ${BANKROLL:.0f}")
    print(f"Kelly Fraction: {KELLY_FRACTION}")
    print(f"{'='*80}\n")
    
    # Load disk-backed event cache
    load_event_cache()

    total_ev = 0
    
    for sport in sports:
        stats = scan_sport(sport, seen)
        total_ev += stats["ev"]
        time.sleep(0.5)
    
    save_dedupe(seen)
    save_api_usage()
    save_event_cache()
    
    print(f"\n{'='*80}")
    print(f"COMPLETE: All odds logged to {ALL_ODDS_CSV}")
    print(f"Use filter_ev_hits.py to find EV opportunities")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


