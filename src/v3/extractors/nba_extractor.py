"""
NBA Extractor - Basketball (NBA) odds extraction

Configuration is loaded from src.v3.configs.sports.py:
- Regions: Per-config (currently au, us, us2, eu)
- Base Markets: h2h, spreads, totals
- Player Props: Per-config (points, rebounds, assists)
- Time Window: Per-config (48 hours)
- API Tiers: Per-config (base + props)

Fair Odds: Uses NBAFairOdds class with sport-specific logic
"""

import logging
from typing import Dict, List

from src.v3.base_extractor import BaseExtractor
from src.v3.configs import get_api_config_for_sport

logger = logging.getLogger(__name__)


class NBAExtractor(BaseExtractor):
    """NBA-specific odds extractor"""

    SPORT_KEY = "basketball_nba"
    SPORT_NAME = "NBA"
    BASE_MARKETS = ["h2h", "spreads", "totals"]
    PLAYER_PROPS = [
        "player_points",
        "player_rebounds",
        "player_assists",
    ]
    REGIONS = ["au", "us", "us2", "eu"]  # Will be overridden by config
    TIME_WINDOW_HOURS = 48  # Will be overridden by config

    def fetch_odds(self) -> List[Dict]:
        """
        Fetch NBA odds using tiered approach:
        - Tier 1: Base markets (always)
        - Tier 2: Player props (if enabled in config)
        - Tier 3: Advanced markets (if enabled)
        """
        all_markets = []
        total_cost = 0
        league = self.SPORT_NAME  # "NBA"
        
        logger.info(f"Starting {self.SPORT_NAME} extraction (Tiers: 1-3)")

        # ====================================================================
        # TIER 1: ALWAYS - Base markets (h2h, spreads, totals)
        # ====================================================================
        logger.info("[Tier 1] Fetching base markets...")
        events, cost = self._fetch_base_markets()
        total_cost += cost

        if not events:
            logger.warning("No events found for base markets")
            return all_markets

        # Filter events by time window
        events = [e for e in events if self._is_event_in_window(e.get("commence_time", ""))]
        logger.info(f"[Tier 1] Events in window: {len(events)}")

        # Group markets by (event_id, market_type, point, selection)
        # This consolidates all bookmakers for each market into one row
        markets_grouped = {}

        # Convert to markets format - flatten all bookmaker/market/outcome combinations
        for event in events:
            event_id = event.get("id", "")
            event_name = f"{event.get('away_team')} @ {event.get('home_team')}"
            commence_time = event.get("commence_time", "")
            bookmakers = event.get("bookmakers", [])

            # Iterate through each bookmaker
            for bookmaker_obj in bookmakers:
                if not isinstance(bookmaker_obj, dict):
                    continue
                    
                bookmaker = bookmaker_obj.get("key", "").lower()
                markets = bookmaker_obj.get("markets", [])

                # Iterate through each market
                for market_obj in markets:
                    if not isinstance(market_obj, dict):
                        continue
                        
                    market_type = market_obj.get("key", "")
                    outcomes = market_obj.get("outcomes", [])

                    # Iterate through each outcome
                    for outcome in outcomes:
                        if not isinstance(outcome, dict):
                            continue
                            
                        selection = outcome.get("name", "")
                        odds = self._parse_float(outcome.get("price", 0))
                        point_raw = outcome.get("point")
                        
                        # Normalize point to half-point increments (0.5)
                        point = self._normalize_point(point_raw)

                        # Skip invalid odds
                        if odds < 1.01:
                            continue

                        # Create market key for grouping (using normalized point)
                        market_key = (event_id, market_type, point, selection)

                        # If not seen before, create entry
                        if market_key not in markets_grouped:
                            markets_grouped[market_key] = {
                                "event_id": event_id,
                                "event_name": event_name,
                                "commence_time": commence_time,
                                "league": league,
                                "market_type": market_type,
                                "point": point,
                                "selection": selection,
                                "player_name": "",
                                "bookmakers": {},
                            }

                        # Add bookmaker odds to this market
                        markets_grouped[market_key]["bookmakers"][bookmaker] = odds

        # Convert dict back to list
        all_markets = list(markets_grouped.values())

        logger.info(f"[API] Total cost: {total_cost} | Extracted {len(all_markets)} unique markets")

        # ====================================================================
        # TIER 2: Player props (disabled for now - simplify first)
        # ====================================================================
        # TODO: Implement per-event player prop fetching
        # prop_cost = self._fetch_player_props(events)
        # total_cost += prop_cost

        logger.info(f"[API] Total extraction cost: {total_cost}")

        return all_markets


def main():
    """Run NBA extraction"""
    extractor = NBAExtractor()
    result = extractor.run()
    print(f"\nResult: {result}")
    return result


if __name__ == "__main__":
    main()
