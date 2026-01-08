"""
V3 NBA EXTRACTOR - Optimized Bookmaker Selection
Outputs CSV with selected 30 bookmakers (cost-optimized):
  - 8 core columns (event, market, selection)
  - 30 bookmakers (selected from 54 total for cost savings)
  - API Cost: 9 credits/event (25% savings vs 4 regions approach)
"""

import csv
import os
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

# Fix Windows terminal encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import requests
from dotenv import load_dotenv

# Load .env first
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("ODDS_API_KEY", "")
API_HOST = "https://api.the-odds-api.com"

# Get proper data dir
def get_data_dir():
    cwd = Path.cwd()
    data_dir = cwd / "data" / "v3" / "extracts"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

DATA_DIR = get_data_dir()

# ============================================================================
# BOOKMAKER MAPPING - Convert API keys to standardized names
# ============================================================================

BOOKMAKER_MAPPING = {
    # EU / Premium Sharp
    "pinnacle": "pinnacle",
    "betfair_ex_eu": "betfair_ex_eu",
    "betfair_ex_au": "betfair_ex_au",
    "matchbook": "matchbook",
    
    # US - Mainstream
    "draftkings": "draftkings",
    "fanduel": "fanduel",
    "betmgm": "betmgm",
    "draftkings_uk": "draftkings",
    "fanduel_uk": "fanduel",
    
    # US - Secondary
    "betonlineag": "betonlineag",
    "lowvig": "lowvig",
    "bovada": "bovada",
    "mybookieag": "mybookieag",
    "betanysports": "betanysports",
    "betus": "betus",
    "everygame": "everygame",
    "gtbets": "gtbets",
    
    # AU Specific
    "sportsbet": "sportsbet",
    "pointsbetau": "pointsbetau",
    "neds": "neds",
    "tab": "tab",
    "tabtouch": "tabtouch",
    "betr_au": "betr_au",
    "betright": "betright",
    "boombet": "boombet",
    "dabble_au": "dabble_au",
    "ladbrokes_au": "ladbrokes_au",
    "playup": "playup",
    "bet365": "bet365",
    
    # EU - Regional
    "unibet": "unibet",
    "unibet_fr": "unibet_fr",
    "unibet_nl": "unibet_nl",
    "unibet_se": "unibet_se",
    "betsson": "betsson",
    "leovegas_se": "leovegas_se",
    "nordicbet": "nordicbet",
    "williamhill": "williamhill",
    "williamhill_us": "williamhill_us",
    "ballybet": "ballybet",
    "betrivers": "betrivers",
    "espnbet": "espnbet",
    "fanatics": "fanatics",
    
    # EU - Specialized
    "betclic_fr": "betclic_fr",
    "parionssport_fr": "parionssport_fr",
    "winamax_fr": "winamax_fr",
    "winamax_de": "winamax_de",
    "tipico_de": "tipico_de",
    "codere_it": "codere_it",
    
    # Other
    "betparx": "betparx",
    "rebet": "rebet",
    "matchbook": "matchbook",
    "coolbet": "coolbet",
    "fliff": "fliff",
    "hardrockbet": "hardrockbet",
    "onexbet": "onexbet",
    "sport888": "sport888",
}

# Selected 30 Bookmakers (January 3, 2026)
# Updated to use bookmakers parameter instead of regions for cost optimization
# Cost: 30 books = ~3 region equivalents = 9 credits per event (was 12 with 4 regions)
# Savings: 25% reduction in API credits (~33 credits/run saved)
ALL_BOOKMAKERS = [
    # 4⭐ SHARPS - Fair Odds Calculation
    "pinnacle",
    "betfair_ex_eu",
    "matchbook",
    "draftkings",
    "fanduel",
    "lowvig",
    
    # 0⭐ AU TARGETS - EV Surface
    "bet365",
    "betfair_ex_au",
    "sportsbet",
    "dabble_au",
    "pointsbetau",
    "neds",
    "ladbrokes_au",
    "unibet",
    "betright",
    "betr_au",
    "boombet",
    "playup",
    "tab",
    "tabtouch",
    
    # 3⭐ SHARPS - Sharp Coverage Depth
    "betonlineag",
    "betmgm",
    "betrivers",
    "fanatics",
    
    # 2⭐ DECENT - Secondary Market Depth
    "hardrockbet",
    "williamhill_us",
    "bovada",
    "espnbet",
    
    # 1⭐ SOFT - Specialized Books
    "coolbet",
    "fliff",
]


class NBAExtractorV3:
    """NBA Extractor - Standardized V3 Format"""
    
    def __init__(self):
        self.api_key = API_KEY
        self.sport = "basketball_nba"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.credit_start = None
        self.credit_end = None
        self.credit_used = 0
    
    def extract(self) -> pd.DataFrame:
        """Extract NBA odds in standardized V3 format."""
        print(f"\n{'='*60}")
        print(f"EVisionBet V3 - NBA Extraction")
        print(f"{'='*60}")
        
        # Fetch events
        events = self._fetch_events()
        if not events:
            print("❌ No events found")
            return pd.DataFrame()
        
        print(f"✅ Found {len(events)} events")
        
        # Filter events: only process those that haven't started (commence_time > now + 5 min)
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        min_start_time = now + timedelta(minutes=5)
        
        filtered_events = []
        for event in events:
            try:
                commence_str = event.get("commence_time", "")
                if commence_str:
                    # Parse ISO format: 2026-01-07T09:10:00Z
                    commence_dt = datetime.fromisoformat(commence_str.replace('Z', '+00:00'))
                    if commence_dt > min_start_time:
                        filtered_events.append(event)
            except Exception as e:
                # If parsing fails, include event anyway
                filtered_events.append(event)
        
        skipped = len(events) - len(filtered_events)
        if skipped > 0:
            print(f"⏭️  Skipped {skipped} event(s) that already started or start in <5 min")
        
        events = filtered_events
        
        if not events:
            print("❌ No upcoming events (all started or starting in <5 min)")
            return pd.DataFrame()
        
        # Process each event
        rows = []
        for event in events:
            event_rows = self._process_event(event)
            rows.extend(event_rows)
        
        if not rows:
            print("❌ No odds extracted")
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        
        # Ensure all bookmaker columns exist
        for book in ALL_BOOKMAKERS:
            if book not in df.columns:
                df[book] = ""
        
        # Reorder columns: core first, then bookmakers
        core_cols = ["event_id", "extracted_at", "commence_time", "league", "event_name", "market_type", "point", "selection", "player_name"]
        df = df[core_cols + ALL_BOOKMAKERS]
        
        print(f"✅ Extracted {len(df)} odds rows")
        return df
    
    def _fetch_events(self) -> List[Dict]:
        """Fetch events from The Odds API."""
        url = f"{API_HOST}/v4/sports/{self.sport}/events"
        params = {
            "apiKey": self.api_key,
            "regions": "au,us,us2,eu",
        }
        
        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            
            # Capture credit info on first request
            if self.credit_start is None:
                remaining = resp.headers.get('x-requests-remaining')
                used = resp.headers.get('x-requests-used')
                if remaining:
                    self.credit_start = int(float(remaining))
            
            data = resp.json()
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []
    
    def _process_event(self, event: Dict) -> List[Dict]:
        """Process single event and extract odds."""
        event_id = event.get("id")
        away = event.get("away_team", "")
        home = event.get("home_team", "")
        commence = event.get("commence_time", "")
        
        # Format event name
        event_name = f"{away} @ {home}"
        
        # Fetch odds
        odds_resp = self._fetch_odds(event_id)
        if not odds_resp:
            return []
        
        bookmakers = odds_resp.get("bookmakers", [])
        
        # First pass: collect all raw outcomes with their frequencies
        raw_data = {}  # (market_type, selection) -> {point -> count, prices}
        for bm in bookmakers:
            book_key = bm.get("key")
            if book_key not in BOOKMAKER_MAPPING:
                continue
            
            book_name = BOOKMAKER_MAPPING[book_key]
            
            for market in bm.get("markets", []):
                market_type = market.get("key")
                # Accept all market types (spreads, totals, player props, period markets, etc.)
                
                for outcome in market.get("outcomes", []):
                    selection = outcome.get("name", "")  # Over/Under for regular, player name for props
                    description = outcome.get("description", "")  # Player name for player props, team name for team_totals
                    point = outcome.get("point")
                    price = outcome.get("price")
                    
                    # Determine player_name based on market type
                    # Player props: use description as player identifier
                    # Other markets: empty
                    player_name = ""
                    
                    if market_type.startswith("player_"):
                        player_name = description  # Player name for player props
                    
                    # Create a unique key based on market type and identifier
                    if player_name:
                        # Player/Team props: key includes identifier (player or team name)
                        key = (market_type, player_name, selection)
                    else:
                        # Regular markets: key is market type and selection (e.g., "spreads", "Under")
                        key = (market_type, selection, None)
                    
                    if key not in raw_data:
                        raw_data[key] = {"points": {}, "prices": {}}
                    
                    # Track point frequency
                    if pd.notna(point):
                        p = float(point)
                        if p not in raw_data[key]["points"]:
                            raw_data[key]["points"][p] = 0
                        raw_data[key]["points"][p] += 1
                    
                    # Store prices for each point variant
                    if price:
                        if point not in raw_data[key]["prices"]:
                            raw_data[key]["prices"][point] = {}
                        raw_data[key]["prices"][point][book_name] = price
        
        # Second pass: PRESERVE ALL POINT VARIATIONS - no consolidation
        # Each unique (market_type, selection, point) = separate row
        rows = []
        for key, data in raw_data.items():
            # Unpack key based on whether it's a player prop
            if len(key) == 3 and key[2] is not None:
                # Player prop: (market_type, player_name, selection)
                market_type, identifier, selection = key
                player_name = identifier
            elif len(key) == 3 and key[2] is None:
                # Regular market: (market_type, selection, None)
                market_type, selection, _ = key
                player_name = ""
            else:
                # Fallback
                market_type, selection = key[0], key[1]
                player_name = ""
            
            # Create a row for EACH unique point value
            for point, books_with_this_point in data["prices"].items():
                row = {
                    "event_id": event_id,
                    "extracted_at": self.timestamp,
                    "commence_time": self._format_time(commence),
                    "league": "NBA",
                    "event_name": event_name,
                    "market_type": market_type,
                    "point": str(point) if point else "",
                    "selection": selection,
                    "player_name": player_name,
                }
                
                # Add all bookmaker prices for THIS specific point
                for book_name, price in books_with_this_point.items():
                    row[book_name] = price
                
                rows.append(row)
        
        return rows
    
    def _fetch_odds(self, event_id: str) -> Dict:
        """Fetch odds for single event using bookmakers parameter for cost optimization."""
        url = f"{API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"
        
        # Core NBA markets (main game only, no period breakdowns)
        all_markets = (
            # Main full-game markets (8)
            "h2h,spreads,totals,alternate_spreads,alternate_totals,"
            "player_points,player_assists,player_rebounds,"
            # Player props - main (8)
            "player_blocks,player_steals,player_threes,player_double_double,"
            "player_triple_double,player_turnovers,"
            "player_blocks_alternate,player_steals_alternate,"
            # Player props - alternate (5)
            "player_points_alternate,player_assists_alternate,player_rebounds_alternate,"
            "player_threes_alternate,player_double_double_alternate,"
            # Player prop combos (8)
            "player_points_assists,player_points_rebounds,player_rebounds_assists,"
            "player_points_rebounds_assists,"
            "player_points_assists_alternate,player_points_rebounds_alternate,"
            "player_rebounds_assists_alternate,player_points_rebounds_assists_alternate,"
            # Niche full-game markets (1)
            "odd_even,"
            # Other special markets (3)
            "player_first_basket,player_first_team_basket,player_method_of_first_basket,"
            "first_team_to_score,last_team_to_score,"
            # Rare props (5)
            "player_twos,player_twos_alternate,player_twos_attempts,player_threes_attempts_alternate,"
            # Draw/Exchange (2)
            "draw_no_bet_h1,h2h_lay"
        )
        
        params = {
            "apiKey": self.api_key,
            "bookmakers": ",".join(ALL_BOOKMAKERS),
            "markets": all_markets,
            "oddsFormat": "decimal",
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            # Capture credit info on last request
            remaining = resp.headers.get('x-requests-remaining')
            last_cost = resp.headers.get('x-requests-last')
            if remaining:
                self.credit_end = int(float(remaining))
            
            data = resp.json()
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"⚠️  Error fetching odds for {event_id}: {e}")
            return {}
    
    def _format_time(self, iso_time: str) -> str:
        """Format ISO time to readable format (converted to local timezone - Perth)."""
        try:
            # Parse ISO time (UTC from API)
            dt = pd.to_datetime(iso_time)
            
            # Localize as UTC if not already aware
            if dt.tz is None:
                dt = dt.tz_localize('UTC')
            
            # Convert to local timezone (Perth/Western Australia)
            dt_local = dt.tz_convert('Australia/Perth')
            
            return dt_local.strftime("%I:%M%p %d/%m/%y").lower()
        except Exception as e:
            print(f"Error formatting time '{iso_time}': {e}")
            return iso_time
    def _normalize_point(self, point) -> str:
        """Normalize point to .5 format - keep as-is since API already provides correct format."""
        if pd.isna(point):
            return ""
        
        # Return point as-is since The Odds API already provides proper .5 format
        # Don't normalize/round - just use what the API gives
        return str(float(point))
    
    def save(self, df: pd.DataFrame, filename: str = None) -> Path:
        """Save to CSV - overwrites previous file."""
        if df.empty:
            print("❌ No data to save")
            return None
        
        if filename is None:
            filename = "basketball_nba_raw.csv"
        
        output_path = DATA_DIR / filename
        
        # Try direct write with pandas, ignore if file is locked
        try:
            df.to_csv(output_path, index=False)
        except PermissionError:
            # File is locked (backend API reading it), save to alternate name
            # This is okay - backend will use the latest available file
            alt_path = DATA_DIR / f"{filename[:-4]}_new.csv"
            df.to_csv(alt_path, index=False)
            print(f"⚠️  Main file locked by backend, saved to: {alt_path}")
            return alt_path
        
        print(f"✅ Saved: {output_path}")
        return output_path


def main():
    extractor = NBAExtractorV3()
    df = extractor.extract()
    if not df.empty:
        extractor.save(df)
        
        # Show credit usage
        if extractor.credit_start and extractor.credit_end:
            credits_used = extractor.credit_start - extractor.credit_end
            print(f"\n{'='*60}")
            print(f"💳 API CREDIT USAGE")
            print(f"{'='*60}")
            print(f"Credits before extraction: {extractor.credit_start:,}")
            print(f"Credits after extraction:  {extractor.credit_end:,}")
            print(f"Credits used this run:     {credits_used:,}")
            print(f"{'='*60}\n")
    else:
        print("❌ Extraction failed")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
