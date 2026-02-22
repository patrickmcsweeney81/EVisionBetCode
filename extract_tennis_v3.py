"""V3 TENNIS EXTRACTOR - Standardized V3 Format

Tennis sport keys can be tournament-specific (e.g. `tennis_atp_qatar_open`).
Use `check_odds_api_sports.py` to see what's currently available.

Usage:
    C:/EVisionWorkspace/EVisionBetCode/.venv/Scripts/python.exe \
        extract_tennis_v3.py --sport tennis_atp_qatar_open

Or set environment variable:
  TENNIS_SPORT_KEY=tennis_atp_qatar_open
"""

from __future__ import annotations

import argparse
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
    if hasattr(sys.stdout, "reconfigure"):
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
OUTPUT_BOOKMAKERS = list(
    dict.fromkeys(list(FINAL_COLUMN_ORDER) + list(REQUESTED_BOOKMAKERS))
)

# Backwards-compat alias (this file historically used ALL_BOOKMAKERS)
ALL_BOOKMAKERS = REQUESTED_BOOKMAKERS


class TennisExtractorV3:
    def __init__(self, sport_key: str):
        self.api_key = API_KEY
        self.sport = sport_key
        self.timestamp = datetime.now().isoformat()
        self.credit_start: int | None = None
        self.credit_end: int | None = None
        self._debug_printed = False
        self.odds_mode = (
            os.getenv("TENNIS_ODDS_MODE", "bookmakers").lower().strip()
        )

    def extract(self) -> pd.DataFrame:
        print(f"\n{'='*60}")
        print(f"EVisionBet V3 - Tennis Extraction ({self.sport})")
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
                f"⏭️  Skipped {skipped} event(s) that already started "
                "or start in <5 min"
            )

        events = filtered_events
        if not events:
            print("❌ No upcoming events (all started or starting in <5 min)")
            return pd.DataFrame()

        if os.getenv("DEBUG_ONE_EVENT", "false").lower() == "true":
            events = events[:1]
            print("🐛 DEBUG_ONE_EVENT=true -> processing only 1 event")

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
        commence = event.get("commence_time", "")

        # Tennis events often include player names directly.
        home = event.get("home_team", "")
        away = event.get("away_team", "")
        event_name = (
            f"{away} @ {home}" if away and home else str(event.get("name", ""))
        )

        event_id_str = str(event_id) if event_id is not None else ""
        odds_resp = self._fetch_odds(event_id_str)
        if not odds_resp:
            return []

        # Debug: print which bookmakers + markets were returned by the API.
        debug_books = os.getenv("DEBUG_BOOKMAKERS", "false").lower() == "true"
        if debug_books and not self._debug_printed:
            self._debug_printed = True
            bms = odds_resp.get("bookmakers", []) or []
            market_union: set[str] = set()
            print(f"\n🐛 DEBUG: returned bookmakers: {len(bms)}")
            for bm in bms:
                bm_key = bm.get("key")
                market_keys = sorted(
                    {
                        m.get("key")
                        for m in (bm.get("markets", []) or [])
                        if m.get("key")
                    }
                )
                market_union.update(market_keys)
                print(f"- {bm_key}: markets={market_keys}")
            print(
                f"\n🐛 DEBUG: union of markets returned ({len(market_union)}):"
            )
            print(sorted(market_union))

            if os.getenv("PROBE_MARKETS", "false").lower() == "true":
                print(
                    "\n🐛 PROBE_MARKETS=true -> probing candidate "
                    "tennis markets"
                )
                self._probe_markets(event_id_str)

        rows: List[Dict] = []
        bookmakers = odds_resp.get("bookmakers", [])
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
                    point = outcome.get("point")
                    price = outcome.get("price")

                    row = {
                        "event_id": event_id,
                        "extracted_at": self.timestamp,
                        "commence_time": self._format_time(commence),
                        "league": "TENNIS",
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

        primary_markets = os.getenv("TENNIS_MARKETS", "h2h,spreads,totals")
        fallback_markets = "h2h"

        params = {
            "apiKey": self.api_key,
            "markets": primary_markets,
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
            print(
                f"⚠️  Error fetching odds for {event_id} "
                f"with primary markets: {e}"
            )
            try:
                fallback_params = params.copy()
                fallback_params["markets"] = fallback_markets
                if self.odds_mode == "regions":
                    fallback_params.pop("bookmakers", None)
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

    def _probe_markets(self, event_id: str) -> None:
        """Probe a set of candidate tennis markets and print which return data.

        Note: The Odds API only returns markets you request.
        """

        candidates_env = os.getenv(
            "TENNIS_MARKET_PROBE_LIST",
            "h2h,spreads,totals,h2h_lay,alternate_spreads,alternate_totals,"
            "h2h_1st_set,spreads_1st_set,totals_1st_set,"
            "h2h_2nd_set,spreads_2nd_set,totals_2nd_set,"
            "h2h_3rd_set,spreads_3rd_set,totals_3rd_set",
        )
        candidates = [
            c.strip() for c in candidates_env.split(",") if c.strip()
        ]

        url = f"{API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"

        supported: list[str] = []
        for market in candidates:
            params = {
                "apiKey": self.api_key,
                "markets": market,
                "oddsFormat": "decimal",
            }
            if self.odds_mode == "regions":
                params["regions"] = "au,us,us2,eu"
            else:
                params["bookmakers"] = ",".join(REQUESTED_BOOKMAKERS)

            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json() if isinstance(resp.json(), dict) else {}
                bms = data.get("bookmakers", []) or []
                # Supported if at least one bookmaker returns it.
                any_market = False
                for bm in bms:
                    keys = {
                        m.get("key") for m in (bm.get("markets", []) or [])
                    }
                    if market in keys:
                        any_market = True
                        break
                if any_market:
                    supported.append(market)
                    print(f"  ✅ {market}")
                else:
                    print(f"  ❌ {market}")
            except Exception as e:
                print(f"  ⚠️  {market}: error ({e})")

        print(f"\n🐛 PROBE RESULT: supported markets ({len(supported)}):")
        print(supported)

    def _format_time(self, iso_time: str) -> str:
        try:
            dt = pd.to_datetime(iso_time)
            if dt.tz is None:
                dt = dt.tz_localize("UTC")
            dt_local = dt.tz_convert("Australia/Perth")
            return str(dt_local.strftime("%I:%M%p %d/%m/%y").lower())
        except Exception:
            return str(iso_time)

    def save(
        self, df: pd.DataFrame, filename: str | None = None
    ) -> Path | None:
        if df.empty:
            print("❌ No data to save")
            return None

        if filename is None:
            safe_key = self.sport.replace("/", "_")
            filename = f"{safe_key}_Raw.csv"

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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sport",
        default=os.getenv("TENNIS_SPORT_KEY", ""),
        help="Tennis sport key (e.g. tennis_atp_qatar_open)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if not args.sport:
        print(
            "ERROR: missing --sport. Run check_odds_api_sports.py "
            "to see current tennis keys."
        )
        raise SystemExit(2)

    extractor = TennisExtractorV3(args.sport)
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
