"""Base adapter interface for bookmaker scrape sources.

All adapters must implement this interface to ensure consistent data structure
compatible with the main bot's event processing pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Outcome:
    """Single outcome (e.g., Over/Under, Home/Away)."""
    name: str  # "Over", "Under", "Home", "Away", player name
    price: float  # Decimal odds
    point: Optional[float] = None  # Line value for spreads/totals/props
    description: Optional[str] = None  # Player name for props


@dataclass
class Market:
    """Single market within an event."""
    key: str  # e.g., "h2h", "spreads", "totals", "player_points"
    outcomes: List[Outcome]
    last_update: Optional[str] = None  # ISO timestamp if available


@dataclass
class Event:
    """Single sporting event with markets."""
    id: str  # Unique event ID from bookmaker
    sport_key: str  # e.g., "basketball_nba", "americanfootball_nfl"
    commence_time: str  # ISO timestamp
    home_team: str
    away_team: str
    bookmaker_key: str  # e.g., "sportsbet", "tab", "pointsbetau"
    markets: List[Market]


class BookmakerAdapter(ABC):
    """Abstract base for bookmaker data adapters."""
    
    def __init__(self, rate_limit_requests: int = 30, rate_limit_period: int = 60):
        """
        Initialize adapter with rate limiting.
        
        Args:
            rate_limit_requests: Max requests allowed
            rate_limit_period: Time period in seconds
        """
        from .rate_limiter import RateLimiter
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_period)
        self.bookmaker_key = self._get_bookmaker_key()
    
    @abstractmethod
    def _get_bookmaker_key(self) -> str:
        """Return standardized bookmaker key (e.g., 'sportsbet')."""
        pass
    
    @abstractmethod
    def fetch_events(
        self,
        sport: str,
        markets: Optional[List[str]] = None
    ) -> List[Event]:
        """
        Fetch events for given sport and markets.
        
        Args:
            sport: Sport key (e.g., "basketball_nba")
            markets: List of market keys to fetch (None = all available)
        
        Returns:
            List of Event objects
        """
        pass
    
    def fetch_markets(self, event_id: str) -> List[Market]:
        """
        Fetch markets for specific event (optional override).
        
        Default implementation returns empty list; adapters can override
        for lazy market loading.
        """
        return []
    
    def normalize_team_name(self, name: str) -> str:
        """
        Normalize team name to match Odds API convention.
        
        Override if bookmaker uses different team naming.
        """
        return name.strip()
    
    def normalize_market_key(self, raw_key: str) -> str:
        """
        Normalize market key to match Odds API convention.
        
        Examples:
            "Head To Head" -> "h2h"
            "Line" -> "spreads"
            "Total Points" -> "totals"
        """
        key_map = {
            "head to head": "h2h",
            "head2head": "h2h",
            "moneyline": "h2h",
            "line": "spreads",
            "handicap": "spreads",
            "total points": "totals",
            "totals": "totals",
            "over/under": "totals",
        }
        normalized = raw_key.lower().strip()
        return key_map.get(normalized, normalized.replace(" ", "_"))
