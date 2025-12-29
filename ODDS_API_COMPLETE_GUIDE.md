# ODDS API V4 - COMPLETE ENDPOINTS GUIDE FOR NBA
**Based on Official API Documentation** | December 29, 2025

---

## Key Findings

### What We're Missing

From the API docs, we can fetch **multiple market types per request**:

```
GET /v4/sports/basketball_nba/odds?regions=au,us,us2,eu&markets=h2h,spreads,totals&oddsFormat=decimal
```

**This single request gets:**
- ✅ Head-to-head (moneyline)
- ✅ Spreads (point spreads) 
- ✅ Totals (over/under)

**What we're NOT capturing yet:**
- ❌ Player props (`player_points`, `player_assists`, `player_rebounds`, etc.)
- ❌ Alternate spreads/totals
- ❌ Quarter/half specific markets
- ❌ Other player prop combinations

---

## Three Main Approaches

### APPROACH 1: Main Odds Endpoint (Current - Basic)
```
GET /v4/sports/basketball_nba/odds
Parameters: regions, markets, oddsFormat
Cost: 1 credit per market per region
Best for: h2h, spreads, totals (3 markets x 4 regions = 12 credits)
Data: All bookmakers, all points
```

**What we're doing:** ✅ This is what `extract_nba_v3.py` uses
**Coverage:** All basic markets (h2h, spreads, totals)

---

### APPROACH 2: Event-Level Detailed Markets (NEW)
```
GET /v4/sports/basketball_nba/events/{eventId}/markets
Parameters: regions
Cost: 1 credit per call
Best for: Discovering ALL available markets for an event BEFORE fetching odds
Data: List of market keys available (like: player_points, player_assists, etc.)
```

**Use case:** First call this to see what markets are available, then fetch specific ones

**Example response structure:**
```json
{
  "bookmakers": [
    {
      "key": "fanduel",
      "markets": [
        "h2h",
        "spreads",
        "totals",
        "player_points",
        "player_assists",
        "player_rebounds",
        ...all available markets
      ]
    }
  ]
}
```

---

### APPROACH 3: Event-Specific Odds (FOR PLAYER PROPS)
```
GET /v4/sports/basketball_nba/events/{eventId}/odds
Parameters: markets (specify player props), regions, oddsFormat
Cost: [number of unique markets returned] x [number of regions]
Best for: Player props and alternate markets
Data: Detailed odds structure with description field (player name in props)
```

**Example request:**
```
/v4/sports/basketball_nba/events/{eventId}/odds
  ?markets=player_points,player_assists,player_rebounds
  &regions=us,au,eu
  &oddsFormat=decimal
```

**Example response for player props:**
```json
{
  "bookmakers": [
    {
      "key": "fanduel",
      "markets": [
        {
          "key": "player_points",
          "outcomes": [
            {
              "name": "Over",
              "description": "Giannis Antetokounmpo",
              "price": 1.90,
              "point": 28.5
            },
            {
              "name": "Under",
              "description": "Giannis Antetokounmpo",
              "price": 1.90,
              "point": 28.5
            },
            ...more players...
          ]
        }
      ]
    }
  ]
}
```

---

## Complete Data Collection Strategy

### Step 1: Basic Markets (Current - Keep as is)
```python
# Costs: 3 credits (h2h, spreads, totals × 1 region group)
GET /v4/sports/basketball_nba/odds
  ?regions=au,us,us2,eu
  &markets=h2h,spreads,totals
  &oddsFormat=decimal
```

**Returns:** All spreads/totals with all variations preserved ✅

---

### Step 2: Discover Available Markets (NEW)
For EACH event, call once:
```python
# Cost: 1 credit per event
GET /v4/sports/basketball_nba/events/{eventId}/markets
  ?regions=us  # Just check US to save credits
```

**Output:** List of market keys available for that event
**Use:** Determine which player props are available before fetching

---

### Step 3: Fetch Player Props (NEW - Optional)
```python
# Cost: Varies based on what's available
# Example: 5 player prop markets × 1 region = 5 credits
GET /v4/sports/basketball_nba/events/{eventId}/odds
  ?markets=player_points,player_assists,player_rebounds,player_blocks,player_steals
  &regions=us
  &oddsFormat=decimal
```

**Why this works:**
- Player name is in `description` field
- All point values preserved
- All bookmakers included
- Simple to parse

---

## What extract_nba_v3.py Is Currently Doing

**✅ EXACT CODE (from extract_nba_v3.py, line 322-338):**

```python
def _fetch_odds(self, event_id: str) -> Dict:
    """Fetch odds for single event."""
    url = f"{API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"
    params = {
        "apiKey": self.api_key,
        "regions": "au,us,us2,eu",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"⚠️  Error fetching odds for {event_id}: {e}")
        return {}
```

**What this means:**
- ✅ Using **EVENT-LEVEL endpoint** (`/events/{eventId}/odds`)
- ✅ Requesting **3 markets**: h2h, spreads, totals
- ✅ From **4 regions**: au, us, us2, eu
- ✅ Getting all bookmakers from each region that support these markets
- ✅ **ALL point variations preserved** (e.g., spreads at -6.5, -7.0, -7.5 all in response)
- ✅ CSV saves with all data intact

**API Cost:**
- Per event: ~3-5 credits (only markets that have data are charged)
- Per run (11 events): ~33-55 credits
- **Status:** ✅ OPTIMAL for current needs

---

## Recommended Implementation

### For MVP (Minimal Viable Product) - THIS IS WHAT WE'RE DOING
**Focus on:** Basic markets only (what we have now)
```
Cost per run: ~3-5 credits per event
Data: h2h, spreads (all points), totals (all points)
Time: ~1-2 min
Result: 226 rows of data (11 events, all variations)
```

✅ **THIS IS ALREADY IMPLEMENTED AND WORKING CORRECTLY**

---

### For Full Implementation (Future)
```
Step 1: Fetch basic markets (3 credits)
  └─→ GET /odds with h2h,spreads,totals

Step 2: For each event, discover available props (11 credits max for 11 events)
  └─→ GET /events/{eventId}/markets
  
Step 3: Fetch player props for popular markets only (varies)
  └─→ GET /events/{eventId}/odds with player_points, player_assists, etc.

Total cost: ~15-30 credits per run (still efficient)
```

---

## Critical API Rules

### ⚠️ Quota Cost Formula
```
cost = [number of markets requested] × [number of regions]

Example:
  3 markets (h2h, spreads, totals) × 4 regions (au,us,us2,eu) = 12 credits

BUT if you query event-level odds:
  cost = [unique markets RETURNED] × [regions specified]
  (only counts markets that have data)
```

### ⚠️ Markets Parameter
- Main `/odds` endpoint: only supports `h2h,spreads,totals,outrights`
- Event `/odds` endpoint: supports **ANY** market (player props, alternate spreads, etc.)

### ⚠️ Response Structure
- Main `/odds`: Returns **all bookmakers, all points**
- Event `/odds`: Returns bookmakers requested, **all points for each market**

---

## What We Should Do Right Now

### Option A: Keep MVP (RECOMMENDED FOR NOW)
```python
# Continue with extract_nba_v3.py
# Get: h2h, spreads (all points), totals (all points)
# Cost: ~3 credits per run
# Benefits: Simple, complete, no wasted API credits
```

✅ **This is what we're doing - it's efficient**

---

### Option B: Add Player Props (FUTURE)
```python
# After MVP is stable, add:
# 1. Call /events/{eventId}/markets for each game
# 2. See what player props are available
# 3. Fetch top 3-5 player prop markets per event
# Cost: +15-25 credits per run
# Benefit: More betting markets available
```

---

## Summary

**Current Status:**
- ✅ We're using the right endpoint (`/odds` with markets parameter)
- ✅ We're preserving all point variations (spreads -6.5, -7.0, -7.5, etc.)
- ✅ We're getting all bookmakers
- ✅ We're NOT missing any main markets (h2h, spreads, totals)

**What we COULD add:**
- Player props (needs event-level endpoint)
- Alternate markets (less liquid, not critical for MVP)

**Recommendation:**
✅ **KEEP CURRENT APPROACH** - it's doing what we need
→ If/when we add player props, use the event `/odds` endpoint with specific market requests
