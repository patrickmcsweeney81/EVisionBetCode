# Scrape Sources Integration Guide

## Overview

This package supplements The Odds API with direct bookmaker data fetching for Australian bookmakers with incomplete aggregator coverage. The system includes:

- **3 production-ready adapters**: Sportsbet, TAB, PointsBet
- **Rate limiting**: Built-in token bucket rate limiter
- **Smart merging**: Fuzzy team name matching + time-based deduplication
- **Extensible design**: Easy to add new bookmakers

---

## Quick Start

### 1. Basic Usage

```python
from core.scrape_sources.sportsbet import SportsbetAdapter
from core.scrape_sources.tab import TABAdapter
from core.scrape_sources.pointsbet import PointsBetAdapter
from core.scrape_sources.merger import merge_multiple_sources

# Fetch events from primary API (The Odds API)
primary_events = fetch_odds_from_api("basketball_nba", ["h2h", "spreads", "totals"])

# Initialize scrape adapters
adapters = [
    SportsbetAdapter(),
    TABAdapter(),
    PointsBetAdapter(),
]

# Merge scraped data
merged_events = merge_multiple_sources(
    primary_events=primary_events,
    scrape_adapters=adapters,
    sport="basketball_nba",
    markets=["h2h", "spreads", "totals"]
)

# Process as normal
for event in merged_events:
    # Now includes data from Sportsbet/TAB/PointsBet if available
    process_event(event)
```ascii

### 2. Integration into Main Bot

Add to `ev_arb_bot_NEW.py` (or your main runner):

```python
# At top of file
from core.scrape_sources.merger import merge_multiple_sources
from core.scrape_sources.sportsbet import SportsbetAdapter
from core.scrape_sources.tab import TABAdapter
from core.scrape_sources.pointsbet import PointsBetAdapter

# Initialize once (reuse across runs)
SCRAPE_ADAPTERS = [
    SportsbetAdapter(),
    TABAdapter(),
    PointsBetAdapter(),
]

# In your main event fetching loop
def fetch_events_with_scrapes(sport_key, markets):
    # 1. Fetch from primary API
    primary_events = fetch_odds_api(sport_key, markets)
    
    # 2. Optionally merge scrapes (configurable)
    if os.getenv("ENABLE_SCRAPE_SOURCES", "0") == "1":
        primary_events = merge_multiple_sources(
            primary_events,
            SCRAPE_ADAPTERS,
            sport_key,
            markets
        )
    
    return primary_events
-
```

### 3. Environment Configuration

Add to `.env`:

```bash
# Enable scrape sources (0=disabled, 1=enabled)
ENABLE_SCRAPE_SOURCES=1

# Contact email for user-agent headers
SCRAPE_CONTACT_EMAIL=your@email.com
```

---

## Architecture

### Data Flow


```
┌─────────────────┐
│  Odds API       │ (Primary canonical source)
│  (aggregator)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Primary Events │ (Standardized format)
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Scrape Sources │◄─────┤ Rate Limiter │
│  - Sportsbet    │      └──────────────┘
│  - TAB          │
│  - PointsBet    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Merger         │ (Fuzzy match + dedupe)
│  - Team names   │
│  - Commence time│
│  - Markets      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Enriched       │ (Primary + scraped bookmakers)
│  Events         │
└─────────────────┘
```

### Key Components

1. **Base Adapter** (`base_adapter.py`)
   - Abstract interface all adapters implement
   - Standardized `Event`, `Market`, `Outcome` dataclasses
   - Built-in rate limiting
   - Team name and market key normalization

2. **Rate Limiter** (`rate_limiter.py`)
   - Token bucket algorithm
   - Thread-safe
   - Configurable per adapter

3. **Adapters** (one per bookmaker)
   - Fetch events from bookmaker's public JSON endpoints
   - Parse into standardized format
   - Handle bookmaker-specific quirks

4. **Merger** (`merger.py`)
   - Fuzzy team name matching (handles "LA Lakers" vs "Los Angeles Lakers")
   - Time-based event matching (30 min default tolerance)
   - Deduplication (prevents double-counting same odds)
   - Adds scraped bookmaker to primary event's bookmakers array

---

## Adding a New Bookmaker

### Template



```python
from .base_adapter import BookmakerAdapter, Event, Market, Outcome

class NewBookieAdapter(BookmakerAdapter):
    BASE_URL = "https://api.newbookie.com"
    
    def __init__(self):
        super().__init__(rate_limit_requests=30, rate_limit_period=60)
        # Setup session, headers, etc.
    
    def _get_bookmaker_key(self) -> str:
        return "newbookie"
    
    def fetch_events(self, sport: str, markets=None) -> List[Event]:
        # 1. Map sport to bookmaker's format
        # 2. Fetch events with rate limiting
        # 3. Parse and return Event objects
        pass
```

### Checklist

- [ ] Identify bookmaker's public API endpoints (inspect network tab)
- [ ] Map sport keys (Odds API convention → bookmaker format)
- [ ] Map market keys (h2h/spreads/totals → bookmaker names)
- [ ] Implement team name extraction (varies by schema)
- [ ] Handle commence time parsing (ISO format preferred)
- [ ] Add to `SCRAPE_ADAPTERS` list in bot
- [ ] Test with small sample (1-2 events) before full deployment

---

## Rate Limiting Strategy

### Per-Adapter Limits

| Adapter    | Requests/Min | Rationale                          |
|------------|--------------|-------------------------------------|
| Sportsbet  | 30           | Conservative (public endpoint)      |
| TAB        | 25           | More restrictive (regional backend) |
| PointsBet  | 30           | Well-documented API                 |

### Global Strategy

- **Stagger calls**: Don't hit all adapters simultaneously
- **Cache responses**: 5-10 min TTL for events (longer for far-future events)
- **Smart refresh**: Only re-fetch within 2 hours of commence time
- **Circuit breaker**: Pause adapter if 3+ consecutive failures

### Implementation



```python
from datetime import datetime, timedelta
from functools import lru_cache

# Simple cache decorator (use redis/memcached in production)
@lru_cache(maxsize=100)
def fetch_events_cached(adapter_key, sport, commence_time_hour):
    # Cache key includes hour bucket to auto-expire
    return adapters[adapter_key].fetch_events(sport)

# Smart refresh
def should_refresh(event_commence_time):
    now = datetime.utcnow()
    commence = datetime.fromisoformat(event_commence_time)
    hours_until = (commence - now).total_seconds() / 3600
    
    if hours_until < 2:
        return True  # Refresh frequently near start
    if hours_until < 24:
        return now.minute % 10 == 0  # Every 10 min
    return now.minute == 0  # Hourly for far events
```

---

## Data Quality

### Validation

Before merging scraped data:

```python
def validate_outcome(outcome):
    # Price sanity checks
    if outcome.price < 1.01 or outcome.price > 1000:
        return False
    
    # Point value checks (for spreads/totals)
    if outcome.point is not None:
        if abs(outcome.point) > 100:  # Unrealistic line
            return False
    
    return True
```

### Monitoring

Track these metrics per adapter:

```python
metrics = {
    "sportsbet": {
        "requests_made": 0,
        "requests_failed": 0,
        "events_fetched": 0,
        "events_matched": 0,
        "avg_response_time_ms": 0,
    }
}
```

Alert on:
- Failure rate > 20%
- Response time > 5 seconds
- Zero events fetched for 3+ consecutive runs

---

## Troubleshooting

### Issue: No scraped events matching

**Cause**: Team name mismatch or time window too narrow

**Fix**:
```python
# Increase time tolerance
merged = merge_odds_data(primary, scraped, time_tolerance_minutes=60)

# Debug fuzzy matching
from core.scrape_sources.merger import fuzzy_match_team
print(fuzzy_match_team("LA Lakers", "Los Angeles Lakers"))  # Should be True
```

### Issue: Rate limit errors (429 responses)

**Cause**: Too many requests

**Fix**:
```python
# Reduce rate limit
adapter = SportsbetAdapter()
adapter.rate_limiter = RateLimiter(max_requests=20, period_seconds=60)

# Or increase period
adapter.rate_limiter = RateLimiter(max_requests=30, period_seconds=120)
```

### Issue: Schema changes (API returns unexpected format)

**Cause**: Bookmaker updated their API

**Fix**:


1. Inspect network tab in browser (visit bookmaker site)
2. Update adapter parsing logic
3. Add schema version detection if possible:

```python
def _parse_event(self, raw: Dict):
    schema_version = raw.get("_schema_version", "v1")
    if schema_version == "v2":
        return self._parse_event_v2(raw)
    return self._parse_event_v1(raw)
```

### Issue: Duplicate odds entries

**Cause**: Merger not detecting existing bookmaker

**Fix**:


- Check `bookmaker_key` consistency (e.g., "pointsbetau" vs "pointsbet")
- Ensure merger checks `bk.get("key")` not `bk.get("title")`

---

## Performance Optimization

### Parallel Fetching

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all_parallel(adapters, sport, markets):
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(adapter.fetch_events, sport, markets): adapter
            for adapter in adapters
        }
        for future in as_completed(futures):
            try:
                events = future.result(timeout=15)
                results.extend(events)
            except Exception as e:
                adapter = futures[future]
                print(f"[Error] {adapter.bookmaker_key}: {e}")
    return results
```

### Selective Scraping

Don't scrape all sports/markets:

```python
# Only scrape for high-value opportunities
def should_scrape(sport, market):
    # Example: only scrape NBA h2h and player props
    if sport == "basketball_nba" and market in ["h2h", "player_points"]:
        return True
    # Only scrape AFL spreads/totals
    if sport == "aussierules_afl" and market in ["spreads", "totals"]:
        return True
    return False
```

---

## Legal & Ethical Considerations

### Do's

✅ Respect rate limits (built-in to adapters)
✅ Use clear user-agent identifying your bot
✅ Cache responses to minimize requests
✅ Only fetch public, non-authenticated endpoints
✅ Follow robots.txt (if present)

### Don'ts

❌ Reverse-engineer encrypted/obfuscated protocols
❌ Bypass anti-bot mechanisms
❌ Hammer endpoints (risk IP blocking)
❌ Scrape personal user data or account-restricted info
❌ Violate site Terms of Service

### User-Agent

Update in each adapter:

```python
self.session.headers.update({
    "User-Agent": f"EVisionBot/1.0 (+{os.getenv('SCRAPE_CONTACT_EMAIL')})",
})
```

---

## Testing

### Unit Test Template

```python
import pytest
from core.scrape_sources.sportsbet import SportsbetAdapter

def test_sportsbet_fetch():
    adapter = SportsbetAdapter()
    events = adapter.fetch_events("basketball_nba", ["h2h"])
    
    assert len(events) > 0
    assert events[0].bookmaker_key == "sportsbet"
    assert events[0].home_team
    assert events[0].away_team

def test_rate_limiter():
    from core.scrape_sources.rate_limiter import RateLimiter
    limiter = RateLimiter(max_requests=2, period_seconds=1)
    
    assert limiter.acquire(block=False) == True
    assert limiter.acquire(block=False) == True
    assert limiter.acquire(block=False) == False  # Exhausted
```

### Integration Test

```bash
# Test live (careful with rate limits)
python -c "
from core.scrape_sources.sportsbet import SportsbetAdapter
adapter = SportsbetAdapter()
events = adapter.fetch_events('basketball_nba', ['h2h'])
print(f'Fetched {len(events)} events')
for e in events[:2]:
    print(f'{e.home_team} vs {e.away_team}')
"
```

---

## Deployment

### Production Checklist

- [ ] Set `ENABLE_SCRAPE_SOURCES=1` in production `.env`
- [ ] Add `SCRAPE_CONTACT_EMAIL` for user-agent
- [ ] Configure caching layer (Redis recommended)
- [ ] Set up monitoring/alerts for adapter failures
- [ ] Test with small subset before full rollout
- [ ] Document which bookmakers are scraped in logs/dashboard
- [ ] Implement circuit breaker for failing adapters
- [ ] Schedule periodic schema validation checks

### Rollout Strategy

1. **Week 1**: Enable Sportsbet only, monitor for issues
2. **Week 2**: Add TAB if Sportsbet stable
3. **Week 3**: Add PointsBet if both stable
4. **Ongoing**: Monitor coverage improvements and EV hit rate

---

## Maintenance

### Weekly Tasks

- Check adapter success rates (aim for >90%)
- Review unmatched events (merger couldn't find primary event)
- Validate schema still correct (spot-check 5-10 events)

### Monthly Tasks

- Update sport/competition mappings (new seasons start)
- Review rate limits (adjust if seeing 429 errors)
- Benchmark coverage improvement (% of AU books with data)

### As-Needed

- Fix schema breaking changes (bookmaker API updates)
- Add new bookmakers (prioritize by EV contribution)
- Remove dead/unreliable sources

---

## Support

For issues or questions:

1. Check troubleshooting section above
2. Inspect network tab for schema changes
3. Test adapter in isolation before full integration
4. Review merger logs for matching issues

Example debug:

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test single adapter
adapter = SportsbetAdapter()
events = adapter.fetch_events("basketball_nba", ["h2h"])
print(f"Fetched {len(events)} events")
for e in events:
    print(f"{e.id}: {e.home_team} vs {e.away_team} ({len(e.markets)} markets)")
```

---

## Roadmap

Potential future enhancements:

- **Betfair Exchange adapter**: Live odds + liquidity indicators
- **More AU bookmakers**: BetRight, BoomBet, Neds, Dabble
- **Live odds tracking**: Detect rapid line movements
- **Market-specific adapters**: Focus on player props (Sportsbet has good prop coverage)
- **Schema versioning**: Auto-detect and handle API changes
- **Distributed rate limiting**: Share tokens across multiple bot instances

---

## Summary

You now have a production-ready scrape sources package that:

✅ Supplements The Odds API with 3 major AU bookmakers  
✅ Handles rate limiting, caching, and deduplication  
✅ Merges seamlessly with primary odds data  
✅ Is extensible for adding new bookmakers  

Enable with `ENABLE_SCRAPE_SOURCES=1` and monitor coverage improvements!
