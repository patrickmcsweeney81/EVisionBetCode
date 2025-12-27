"""
NFL Extractor - American Football (NFL) odds extraction

Configuration is loaded from src.v3.configs.sports.py:
- Regions: Per-config (currently us, us2, au)
- Base Markets: h2h, spreads, totals
- Player Props: Per-config (pass yards, rush yards, TDs)
- Time Window: Per-config (168 hours - weekly)
- API Tiers: Per-config (base + props)

Fair Odds: Uses NFLFairOdds class with sport-specific logic
"""

import logging
from typing import Dict, List

from src.v3.base_extractor import BaseExtractor
from src.v3.configs import get_api_config_for_sport

logger = logging.getLogger(__name__)


class NFLExtractor(BaseExtractor):
    """NFL-specific odds extractor"""

    SPORT_KEY = "americanfootball_nfl"
    SPORT_NAME = "NFL"
    BASE_MARKETS = ["h2h", "spreads", "totals"]
    PLAYER_PROPS = [
        "player_pass_yds",
        "player_rush_yds",
        "player_pass_tds",
    ]
    REGIONS = ["us", "us2", "au"]  # Will be overridden by config
    TIME_WINDOW_HOURS = 168  # Will be overridden by config

    def fetch_odds(self) -> List[Dict]:
        """
        Fetch NFL odds:
        1. Base markets (h2h, spreads, totals)
        2. Player props per event
        """
        all_markets = []
        total_cost = 0

        # ====================================================================
        # STEP 1: Fetch base markets
        # ====================================================================
        events, cost = self._fetch_base_markets()
        total_cost += cost

        if not events:
            logger.warning("No NFL events found")
            return all_markets

        # Filter events by time window
        events = [e for e in events if self._is_event_in_window(e.get("commence_time", ""))]
        logger.info(f"Events in time window: {len(events)}")

        # Convert to markets format
        for event in events:
            event_id = event.get("id", "")
            away_team = event.get("away_team", "")
            home_team = event.get("home_team", "")
            event_name = f"{away_team} @ {home_team}"
            commence_time = event.get("commence_time", "")
            league = "NFL"

            # Process each bookmaker's offerings
            for bookmaker_data in event.get("bookmakers", []):
                bookmaker = bookmaker_data.get("key", "").replace("_", "").lower()

                # Get all market types
                for market_group in bookmaker_data.get("markets", []):
                    market_key = market_group.get("key", "")

                    # Skip if not in our base markets
                    if market_key not in self.BASE_MARKETS:
                        continue

                    outcomes = market_group.get("outcomes", [])

                    if market_key == "h2h":
                        # h2h: Home vs Away (2-way)
                        if len(outcomes) == 2:
                            for outcome in outcomes:
                                market_dict = {
                                    "event_id": event_id,
                                    "event_name": event_name,
                                    "commence_time": commence_time,
                                    "league": league,
                                    "market_type": market_key,
                                    "point": "",
                                    "selection": outcome.get("name", ""),
                                    "player_name": "",
                                    "bookmakers": {
                                        bookmaker: self._parse_float(outcome.get("price", 0))
                                    },
                                }
                                all_markets.append(market_dict)

                    elif market_key == "spreads":
                        # spreads: Handicap +/- (2-way pairs)
                        if len(outcomes) == 2:
                            for outcome in outcomes:
                                market_dict = {
                                    "event_id": event_id,
                                    "event_name": event_name,
                                    "commence_time": commence_time,
                                    "league": league,
                                    "market_type": market_key,
                                    "point": outcome.get("point", ""),
                                    "selection": outcome.get("name", ""),
                                    "player_name": "",
                                    "bookmakers": {
                                        bookmaker: self._parse_float(outcome.get("price", 0))
                                    },
                                }
                                all_markets.append(market_dict)

                    elif market_key == "totals":
                        # totals: Over/Under (2-way pairs)
                        if len(outcomes) == 2:
                            for outcome in outcomes:
                                market_dict = {
                                    "event_id": event_id,
                                    "event_name": event_name,
                                    "commence_time": commence_time,
                                    "league": league,
                                    "market_type": market_key,
                                    "point": outcome.get("point", ""),
                                    "selection": outcome.get("name", ""),
                                    "player_name": "",
                                    "bookmakers": {
                                        bookmaker: self._parse_float(outcome.get("price", 0))
                                    },
                                }
                                all_markets.append(market_dict)

        logger.info(f"[API] Cost: {total_cost} | Base markets: {len(all_markets)}")

        # ====================================================================
        # STEP 2: Fetch player props per event
        # ====================================================================
        prop_cost = self._fetch_player_props(events)
        total_cost += prop_cost

        logger.info(f"[API] Total extraction cost: {total_cost}")

        return all_markets

    def _fetch_player_props(self, events: List[Dict]) -> int:
        """
        Fetch NFL player props for each event
        
        Logs cost but implementation deferred - requires per-event API calls
        """
        if not self.PLAYER_PROPS:
            logger.info("Player props disabled")
            return 0

        logger.info(f"[API] Fetching props: {', '.join(self.PLAYER_PROPS)}")
        # TODO: Implement per-event prop fetching
        # Each event requires individual API call
        total_cost = 0

        return total_cost


def main():
    """Run NFL extraction"""
    extractor = NFLExtractor()
    result = extractor.run()
    print(f"\nResult: {result}")
    return result


if __name__ == "__main__":
    main()
