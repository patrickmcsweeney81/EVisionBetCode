"""
V3 NBL EXTRACTOR - Optimized Bookmaker Selection
Outputs CSV with selected 30 bookmakers (cost-optimized):
  - 8 core columns (event, market, selection)
  - 30 bookmakers (selected from 54 total for cost savings)

Notes:
- NBL market coverage varies by bookmaker/sport.
- This extractor requests core markets that are consistently available:
  h2h, spreads, totals, alternate_spreads, alternate_totals, h2h_lay
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

# Fix Windows terminal encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import requests
from dotenv import load_dotenv

from bookmaker_ratings import FINAL_COLUMN_ORDER

# Load .env first
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("ODDS_API_KEY", "")
API_HOST = "https://api.the-odds-api.com"


def get_data_dir() -> Path:
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
    "marathonbet": "marathonbet",
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
    "coolbet": "coolbet",
    "fliff": "fliff",
    "hardrockbet": "hardrockbet",
    "onexbet": "onexbet",
    "sport888": "sport888",
}

# Cost-optimized request list (30 books)
REQUESTED_BOOKMAKERS = [
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

# Output column order (LOCKED 54-book order + ensure requested books included)
OUTPUT_BOOKMAKERS = list(dict.fromkeys(list(FINAL_COLUMN_ORDER) + list(REQUESTED_BOOKMAKERS)))

# Backwards-compat alias (this file historically used ALL_BOOKMAKERS)
ALL_BOOKMAKERS = REQUESTED_BOOKMAKERS


class NBLExtractorV3:
    """NBL Extractor - Standardized V3 Format"""

    def __init__(self):
        self.api_key = API_KEY
        self.sport = "basketball_nbl"
        self.timestamp = datetime.now().isoformat()
        self.credit_start = None
        self.credit_end = None
        self.odds_mode = os.getenv("NBL_ODDS_MODE", "bookmakers").lower().strip()

    def extract(self) -> pd.DataFrame:
        print(f"\n{'='*60}")
        print("EVisionBet V3 - NBL Extraction")
        print(f"{'='*60}")

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
                    commence_dt = datetime.fromisoformat(
                        commence_str.replace("Z", "+00:00")
                    )
                    if commence_dt > min_start_time:
                        filtered_events.append(event)
            except Exception:
                filtered_events.append(event)

        skipped = len(events) - len(filtered_events)
        if skipped > 0:
            print(f"⏭️  Skipped {skipped} event(s) that already started or start in <5 min")

        events = filtered_events
        if not events:
            print("❌ No upcoming events (all started or starting in <5 min)")
            return pd.DataFrame()

        rows: List[Dict] = []
        for event in events:
            rows.extend(self._process_event(event))

        if not rows:
            print("❌ No odds extracted")
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        for book in OUTPUT_BOOKMAKERS:
            if book not in df.columns:
                df[book] = ""

        df["pair_id"] = None

        core_cols = [
            "event_id",
            "extracted_at",
            "commence_time",
            "league",
            "event_name",
            "market_type",
            "point",
            "selection",
            "player_name",
            "pair_id",
        ]
        if self.odds_mode == "regions":
            book_cols = [c for c in df.columns if c not in set(core_cols)]
            locked_first = [b for b in OUTPUT_BOOKMAKERS if b in book_cols]
            extras = sorted([b for b in book_cols if b not in set(locked_first)])
            df = df[core_cols + locked_first + extras]
        else:
            df = df[core_cols + OUTPUT_BOOKMAKERS]

        print(f"✅ Extracted {len(df)} odds rows")
        return df

    def _fetch_events(self) -> List[Dict]:
        url = f"{API_HOST}/v4/sports/{self.sport}/events"
        params = {
            "apiKey": self.api_key,
            "regions": "au,us,us2,eu",
        }

        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()

            if self.credit_start is None:
                remaining = resp.headers.get("x-requests-remaining")
                if remaining:
                    self.credit_start = int(float(remaining))

            data = resp.json()
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []

    def _process_event(self, event: Dict) -> List[Dict]:
        event_id = event.get("id")
        away = event.get("away_team", "")
        home = event.get("home_team", "")
        commence = event.get("commence_time", "")

        event_name = f"{away} @ {home}"

        odds_resp = self._fetch_odds(str(event_id) if event_id is not None else "")
        if not odds_resp:
            return []

        bookmakers = odds_resp.get("bookmakers", [])

        raw_data: Dict = {}
        for bm in bookmakers:
            book_key = bm.get("key")
            if book_key in BOOKMAKER_MAPPING:
                book_name = BOOKMAKER_MAPPING[book_key]
            elif self.odds_mode == "regions" and book_key:
                book_name = str(book_key)
            else:
                continue

            for market in bm.get("markets", []):
                market_type = market.get("key")

                for outcome in market.get("outcomes", []):
                    selection = outcome.get("name", "")
                    description = outcome.get("description", "")
                    point = outcome.get("point")
                    price = outcome.get("price")

                    player_name = ""
                    if market_type.startswith("player_"):
                        player_name = description

                    if player_name:
                        key = (market_type, player_name, selection)
                    else:
                        key = (market_type, selection, None)

                    if key not in raw_data:
                        raw_data[key] = {"prices": {}}

                    if price:
                        if point not in raw_data[key]["prices"]:
                            raw_data[key]["prices"][point] = {}
                        raw_data[key]["prices"][point][book_name] = price

        rows: List[Dict] = []
        for key, data in raw_data.items():
            if len(key) == 3 and key[2] is not None:
                market_type, identifier, selection = key
                player_name = identifier
            elif len(key) == 3 and key[2] is None:
                market_type, selection, _ = key
                player_name = ""
            else:
                market_type, selection = key[0], key[1]
                player_name = ""

            for point, books_with_this_point in data["prices"].items():
                row = {
                    "event_id": event_id,
                    "extracted_at": self.timestamp,
                    "commence_time": self._format_time(commence),
                    "league": "NBL",
                    "event_name": event_name,
                    "market_type": market_type,
                    "point": str(point) if point else "",
                    "selection": selection,
                    "player_name": player_name,
                }

                for book_name, price in books_with_this_point.items():
                    row[book_name] = price

                rows.append(row)

        return rows

    def _fetch_odds(self, event_id: str) -> Dict:
        url = f"{API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"

        core_markets = "h2h,spreads,totals,alternate_spreads,alternate_totals,h2h_lay"

        params = {
            "apiKey": self.api_key,
            "markets": core_markets,
            "oddsFormat": "decimal",
        }

        if self.odds_mode == "regions":
            params["regions"] = "au,us,us2,eu"
        else:
            params["bookmakers"] = ",".join(REQUESTED_BOOKMAKERS)

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()

            remaining = resp.headers.get("x-requests-remaining")
            if remaining:
                self.credit_end = int(float(remaining))

            data = resp.json()
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"⚠️  Error fetching odds for {event_id}: {e}")
            return {}

    def _format_time(self, iso_time: str) -> str:
        try:
            dt = pd.to_datetime(iso_time)
            if dt.tz is None:
                dt = dt.tz_localize("UTC")
            dt_local = dt.tz_convert("Australia/Perth")
            return dt_local.strftime("%I:%M%p %d/%m/%y").lower()
        except Exception as e:
            print(f"Error formatting time '{iso_time}': {e}")
            return iso_time

    def save(self, df: pd.DataFrame, filename: str | None = None) -> Path | None:
        if df.empty:
            print("❌ No data to save")
            return None

        if filename is None:
            filename = "NBL_Raw.csv"

        output_path = DATA_DIR / filename

        try:
            df.to_csv(output_path, index=False)
        except PermissionError:
            alt_path = DATA_DIR / f"{filename[:-4]}_new.csv"
            df.to_csv(alt_path, index=False)
            print(f"⚠️  Main file locked by backend, saved to: {alt_path}")
            return alt_path

        print(f"✅ Saved: {output_path}")
        return output_path


def main():
    extractor = NBLExtractorV3()
    df = extractor.extract()
    if not df.empty:
        extractor.save(df)

        if extractor.credit_start and extractor.credit_end:
            credits_used = extractor.credit_start - extractor.credit_end
            print(f"\n{'='*60}")
            print("💳 API CREDIT USAGE")
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
