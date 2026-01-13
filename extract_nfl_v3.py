"""
V3 NFL EXTRACTOR - 30 Bookmakers (mirrors NBA V3 pattern)
Outputs CSV with standardized columns for backend consumption.
- Preserves every unique (market_type, selection, point) row (no consolidation)
- Uses same 30-book cost-optimized set as NBA V3
- Adds pair_id placeholder for downstream pairing
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

# Fix Windows terminal encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Load .env first
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("ODDS_API_KEY", "")
API_HOST = "https://api.the-odds-api.com"


def get_data_dir() -> Path:
    """Return data directory (created if missing)."""
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
    "coolbet": "coolbet",
    "fliff": "fliff",
    "hardrockbet": "hardrockbet",
    "onexbet": "onexbet",
    "sport888": "sport888",
}

# Selected 30 Bookmakers (same set as NBA V3)
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


class NFLExtractorV3:
    """NFL Extractor - Standardized V3 Format"""

    def __init__(self):
        self.api_key = API_KEY
        self.sport = "americanfootball_nfl"
        self.timestamp = datetime.now().isoformat()
        self.credit_start = None
        self.credit_end = None

    def extract(self) -> pd.DataFrame:
        """Extract NFL odds in standardized V3 format."""
        print(f"\n{'='*60}")
        print("EVisionBet V3 - NFL Extraction")
        print(f"{'='*60}")

        events = self._fetch_events()
        if not events:
            print("❌ No events found")
            return pd.DataFrame()

        # Filter events: only process those that haven't started
        # (commence_time > now + 5 min)
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
            msg = (
                "⏭️  Skipped {skipped} event(s) that already started or "
                "start in <5 min"
            )
            print(msg.format(skipped=skipped))

        events = filtered_events
        if not events:
            print("❌ No upcoming events (all started or starting in <5 min)")
            return pd.DataFrame()

        rows: List[Dict] = []
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

        # Initialize empty pair_id column (populated in filter stage)
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
        df = df[core_cols + ALL_BOOKMAKERS]

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

        event_id_str = str(event_id) if event_id is not None else ""
        odds_resp = self._fetch_odds(event_id_str)
        if not odds_resp:
            return []

        bookmakers = odds_resp.get("bookmakers", [])
        raw_data: Dict = {}
        for bm in bookmakers:
            book_key = bm.get("key")
            if book_key not in BOOKMAKER_MAPPING:
                continue
            book_name = BOOKMAKER_MAPPING[book_key]

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
                        raw_data[key] = {"points": {}, "prices": {}}

                    if pd.notna(point):
                        p = float(point)
                        raw_data[key]["points"].setdefault(p, 0)
                        raw_data[key]["points"][p] += 1

                    if price is not None:
                        raw_data[key]["prices"].setdefault(point, {})
                        raw_data[key]["prices"][point][book_name] = price

        rows: List[Dict] = []
        for key, data in raw_data.items():
            if len(key) == 3 and key[2] is not None:
                market_type, identifier, selection = key
                player_name = identifier
            else:
                market_type, selection, _ = key
                player_name = ""

            for point, books_with_point in data["prices"].items():
                row = {
                    "event_id": event_id,
                    "extracted_at": self.timestamp,
                    "commence_time": self._format_time(commence),
                    "league": "NFL",
                    "event_name": event_name,
                    "market_type": market_type,
                    "point": str(point) if point else "",
                    "selection": selection,
                    "player_name": player_name,
                }
                for book_name, price in books_with_point.items():
                    row[book_name] = price
                rows.append(row)

        return rows

    def _fetch_odds(self, event_id: str) -> Dict:
        url = f"{API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"

        # NFL VALID MARKETS (verified Jan 10, 2026)
        # Core markets available for NFL
        primary_markets = (
            "h2h,spreads,totals,alternate_spreads,alternate_totals,"
            "team_totals,"
            "player_pass_yds,player_pass_tds,player_pass_completions,"
            "player_pass_attempts,player_pass_longest_completion,"
            "player_rush_yds,player_rush_attempts,player_rush_longest,"
            "player_receptions"
        )

        fallback_markets = "h2h,spreads,totals"

        # Optional NFL markets (enable via INCLUDE_OPTIONAL_MARKETS=true)
        # Note: first_half markets and player_td_anytime NOT available for NFL
        include_optional = (
            os.getenv("INCLUDE_OPTIONAL_MARKETS", "true").lower() == "true"
        )
        optional_markets = (
            "player_field_goals,player_kicking_points,"
            "player_1st_td,player_last_td,player_anytime_td"
        )
        markets_to_use = primary_markets + (
            "," + optional_markets if include_optional else ""
        )

        params = {
            "apiKey": self.api_key,
            "bookmakers": ",".join(ALL_BOOKMAKERS),
            "markets": markets_to_use,
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
            msg_primary = (
                "⚠️  Error fetching odds for {event_id} with primary markets: "
                "{err}"
            )
            print(msg_primary.format(event_id=event_id, err=e))
            # Retry with a minimal market set to avoid total failure
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
        """Format ISO time to readable format (Perth timezone)."""
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
            filename = "NFL_Raw.csv"

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
    extractor = NFLExtractorV3()
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
