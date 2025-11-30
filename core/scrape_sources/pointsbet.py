"""PointsBet (Australia) adapter.

PointsBet offers comprehensive REST API v2 used by their web/mobile apps.
Known for good prop market coverage (especially AFL/NRL alternative lines).

Endpoints (as of Nov 2025):
- Events: /api/v2/events
- Event detail with markets: /api/v2/events/{eventId}

IMPORTANT:
- PointsBet uses hierarchical event keys (competition -> event)
- Strong prop market offerings (prioritize for player props enrichment)
- Rate limit: 30 req/min recommended
- Regional filtering available (AU/US/etc.)
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import requests

from .base_adapter import BookmakerAdapter, Event, Market, Outcome


class PointsBetAdapter(BookmakerAdapter):
    """PointsBet (Australia) data adapter."""
    
    BASE_URL = "https://api.au.pointsbet.com"
    
    # Sport mapping
    SPORT_MAP = {
        "basketball_nba": "Basketball",
        "americanfootball_nfl": "American Football",
        "aussierules_afl": "Australian Rules",
        "rugbyleague_nrl": "Rugby League",
    }
    
    MARKET_MAP = {
        "money line": "h2h",
        "moneyline": "h2h",
        "spread": "spreads",
        "total": "totals",
        "match result": "h2h",
    }
    
    def __init__(self):
        super().__init__(rate_limit_requests=30, rate_limit_period=60)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EVisionBot/1.0 (Respectful scraper; contact: your@email.com)",
            "Accept": "application/json",
        })
    
    def _get_bookmaker_key(self) -> str:
        return "pointsbetau"
    
    def fetch_events(
        self,
        sport: str,
        markets: Optional[List[str]] = None
    ) -> List[Event]:
        """
        Fetch events for given sport.
        
        PointsBet API returns events with nested competitions.
        """
        sport_name = self.SPORT_MAP.get(sport)
        if not sport_name:
            return []
        
        raw_events = self._fetch_events_api(sport_name)
        events = []
        
        for evt in raw_events:
            try:
                event = self._parse_event(evt, sport, markets)
                if event:
                    events.append(event)
            except Exception as e:
                print(f"[PointsBet] Failed to parse event {evt.get('key')}: {e}")
        
        return events
    
    def _fetch_events_api(self, sport_name: str) -> List[Dict]:
        """Fetch events from PointsBet API."""
        with self.rate_limiter:
            try:
                url = f"{self.BASE_URL}/api/v2/competitions"
                params = {
                    "includeLive": "false",
                    "page": "1",
                }
                resp = self.session.get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[PointsBet] Failed to fetch events for {sport_name}: {e}")
                return []
        
        # Filter by sport and extract events
        events = []
        competitions = data.get("competitions", [])
        
        for comp in competitions:
            if comp.get("sport", {}).get("name") != sport_name:
                continue
            
            comp_events = comp.get("events", [])
            events.extend(comp_events)
        
        return events
    
    def _parse_event(
        self,
        raw: Dict,
        sport_key: str,
        requested_markets: Optional[List[str]]
    ) -> Optional[Event]:
        """Parse raw event JSON into Event object."""
        event_key = raw.get("key", "")
        if not event_key:
            return None
        
        # Extract teams (PointsBet uses "name" field with " vs " separator)
        event_name = raw.get("name", "")
        if " vs " in event_name:
            teams = event_name.split(" vs ")
            home_team = teams[0].strip()
            away_team = teams[1].strip() if len(teams) > 1 else ""
        elif " @ " in event_name:
            teams = event_name.split(" @ ")
            away_team = teams[0].strip()
            home_team = teams[1].strip() if len(teams) > 1 else ""
        else:
            # Fallback: try competitors array
            competitors = raw.get("competitors", [])
            if len(competitors) >= 2:
                home_team = competitors[0].get("name", "")
                away_team = competitors[1].get("name", "")
            else:
                return None
        
        if not home_team or not away_team:
            return None
        
        # Commence time
        start_time_raw = raw.get("startsAt")
        if start_time_raw:
            try:
                commence_time = datetime.fromisoformat(start_time_raw.replace("Z", "+00:00")).isoformat()
            except Exception:
                commence_time = start_time_raw
        else:
            commence_time = datetime.utcnow().isoformat()
        
        # Parse markets (often requires separate detail fetch, but basic markets may be embedded)
        markets_parsed = []
        
        # Check for embedded markets
        fixed_odds_markets = raw.get("fixedOddsMarkets", [])
        for mkt in fixed_odds_markets:
            parsed_mkt = self._parse_market(mkt, requested_markets)
            if parsed_mkt:
                markets_parsed.append(parsed_mkt)
        
        # If no markets, optionally fetch detail endpoint
        # (Skip for now to conserve rate limit; implement if needed)
        
        if not markets_parsed:
            return None
        
        return Event(
            id=event_key,
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
        market_name = raw.get("name", "").lower()
        market_key = self.MARKET_MAP.get(market_name, market_name.replace(" ", "_"))
        
        # Filter by requested markets
        if requested_markets and market_key not in requested_markets:
            return None
        
        outcomes = []
        selections = raw.get("outcomes", [])
        
        for sel in selections:
            name = sel.get("name", "")
            price = sel.get("price")
            
            if not name or not price:
                continue
            
            try:
                price_float = float(price)
            except (ValueError, TypeError):
                continue
            
            # Extract points/handicap
            point = None
            points_val = sel.get("points")
            if points_val is not None:
                try:
                    point = float(points_val)
                except (ValueError, TypeError):
                    pass
            
            outcomes.append(Outcome(
                name=name,
                price=price_float,
                point=point
            ))
        
        if not outcomes:
            return None
        
        return Market(
            key=market_key,
            outcomes=outcomes,
            last_update=raw.get("lastUpdated")
        )
