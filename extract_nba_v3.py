"""
V3 NBA EXTRACTOR - Standardized Format
Outputs CSV matching your preferred structure:
  - 8 core columns (event, market, selection)
  - 53 bookmakers (comprehensive)
"""

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

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

# All 53 bookmakers in order
ALL_BOOKMAKERS = [
    "betfair_ex_eu",
    "draftkings",
    "fanduel",
    "pinnacle",
    "betonlineag",
    "lowvig",
    "betfair_ex_au",
    "betr_au",
    "betright",
    "boombet",
    "dabble_au",
    "ladbrokes_au",
    "neds",
    "playup",
    "pointsbetau",
    "sportsbet",
    "tab",
    "tabtouch",
    "unibet",
    "ballybet",
    "betanysports",
    "betclic_fr",
    "betmgm",
    "betparx",
    "betrivers",
    "betsson",
    "betus",
    "bovada",
    "codere_it",
    "coolbet",
    "espnbet",
    "everygame",
    "fanatics",
    "fliff",
    "gtbets",
    "hardrockbet",
    "leovegas_se",
    "marathonbet",
    "matchbook",
    "mybookieag",
    "nordicbet",
    "onexbet",
    "parionssport_fr",
    "rebet",
    "sport888",
    "tipico_de",
    "unibet_fr",
    "unibet_nl",
    "unibet_se",
    "williamhill",
    "williamhill_us",
    "winamax_de",
    "winamax_fr",
]


class NBAExtractorV3:
    """NBA Extractor - Standardized V3 Format"""
    
    def __init__(self):
        self.api_key = API_KEY
        self.sport = "basketball_nba"
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
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
        core_cols = ["event_id", "extracted_at", "commence_time", "league", "event_name", "market_type", "point", "selection"]
        df = df[core_cols + ALL_BOOKMAKERS]
        
        print(f"✅ Extracted {len(df)} odds rows")
        return df
    
    def _fetch_events(self) -> List[Dict]:
        """Fetch events from The Odds API."""
        url = f"{API_HOST}/v4/sports/{self.sport}/events"
        params = {
            "apiKey": self.api_key,
            "regions": "au,us,eu",
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
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
        rows = []
        markets_data = {}  # Aggregate by market + selection
        
        for bm in bookmakers:
            book_key = bm.get("key")
            if book_key not in BOOKMAKER_MAPPING:
                continue
            
            book_name = BOOKMAKER_MAPPING[book_key]
            
            for market in bm.get("markets", []):
                market_type = market.get("key")
                if market_type not in ["h2h", "spreads", "totals", "h2h_lay"]:
                    continue
                
                for outcome in market.get("outcomes", []):
                    selection = outcome.get("name", "")
                    point = outcome.get("point")
                    price = outcome.get("price")
                    
                    # Create key for this market/selection combo
                    key = (market_type, selection, point)
                    
                    if key not in markets_data:
                        markets_data[key] = {
                            "event_id": event_id,
                            "extracted_at": self.timestamp,
                            "commence_time": self._format_time(commence),
                            "league": "NBA",
                            "event_name": event_name,
                            "market_type": market_type,
                            "point": point if pd.notna(point) else "",
                            "selection": selection,
                        }
                    
                    # Add bookmaker price
                    if price:
                        markets_data[key][book_name] = price
        
        # Convert to rows
        for market_data in markets_data.values():
            rows.append(market_data)
        
        return rows
    
    def _fetch_odds(self, event_id: str) -> Dict:
        """Fetch odds for single event."""
        url = f"{API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": "au,us,eu",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal",
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"⚠️  Error fetching odds for {event_id}: {e}")
            return {}
    
    def _format_time(self, iso_time: str) -> str:
        """Format ISO time to readable format."""
        try:
            dt = pd.to_datetime(iso_time)
            return dt.strftime("%I:%M%p %d/%m/%y").lower()
        except:
            return iso_time
    
    def save(self, df: pd.DataFrame, filename: str = None) -> Path:
        """Save to CSV."""
        if df.empty:
            print("❌ No data to save")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"basketball_nba_raw_{timestamp}.csv"
        
        output_path = DATA_DIR / filename
        df.to_csv(output_path, index=False)
        print(f"✅ Saved: {output_path}")
        return output_path


def main():
    extractor = NBAExtractorV3()
    df = extractor.extract()
    if not df.empty:
        extractor.save(df)
    else:
        print("❌ Extraction failed")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
