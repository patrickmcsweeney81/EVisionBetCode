"""Sportsbet (Australia) adapter.

Fetches odds from Sportsbet's public JSON endpoints used by their web frontend.

Endpoints (as of Nov 2025):
- Events: /api/v3/sports/{sport}/competitions/{comp}/events
- Markets: /api/v3/events/{event_id}/markets

IMPORTANT:
- These are unofficial endpoints (public but not documented API)
- Schema may change without notice
- Implement schema validation and graceful degradation
- Rate limit: 30 req/min recommended
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional

import requests

from .base_adapter import BookmakerAdapter, Event, Market, Outcome


class SportsbetAdapter(BookmakerAdapter):
    """Sportsbet data adapter."""
    
    BASE_URL = "https://www.sportsbet.com.au/apigw"
    
    # Sport code mapping (Sportsbet -> Odds API convention)
    SPORT_MAP = {
        "basketball_nba": "basketball/nba",
        "americanfootball_nfl": "american-football/nfl",
        "aussierules_afl": "australian-rules/afl",
        "rugbyleague_nrl": "rugby-league/nrl",
    }
    
    # Market key normalization
    MARKET_MAP = {
        "head to head": "h2h",
        "line": "spreads",
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
        return "sportsbet"
    
    def fetch_events(
        self,
        sport: str,
        markets: Optional[List[str]] = None
    ) -> List[Event]:
        """
        Fetch events for given sport.
        
        Note: Sportsbet requires competition-level queries; this implementation
        fetches from primary competitions for each sport.
        """
        sport_path = self.SPORT_MAP.get(sport)
        if not sport_path:
            return []
        
        events = []
        
        # Fetch primary competitions for sport
        # (In production, you'd discover competitions dynamically or maintain a config)
        comps = self._get_competitions(sport_path)
        
        for comp_id in comps[:3]:  # Limit to top 3 comps to avoid rate limits
            comp_events = self._fetch_competition_events(sport, sport_path, comp_id, markets)
            events.extend(comp_events)
        
        return events
    
    def _get_competitions(self, sport_path: str) -> List[str]:
        """Get competition IDs for sport (stub - expand per sport)."""
        # Simplified: return common competition IDs
        # In production: query /api/v3/sports/{sport}/competitions
        comp_map = {
            "basketball/nba": ["nba-regular-season"],
            "american-football/nfl": ["nfl-regular-season"],
            "australian-rules/afl": ["afl-premiership"],
            "rugby-league/nrl": ["nrl-premiership"],
        }
        return comp_map.get(sport_path, [])
    
    def _fetch_competition_events(
        self,
        sport_key: str,
        sport_path: str,
        comp_id: str,
        markets: Optional[List[str]]
    ) -> List[Event]:
        """Fetch events for specific competition."""
        with self.rate_limiter:
            try:
                url = f"{self.BASE_URL}/sportsbook-sports/Sportsbook/Sports/{sport_path}/{comp_id}/events"
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[Sportsbet] Failed to fetch {comp_id}: {e}")
                return []
        
        events = []
        event_list = data.get("events", [])
        
        for evt in event_list:
            try:
                parsed = self._parse_event(evt, sport_key, markets)
                if parsed:
                    events.append(parsed)
            except Exception as e:
                print(f"[Sportsbet] Failed to parse event {evt.get('id')}: {e}")
        
        return events
    
    def _parse_event(
        self,
        raw: Dict,
        sport_key: str,
        requested_markets: Optional[List[str]]
    ) -> Optional[Event]:
        """Parse raw event JSON into Event object."""
        event_id = str(raw.get("id", ""))
        if not event_id:
            return None
        
        # Extract teams (format varies; common pattern: competitors array)
        competitors = raw.get("competitors", [])
        if len(competitors) < 2:
            return None
        
        home_team = competitors[0].get("name", "")
        away_team = competitors[1].get("name", "")
        
        # Commence time
        start_time_raw = raw.get("startTime")
        if start_time_raw:
            try:
                commence_time = datetime.fromisoformat(start_time_raw.replace("Z", "+00:00")).isoformat()
            except Exception:
                commence_time = start_time_raw
        else:
            commence_time = datetime.utcnow().isoformat()
        
        # Parse markets
        markets_parsed = []
        raw_markets = raw.get("markets", [])
        
        for mkt in raw_markets:
            parsed_mkt = self._parse_market(mkt, requested_markets)
            if parsed_mkt:
                markets_parsed.append(parsed_mkt)
        
        if not markets_parsed:
            return None
        
        return Event(
            id=event_id,
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
        selections = raw.get("selections", [])
        
        for sel in selections:
            name = sel.get("name", "")
            price_raw = sel.get("price", {}).get("winPrice")
            
            if not name or not price_raw:
                continue
            
            try:
                price = float(price_raw)
            except (ValueError, TypeError):
                continue
            
            # Extract point/line if present (e.g., spreads/totals)
            point = None
            handicap = sel.get("handicap")
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
            last_update=raw.get("lastUpdate")
        )
