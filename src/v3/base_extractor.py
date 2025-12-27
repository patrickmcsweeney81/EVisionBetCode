"""
Base Extractor Class - Common logic for all sport extractors

Responsibilities:
- API authentication and request handling
- CSV output and caching
- Error handling and retries
- Data validation
"""

import csv
import logging
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytz

import requests
from dotenv import load_dotenv

# Import configurations
try:
    from src.v3.configs import (
        get_sport_config,
        get_regions_for_sport,
        get_api_config_for_sport,
        get_fair_odds_config,
    )
except ImportError:
    # Fallback for direct execution
    def get_sport_config(key): return {}
    def get_regions_for_sport(key): return {"extract_from": ["au", "us"], "time_window_hours": 48}
    def get_api_config_for_sport(key): return {}
    def get_fair_odds_config(key): return {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class BaseExtractor(ABC):
    """Base class for sport-specific extractors"""

    # Must be overridden by subclasses
    SPORT_KEY: str = ""
    SPORT_NAME: str = ""
    BASE_MARKETS: List[str] = ["h2h", "spreads", "totals"]
    PLAYER_PROPS: List[str] = []
    REGIONS: List[str] = ["au", "us", "eu"]
    TIME_WINDOW_HOURS: int = 48

    # API Configuration
    ODDS_API_HOST = "https://api.the-odds-api.com"
    ODDS_FORMAT = "decimal"

    # Output file (will be set by subclass)
    OUTPUT_FILE: Optional[Path] = None

    def __init__(self):
        """Initialize extractor with API key and data path"""
        self.api_key = os.getenv("ODDS_API_KEY", "")
        if not self.api_key:
            logger.error("❌ ODDS_API_KEY not set in .env")
            sys.exit(1)

        # Setup output path
        data_dir = Path(__file__).parent.parent.parent / "data" / "v3" / "extracts"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = data_dir / f"{self.SPORT_KEY}_raw.csv"

        # Load config for this sport
        self.sport_config = get_sport_config(self.SPORT_KEY)
        self.api_tiers_config = get_api_config_for_sport(self.SPORT_KEY)
        self.region_config = get_regions_for_sport(self.SPORT_KEY)
        self.fair_odds_config = get_fair_odds_config(self.SPORT_KEY)
        
        # Set regions from config
        if self.region_config and "extract_from" in self.region_config:
            self.REGIONS = self.region_config["extract_from"]
        
        # Set time window from config
        if self.region_config and "time_window_hours" in self.region_config:
            self.TIME_WINDOW_HOURS = self.region_config["time_window_hours"]

        logger.info(f"Initialized {self.SPORT_NAME} extractor")
        logger.info(f"Output: {self.output_file}")
        logger.info(f"Regions: {', '.join(self.REGIONS)}")
        logger.info(f"Time window: {self.TIME_WINDOW_HOURS}h")

    def _utc_to_local_time(self, utc_time_str: str) -> str:
        """
        Convert UTC time (e.g., '2025-12-26T03:38:00Z') to local user time.
        Format: 'HH:00am DD/MM/YY' (e.g., '08:00am 25/12/25')
        
        Args:
            utc_time_str: UTC timestamp in ISO format (e.g., '2025-12-26T03:38:00Z')
            
        Returns:
            Formatted local time string
        """
        try:
            # Parse UTC time
            if utc_time_str.endswith('Z'):
                utc_time_str = utc_time_str[:-1] + '+00:00'
            
            dt_utc = datetime.fromisoformat(utc_time_str)
            
            # Convert to local timezone (user's machine timezone)
            local_tz = pytz.timezone('UTC').localize(dt_utc.replace(tzinfo=None)).astimezone()
            
            # Format as requested: HH:00am DD/MM/YY
            formatted = local_tz.strftime('%I:%M%p %d/%m/%y').lower()
            return formatted
        except Exception as e:
            logger.warning(f"Could not convert time {utc_time_str}: {e}")
            return utc_time_str

    @abstractmethod
    def fetch_odds(self) -> List[Dict]:
        """
        Fetch odds from API. Must be implemented by subclass.
        Returns list of market dictionaries.
        """
        pass

    def _fetch_base_markets(self) -> Tuple[List[Dict], int]:
        """
        Fetch h2h, spreads, totals from API
        Returns (events, cost)
        """
        url = f"{self.ODDS_API_HOST}/v4/sports/{self.SPORT_KEY}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": ",".join(self.REGIONS),
            "markets": ",".join(self.BASE_MARKETS),
            "oddsFormat": self.ODDS_FORMAT,
        }

        logger.info(f"Fetching {self.SPORT_NAME} base markets: {', '.join(self.BASE_MARKETS)}")

        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            events = resp.json()
            cost = int(resp.headers.get("x-requests-last", "0"))
            remaining = resp.headers.get("x-requests-remaining", "?")
            logger.info(f"✓ Got {len(events)} events | Cost: {cost} | Remaining: {remaining}")
            return events, cost
        except Exception as e:
            logger.error(f"✗ Base markets error: {e}")
            return [], 0

    def _fetch_tier_2_props(self) -> Tuple[List[Dict], int]:
        """
        Tier 2: Fetch player props (if enabled and if subclass implements)
        Returns (prop_markets, cost)
        """
        if not self.api_tiers_config.get("fetch_player_props", False):
            logger.info(f"[Tier 2] Skipped for {self.SPORT_NAME}")
            return [], 0
        
        # Subclass can override this method for custom prop handling
        logger.info(f"[Tier 2] No custom props implementation for {self.SPORT_NAME}")
        return [], 0

    def _fetch_tier_3_advanced(self) -> Tuple[List[Dict], int]:
        """
        Tier 3: Fetch advanced markets (3-way, partials, etc)
        Returns (advanced_markets, cost)
        """
        if not self.api_tiers_config.get("fetch_advanced_markets", False):
            logger.info(f"[Tier 3] Skipped for {self.SPORT_NAME}")
            return [], 0
        
        logger.info(f"[Tier 3] No advanced implementation for {self.SPORT_NAME}")
        return [], 0

    def _is_event_in_window(self, commence_time_str: str) -> bool:
        """Check if event start time is within time window"""
        try:
            event_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = event_time - now

            min_seconds = 5 * 60  # Don't fetch events <5 min from now
            max_seconds = self.TIME_WINDOW_HOURS * 3600

            in_window = min_seconds <= delta.total_seconds() <= max_seconds
            return in_window
        except Exception:
            return True  # Include if parsing fails

    def _parse_float(self, value) -> float:
        """Parse string/float to float, return 0.0 on error"""
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).strip())
        except (ValueError, AttributeError):
            return 0.0

    def _normalize_point(self, point) -> str:
        """
        Normalize point value to half-point increments (0.5).
        
        This ensures consistent market grouping regardless of how bookmakers
        present the lines (e.g., 225.0 vs 225 vs 225.5).
        
        Examples:
            225.0 -> "225.0"
            225.3 -> "225.5" (rounds to nearest 0.5)
            225.7 -> "226.0" (rounds to nearest 0.5)
            226.0 -> "226.0"
            None -> ""
            
        Args:
            point: The point value (can be float, int, str, or None)
            
        Returns:
            Normalized point as string, or empty string if invalid
        """
        if point is None or point == "":
            return ""
        
        try:
            # Parse to float
            point_float = self._parse_float(point)
            
            # Round to nearest 0.5 using floor + 0.5 method
            # This avoids banker's rounding issues
            import math
            normalized = math.floor(point_float * 2 + 0.5) / 2
            
            # Format with one decimal place to show .0 or .5
            return f"{normalized:.1f}"
        except (ValueError, TypeError):
            return ""

    def _is_valid_odds(self, odds: float) -> bool:
        """Validate odds (should be between 1.01 and ~1000)"""
        return 1.01 <= odds <= 1000.0

    def _deduplicate_markets(self, markets: List[Dict]) -> List[Dict]:
        """Remove duplicate market entries (keep most recent odds)"""
        seen = {}
        for market in markets:
            key = (
                market.get("event_id"),
                market.get("market_type"),
                market.get("point"),
                market.get("selection"),
            )
            if key not in seen:
                seen[key] = market
            else:
                # Keep if newer
                if market.get("extracted_at", "") > seen[key].get("extracted_at", ""):
                    seen[key] = market

        return list(seen.values())

    def _validate_market_data(self, markets: List[Dict]) -> Tuple[List[Dict], int]:
        """
        Validate markets:
        - All required fields present
        - Odds in valid range
        - Sufficient bookmaker coverage
        """
        valid = []
        invalid = 0

        for market in markets:
            # Check required fields
            required = ["event_id", "market_type", "selection", "bookmakers"]
            if not all(market.get(f) for f in required):
                invalid += 1
                continue

            # Check bookmaker odds - bookmakers is a dict {bookmaker_name: odds}
            has_valid_odds = False
            bookmakers = market.get("bookmakers", {})
            for bookmaker_name, odds in bookmakers.items():
                odds_float = self._parse_float(odds)
                if self._is_valid_odds(odds_float):
                    has_valid_odds = True
                    break

            if has_valid_odds:
                valid.append(market)
            else:
                invalid += 1

        logger.info(f"Validation: {len(valid)} valid, {invalid} invalid")
        return valid, invalid

    def _write_csv(self, markets: List[Dict]) -> None:
        """
        Write markets to CSV with wide format (each bookmaker as a column).
        
        Column order (as requested):
        1. event_id
        2. extracted_at (with local user time)
        3. commence_time
        4. league
        5. event_name
        6. market_type
        7. point
        8. selection
        9. bookmakers (4⭐ sharps first, then 3⭐, then 0⭐ targets/AU, then all others)
        
        Filename includes timestamp for easy version tracking during testing.
        """
        # Import ratings for proper bookmaker ordering
        from src.v3.configs.bookmakers import BOOKMAKER_RATINGS
        
        # Add timestamp to filename for easy testing/tracking
        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        output_path = Path(self.output_file)
        timestamped_file = output_path.parent / f"{output_path.stem}_{timestamp_str}{output_path.suffix}"
        
        logger.info(f"Writing {len(markets)} markets to {timestamped_file}")

        try:
            # Collect all unique bookmakers across all markets
            all_bookmakers = set()
            for market in markets:
                all_bookmakers.update(market.get("bookmakers", {}).keys())
            
            all_bookmakers_sorted = sorted(list(all_bookmakers))
            logger.info(f"Found {len(all_bookmakers_sorted)} unique bookmakers: {', '.join(all_bookmakers_sorted)}")

            # ORDER BOOKMAKERS by star rating:
            # 1. 4⭐ sharps (Pinnacle, Betfair EU, DraftKings, FanDuel)
            # 2. 3⭐ sharps (BetOnline, LowVig)
            # 3. 0⭐ targets/AU (All Australian local books)
            # 4. All others (1⭐ and 2⭐)
            
            sharps_4 = []
            sharps_3 = []
            targets_0 = []
            others = []
            
            for book in all_bookmakers_sorted:
                rating = BOOKMAKER_RATINGS.get(book, {})
                stars = rating.get("stars", -1)
                
                if stars == 4:
                    sharps_4.append(book)
                elif stars == 3:
                    sharps_3.append(book)
                elif stars == 0:
                    targets_0.append(book)
                else:
                    others.append(book)
            
            # Sort each group alphabetically
            sharps_4 = sorted(sharps_4)
            sharps_3 = sorted(sharps_3)
            targets_0 = sorted(targets_0)
            others = sorted(others)
            
            # Combine in priority order
            ordered_bookmakers = sharps_4 + sharps_3 + targets_0 + others
            
            logger.info(f"Book order: {len(sharps_4)} 4⭐ | {len(sharps_3)} 3⭐ | {len(targets_0)} 0⭐ | {len(others)} others")

            rows = []
            for market in markets:
                event_id = market.get("event_id", "")
                event_name = market.get("event_name", "")
                commence_time_utc = market.get("commence_time", "")
                # Convert UTC to local user time (e.g., "08:00am 25/12/25")
                commence_time_local = self._utc_to_local_time(commence_time_utc)
                
                market_type = market.get("market_type", "")
                point = market.get("point", "")
                selection = market.get("selection", "")
                extracted_at = now.isoformat()  # Use consistent timestamp

                # Build row with REORDERED base columns
                row = {
                    "event_id": event_id,
                    "extracted_at": extracted_at,
                    "commence_time": commence_time_local,  # Use local time
                    "league": market.get("league", self.SPORT_NAME),
                    "event_name": event_name,
                    "market_type": market_type,
                    "point": point,
                    "selection": selection,
                }

                # Add odds for each bookmaker in correct order
                bookmakers_dict = market.get("bookmakers", {})
                for bookmaker in ordered_bookmakers:
                    odds = bookmakers_dict.get(bookmaker)
                    if odds:
                        row[bookmaker] = f"{self._parse_float(odds):.2f}"
                    else:
                        row[bookmaker] = ""

                rows.append(row)

            # Write to CSV with REORDERED fieldnames
            fieldnames = ["event_id", "extracted_at", "commence_time", "league", "event_name", 
                         "market_type", "point", "selection"] + ordered_bookmakers

            with open(timestamped_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"✓ Wrote {len(rows)} rows to CSV with {len(all_bookmakers)} bookmaker columns")

        except Exception as e:
            logger.error(f"✗ Failed to write CSV: {e}")
            raise

    def run(self) -> Dict:
        """
        Main execution method
        Returns summary dict
        """
        try:
            logger.info(f"{'='*60}")
            logger.info(f"Extracting {self.SPORT_NAME} odds...")
            logger.info(f"{'='*60}")

            # Fetch odds
            markets = self.fetch_odds()

            if not markets:
                logger.warning(f"No odds found for {self.SPORT_NAME}")
                return {
                    "sport": self.SPORT_KEY,
                    "markets_found": 0,
                    "status": "empty",
                }

            # Deduplicate
            markets = self._deduplicate_markets(markets)

            # Validate
            markets, invalid_count = self._validate_market_data(markets)

            # Write
            self._write_csv(markets)

            logger.info(f"✓ {self.SPORT_NAME} extraction complete")
            return {
                "sport": self.SPORT_KEY,
                "name": self.SPORT_NAME,
                "markets_found": len(markets),
                "invalid_count": invalid_count,
                "output_file": str(self.output_file),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"✗ {self.SPORT_NAME} extraction failed: {e}")
            return {
                "sport": self.SPORT_KEY,
                "name": self.SPORT_NAME,
                "status": "error",
                "error": str(e),
            }
