"""V3 SOCCER (EPL) EXTRACTOR - Standardized V3 Format

- Uses the shared 30 bookmaker set (cost-optimized)
- Writes a standardized CSV into data/v3/extracts/

Notes
- Soccer `h2h` is often 3-way (Home/Away/Draw). This extractor defaults to
  2-way markets only (spreads/totals + alternates) to keep downstream EV
  calculation compatible.
- Enable `h2h` explicitly by setting INCLUDE_SOCCER_H2H=true.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

from bookmaker_ratings import FINAL_COLUMN_ORDER


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

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


BOOKMAKER_MAPPING = {
    "pinnacle": "pinnacle",
    "betfair_ex_eu": "betfair_ex_eu",
    "betfair_ex_au": "betfair_ex_au",
    "matchbook": "matchbook",
    "draftkings": "draftkings",
    "fanduel": "fanduel",
    "betmgm": "betmgm",
    "draftkings_uk": "draftkings",
    "fanduel_uk": "fanduel",
    "betonlineag": "betonlineag",
    "lowvig": "lowvig",
    "bovada": "bovada",
    "mybookieag": "mybookieag",
    "betanysports": "betanysports",
    "betus": "betus",
    "everygame": "everygame",
    "gtbets": "gtbets",
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
    "betclic_fr": "betclic_fr",
    "parionssport_fr": "parionssport_fr",
    "winamax_fr": "winamax_fr",
    "winamax_de": "winamax_de",
    "tipico_de": "tipico_de",
    "codere_it": "codere_it",
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
    "pinnacle",
    "betfair_ex_eu",
    "matchbook",
    "draftkings",
    "fanduel",
    "lowvig",
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
    "betonlineag",
    "betmgm",
    "betrivers",
    "fanatics",
    "hardrockbet",
    "williamhill_us",
    "bovada",
    "espnbet",
    "coolbet",
    "fliff",
]

# Output column order (LOCKED 54-book order + ensure requested books included)
OUTPUT_BOOKMAKERS = list(dict.fromkeys(list(FINAL_COLUMN_ORDER) + list(REQUESTED_BOOKMAKERS)))

# Backwards-compat alias (this file historically used ALL_BOOKMAKERS)
ALL_BOOKMAKERS = REQUESTED_BOOKMAKERS


class SoccerEPLExtractorV3:
    def __init__(self):
        self.api_key = API_KEY
        self.sport = "soccer_epl"
        self.timestamp = datetime.now().isoformat()
        self.credit_start: int | None = None
        self.credit_end: int | None = None

    def extract(self) -> pd.DataFrame:
        print(f"\n{'='*60}")
        print("EVisionBet V3 - Soccer EPL Extraction")
        print(f"{'='*60}")

        events = self._fetch_events()
        if not events:
            print("❌ No events found")
            return pd.DataFrame()

        print(f"✅ Found {len(events)} events")

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
            print(
                f"⏭️  Skipped {skipped} event(s) that already started or start in <5 min"
            )

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
        df = df[core_cols + OUTPUT_BOOKMAKERS]

        print(f"✅ Extracted {len(df)} odds rows")
        return df

    def _fetch_events(self) -> List[Dict]:
        url = f"{API_HOST}/v4/sports/{self.sport}/events"
        params = {"apiKey": self.api_key, "regions": "au,us,us2,eu"}
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
        event_name = f"{away} @ {home}" if away and home else str(event.get("name", ""))

        event_id_str = str(event_id) if event_id is not None else ""
        odds_resp = self._fetch_odds(event_id_str)
        if not odds_resp:
            return []

        rows: List[Dict] = []
        bookmakers = odds_resp.get("bookmakers", [])
        for bm in bookmakers:
            book_key = bm.get("key")
            if book_key not in BOOKMAKER_MAPPING:
                continue
            book_name = BOOKMAKER_MAPPING[book_key]

            for market in bm.get("markets", []):
                market_type = market.get("key")
                for outcome in market.get("outcomes", []):
                    selection = outcome.get("name", "")
                    point = outcome.get("point")
                    price = outcome.get("price")

                    row = {
                        "event_id": event_id,
                        "extracted_at": self.timestamp,
                        "commence_time": self._format_time(commence),
                        "league": "EPL",
                        "event_name": event_name,
                        "market_type": market_type,
                        "point": str(point) if point is not None else "",
                        "selection": selection,
                        "player_name": "",
                    }
                    row[book_name] = price
                    rows.append(row)

        return rows

    def _fetch_odds(self, event_id: str) -> Dict:
        url = f"{API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"

        include_h2h = os.getenv("INCLUDE_SOCCER_H2H", "false").lower() == "true"

        # Default to two-way markets only.
        base_markets = "spreads,totals,alternate_spreads,alternate_totals"
        markets = base_markets + (",h2h" if include_h2h else "")
        fallback_markets = "spreads,totals"

        params = {
            "apiKey": self.api_key,
            "bookmakers": ",".join(REQUESTED_BOOKMAKERS),
            "markets": markets,
            "oddsFormat": "decimal",
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            remaining = resp.headers.get("x-requests-remaining")
            if remaining:
                self.credit_end = int(float(remaining))
            data = resp.json()
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(
                f"⚠️  Error fetching odds for {event_id} with primary markets: {e}"
            )
            try:
                fallback_params = params.copy()
                fallback_params["markets"] = fallback_markets
                resp = requests.get(url, params=fallback_params, timeout=20)
                resp.raise_for_status()
                remaining = resp.headers.get("x-requests-remaining")
                if remaining:
                    self.credit_end = int(float(remaining))
                data = resp.json()
                return data if isinstance(data, dict) else {}
            except Exception as e2:
                print(f"❌ Fallback odds fetch failed for {event_id}: {e2}")
                return {}

    def _format_time(self, iso_time: str) -> str:
        try:
            dt = pd.to_datetime(iso_time)
            if dt.tz is None:
                dt = dt.tz_localize("UTC")
            dt_local = dt.tz_convert("Australia/Perth")
            return str(dt_local.strftime("%I:%M%p %d/%m/%y").lower())
        except Exception:
            return str(iso_time)

    def save(self, df: pd.DataFrame, filename: str | None = None) -> Path | None:
        if df.empty:
            print("❌ No data to save")
            return None

        if filename is None:
            filename = "EPL_Raw.csv"

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


def main() -> None:
    extractor = SoccerEPLExtractorV3()
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
