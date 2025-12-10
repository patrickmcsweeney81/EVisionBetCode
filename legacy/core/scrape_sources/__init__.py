"""
Scrape sources package for supplemental AU bookmaker data.

This package provides lightweight adapters for bookmakers not fully covered
by The Odds API aggregator. Each adapter implements a common interface for
fetching events and markets.

Usage:
    from core.scrape_sources.sportsbet import SportsbetAdapter
    from core.scrape_sources.merger import merge_odds_data
    
    adapter = SportsbetAdapter()
    scraped = adapter.fetch_events(sport="basketball_nba")
    merged = merge_odds_data(primary_events, scraped)

IMPORTANT:
- Respect rate limits (use built-in rate_limiter)
- Cache responses (5-10 min TTL recommended)
- Follow each site's TOS
- Use clear user-agent identifying your bot
"""

from .base_adapter import BookmakerAdapter, Event, Market, Outcome
from .rate_limiter import RateLimiter

__all__ = [
    "BookmakerAdapter",
    "Event",
    "Market", 
    "Outcome",
    "RateLimiter",
]
