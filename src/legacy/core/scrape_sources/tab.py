"""TAB (Australia) adapter.

TAB operates separate state-based endpoints (NSW, VIC, QLD, etc.).
This adapter targets the primary TAB API used for sports betting.

Endpoints (as of Nov 2025):
- Fixtures: /v1/tab-info-service/sports/fixtures
- Market prices: /v1/tab-info-service/racing/dates/{date}/meetings/{meeting}/races/{race}/win/prices

IMPORTANT:
- TAB schema includes racing (horses/greyhounds/harness) + sports
- Sports betting uses different endpoint structure than racing
- Rate limit: 20-30 req/min recommended
- Some endpoints may require region headers
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import requests

from .base_adapter import BookmakerAdapter, Event, Market, Outcome


class TABAdapter(BookmakerAdapter):
    """TAB (Australia) data adapter."""
    
    BASE_URL = "https://api.beta.tab.com.au"
    
    # Sport mapping (simplified - TAB uses numeric IDs internally)
    SPORT_MAP = {
        "basketball_nba": "basketball",
        "americanfootball_nfl": "american-football",
        "aussierules_afl": "afl",
        "rugbyleague_nrl": "rugby-league",
    }
    
    MARKET_MAP = {
        "head to head": "h2h",
        "head-to-head": "h2h",
        "line": "spreads",
        "total": "totals",
        "match winner": "h2h",
    }
    
    def __init__(self):
        super().__init__(rate_limit_requests=25, rate_limit_period=60)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EVisionBot/1.0 (Respectful scraper; contact: your@email.com)",
            "Accept": "application/json",
            "x-tab-client-version": "1.0",
        })
    
    def _get_bookmaker_key(self) -> str:
        return "tab"
    
    def fetch_events(
        self,
        sport: str,
        markets: Optional[List[str]] = None
    ) -> List[Event]:
        """
        Fetch events for given sport.
        
        TAB structure: query fixtures by sport, then fetch individual markets.
        """
        sport_slug = self.SPORT_MAP.get(sport)
        if not sport_slug:
            return []
        
        fixtures = self._fetch_fixtures(sport_slug)
        events = []
        
        for fixture in fixtures:
            try:
                event = self._parse_fixture(fixture, sport, markets)
                if event:
                    events.append(event)
            except Exception as e:
                print(f"[TAB] Failed to parse fixture {fixture.get('id')}: {e}")
        
        return events
    
    def _fetch_fixtures(self, sport_slug: str) -> List[Dict]:
        """Fetch fixtures for sport."""
        with self.rate_limiter:
            try:
                url = f"{self.BASE_URL}/v1/tab-info-service/sports/{sport_slug}/competitions"
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[TAB] Failed to fetch {sport_slug} fixtures: {e}")
                return []
        
        # Extract fixtures from competitions
        fixtures = []
        competitions = data.get("competitions", [])
        
        for comp in competitions:
            matches = comp.get("matches", [])
            fixtures.extend(matches)
        
        return fixtures
    
    def _parse_fixture(
        self,
        raw: Dict,
        sport_key: str,
        requested_markets: Optional[List[str]]
    ) -> Optional[Event]:
        """Parse fixture into Event object."""
        match_id = str(raw.get("matchId", ""))
        if not match_id:
            return None
        
        # Extract teams
        home_team = raw.get("homeTeam", {}).get("name", "")
        away_team = raw.get("awayTeam", {}).get("name", "")
        
        if not home_team or not away_team:
            return None
        
        # Commence time
        start_time_raw = raw.get("startTime")
        if start_time_raw:
            try:
                commence_time = datetime.fromisoformat(start_time_raw.replace("Z", "+00:00")).isoformat()
            except Exception:
                commence_time = start_time_raw
        else:
            commence_time = datetime.utcnow().isoformat()
        
        # Parse markets (TAB embeds basic markets in fixture response)
        markets_parsed = []
        raw_markets = raw.get("markets", [])
        
        for mkt in raw_markets:
            parsed_mkt = self._parse_market(mkt, requested_markets)
            if parsed_mkt:
                markets_parsed.append(parsed_mkt)
        
        # If no markets embedded, can optionally fetch via separate endpoint
        # (Skipped here for simplicity; add if needed)
        
        if not markets_parsed:
            return None
        
        return Event(
            id=match_id,
            sport_key=sport_key,
            commence_time=commence_time,
            home_team=home_team,
            away_team=away_team,
            bookmaker_key=self.bookmaker_key,
            markets=markets_parsed
        )
    
    def _parse_market(
        self,
        raw: Dict,
        requested_markets: Optional[List[str]]
    ) -> Optional[Market]:
        """Parse raw market JSON."""
        market_name = raw.get("marketName", "").lower()
        market_key = self.MARKET_MAP.get(market_name, market_name.replace(" ", "_"))
        
        # Filter by requested markets
        if requested_markets and market_key not in requested_markets:
            return None
        
        outcomes = []
        propositions = raw.get("propositions", [])
        
        for prop in propositions:
            name = prop.get("name", "")
            return_win = prop.get("returnWin")
            
            if not name or not return_win:
                continue
            
            try:
                price = float(return_win)
            except (ValueError, TypeError):
                continue
            
            # Extract handicap if present
            point = None
            handicap = prop.get("handicap")
            if handicap is not None:
                try:
                    point = float(handicap)
                except (ValueError, TypeError):
                    pass
            
            outcomes.append(Outcome(
                name=name,
                price=price,
                point=point
            ))
        
        if not outcomes:
            return None
        
        return Market(
            key=market_key,
            outcomes=outcomes,
            last_update=raw.get("timestamp")
        )
