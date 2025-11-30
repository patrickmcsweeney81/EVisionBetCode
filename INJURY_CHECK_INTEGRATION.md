# Injury Check Integration Guide

## Overview

This module provides **trigger-only** injury checks across 3 free data sources for NBA, NFL, and NHL player props:

1. **BALLDONTLIE** (NBA only, always free)
2. **TheSportsDB** (multi-league, free tier)
3. **API-SPORTS** (multi-league, free tier with rate limits)

**Zero API costs** — all sources are free or nearly free.  
**No rate-limit burn** — only called on demand (user click or high-EV bot trigger).  
**Triple-redundancy accuracy** — consensus logic merges all 3 sources.

---

## Architecture

### Backend Integration (Recommended)

Place injury check logic in your **backend** (`backend-python/`), not the bot:

- **Security**: Centralize API keys (`API_SPORTS_KEY`, optional `THESPORTSDB_API_KEY`).
- **Reliability**: Add retries, timeouts, circuit breakers.
- **Efficiency**: Cache recent responses (2–5 min TTL) to avoid duplicate calls.
- **Consistency**: One canonical consensus endpoint for UI and bot.

### Bot Integration

When the bot finds a **high-EV player prop**, POST the player + league to the backend:

```python
# Inside ev_arb_bot.py or player_props_handler.py
import requests

def notify_high_ev_prop(player_name: str, league: str, ev_percent: float, ...):
    # Existing notification logic
    ...
    
    # Trigger injury check via backend
    try:
        resp = requests.post(
            "http://localhost:8000/api/injury-check",
            json={"player": player_name, "league": league},
            timeout=10
        )
        if resp.ok:
            injury_data = resp.json()
            # Attach to Telegram/Discord notification or logs
            print(f"Injury check: {injury_data['confidence']} confidence — {injury_data['injury_status']}")
    except Exception as e:
        print(f"Injury check skipped: {e}")
```text

**Key principle**: Bot remains EV-first; injury check is an enrichment, not a blocker.

---

## Files to Copy

### 1. Core Module

**Source**: `injury_check.py` (generated above)  
**Destination**: `backend-python/app/injury_check.py`

Contains:

- `check_injury(player, league)` — main entry point
- `query_balldontlie(player)` — NBA-only source
- `query_thesportsdb(player, league)` — multi-league source
- `query_apisports(player, league)` — multi-league source
- `merge_results(...)` — consensus logic with confidence rating

### 2. FastAPI Endpoint

**Source**: `injury_check_endpoint.py` (generated above)  
**Destination**: `backend-python/app/routers/injury.py` (or integrate into existing router)

Example integration into `main.py`:

```python
from app.routers.injury import router as injury_router

app.include_router(injury_router, prefix="/api", tags=["injury"])
```text

---

## API Reference

### Endpoint

```http
POST /api/injury-check
```

### Request Body


```json
{
  "player": "Neemias Queta",
  "league": "NBA"
}
```text

### Response

```json
{
  "injury_status": "QUESTIONABLE",
  "injury_detail": "Right ankle",
  "last_updated": "2025-11-29 12:34:56",
  "confidence": "HIGH",
  "sources": [
    {
      "source": "BALLDONTLIE",
      "status": "QUESTIONABLE",
      "detail": null,
      "last_updated": "2025-11-29 12:34:56"
    },
    {
      "source": "TheSportsDB",
      "status": "QUESTIONABLE",
      "detail": "Right ankle",
      "last_updated": "2025-11-29 12:34:56"
    },
    {
      "source": "API-SPORTS",
      "status": "QUESTIONABLE",
      "detail": "Ankle injury",
      "last_updated": "2025-11-29 12:30:00"
    }
  ],
  "note": null
}
```text

### Confidence Levels

- **HIGH**: All 3 sources agree
- **MEDIUM**: 2 sources agree
- **LOW**: All sources disagree or < 2 sources returned data

### Note Field

When sources conflict:
```json
{
  "note": "Conflicting reports — double check before betting"
}
```text

---

## Environment Variables

Add to `backend-python/.env`:

```bash
# Optional: API-SPORTS key (free tier available)
API_SPORTS_KEY=your_key_here

# Optional: TheSportsDB key (public demo key "2" works, or upgrade)
THESPORTSDB_API_KEY=2
```

**BALLDONTLIE** requires no key.

---

## UI Integration

### Frontend Button

When user clicks "Check Injury" on a player prop:

```javascript
async function checkInjury(player, league) {
  const response = await fetch('/api/injury-check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player, league })
  });
  
  const data = await response.json();
  
  // Display to user
  displayInjuryStatus(data);
}
```

### Example UI Display

```
Injury Status: QUESTIONABLE
Injury: Right ankle
Last Updated: 4 min ago

Sources:
✔ BALLDONTLIE
✔ API-SPORTS
✔ TheSportsDB

Confidence: HIGH
```

If conflicting:
```
⚠ Conflicting reports — double check before betting
```

---

## Bot Trigger Logic

### Recommended Flow

1. Bot detects high-EV player prop (e.g., EV > 5%)
2. Before sending notification, POST to `/api/injury-check`
3. If response indicates `OUT` or `QUESTIONABLE`, append warning to notification
4. If `ACTIVE`, proceed normally

### Example Bot Code

```python
def log_player_prop_ev(player, market, odds, fair, ev_pct, league):
    # Existing logging
    ...
    
    # Trigger injury check for high-EV
    if ev_pct >= 5.0:
        injury = check_injury_via_backend(player, league)
        if injury and injury.get("injury_status") in ("OUT", "QUESTIONABLE"):
            print(f"⚠ {player} injury: {injury['injury_status']} — {injury['injury_detail']}")
            # Append to Telegram message or skip notification
```

---

## Caching Strategy

### Backend Cache (Recommended)

Use in-memory cache (e.g., `cachetools` or Redis) with **2–5 min TTL**:

```python
from cachetools import TTLCache
import hashlib

injury_cache = TTLCache(maxsize=1000, ttl=180)  # 3 min

def check_injury_cached(player: str, league: str):
    cache_key = hashlib.md5(f"{player}:{league}".encode()).hexdigest()
    if cache_key in injury_cache:
        return injury_cache[cache_key]
    
    result = check_injury(player, league)
    injury_cache[cache_key] = result
    return result
```

### Why Cache?

- Same player often appears in multiple props (O/U points, rebounds, assists)
- User may click "Check Injury" multiple times within short window
- Bot may detect multiple EV hits for same player

---

## Rate Limit Management

### API-SPORTS Free Tier

- ~100 requests/day (varies by sport)
- Use as **final confirmation** source, not primary

### Strategy

1. Always call BALLDONTLIE + TheSportsDB first (unlimited/generous)
2. Only call API-SPORTS if first two disagree or return `None`
3. Circuit breaker: If API-SPORTS fails 3+ times in 5 min, skip for next 30 min

---

## Testing

### Manual Test

```bash
cd backend-python
python -c "from app.injury_check import check_injury; import json; print(json.dumps(check_injury('Neemias Queta', 'NBA'), indent=2))"
```

Expected output:

```json
{
  "injury_status": "ACTIVE",
  "injury_detail": null,
  "last_updated": "2025-11-29 12:34:56",
  "confidence": "MEDIUM",
  "sources": [...]
}
```

### FastAPI Test

Start backend:

```bash
cd backend-python
python manage.py runserver
```

Test endpoint:

```bash
curl -X POST http://localhost:8000/api/injury-check \
  -H "Content-Type: application/json" \
  -d '{"player": "Neemias Queta", "league": "NBA"}'
```

---

## Deployment Checklist

- [ ] Copy `injury_check.py` to `backend-python/app/`
- [ ] Copy endpoint to `backend-python/app/routers/injury.py`
- [ ] Add router to `main.py`
- [ ] Add `API_SPORTS_KEY` to `.env` (optional)
- [ ] Add `THESPORTSDB_API_KEY` to `.env` (optional, default "2" works)
- [ ] Add `requests` to `requirements.txt` (likely already present)
- [ ] Test with manual script (see above)
- [ ] Test endpoint with curl/Postman
- [ ] Add caching layer (optional but recommended)
- [ ] Wire bot to call endpoint on high-EV props
- [ ] Wire UI button to call endpoint

---

## Monitoring

Track these metrics:

- **Source availability**: % of successful responses per source
- **Conflict rate**: % of checks with conflicting statuses
- **Response time**: P95 latency per source
- **Cache hit rate**: % of requests served from cache

Alert on:

- API-SPORTS 429 (rate limit) → pause for 30 min
- All sources failing → investigate network/keys
- High conflict rate (>20%) → review normalization logic

---

## Future Enhancements

1. **Webhook subscriptions**: Instead of polling, subscribe to injury updates (if sources offer)
2. **Historical tracking**: Log injury status changes over time
3. **Correlation analysis**: Track EV hit accuracy vs. injury status
4. **Smart throttling**: Reduce checks for players marked `ACTIVE` recently
5. **Multi-source fallback**: If 2 sources are down, still return result with `LOW` confidence

---

## Cost Summary

| Source | NBA | NFL | NHL | Cost | Rate Limit |
|--------|-----|-----|-----|------|------------|
| BALLDONTLIE | ✔ | ✘ | ✘ | **FREE** | Generous |
| TheSportsDB | ✔ | ✔ | ✔ | **FREE** ($9/mo pro optional) | 30 req/min |
| API-SPORTS | ✔ | ✔ | ✔ | **FREE** tier available | ~100/day per sport |

**Total monthly cost**: $0 (can scale to $9/mo for faster TheSportsDB)

---

## Support

For questions or issues:

1. Check source API docs (links in `injury_check.py`)
2. Verify API keys in `.env`
3. Test individual source functions in isolation
4. Check rate limit status in API-SPORTS dashboard
