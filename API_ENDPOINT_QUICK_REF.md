# QUICK REFERENCE: API ENDPOINTS COMPARISON
**Which endpoint to use and why**

---

## The Three Odds Endpoints

### 1. MAIN ODDS ENDPOINT
```
GET /v4/sports/basketball_nba/odds
```

**Parameters:**
```
regions=au,us,us2,eu
markets=h2h,spreads,totals,outrights
oddsFormat=decimal
```

**Returns:** All available odds for sport across all regions

**Markets Supported:** Only h2h, spreads, totals, outrights (no player props)

**Pros:**
- Single call for ALL events
- Simple response structure

**Cons:**
- Limited market types
- Can't request player props
- Larger response (all events at once)

**Cost:** ~1 credit if you get all 3 markets back

---

### 2. EVENT-LEVEL ODDS (⭐ WHAT WE USE)
```
GET /v4/sports/basketball_nba/events/{eventId}/odds
```

**Parameters:**
```
regions=au,us,us2,eu
markets=h2h,spreads,totals
oddsFormat=decimal
```

**Returns:** Odds for ONE specific event

**Markets Supported:** h2h, spreads, totals, outrights, player_*, alternate_*, period markets, etc.

**Pros:**
- ✅ Supports ANY market type
- ✅ Can request player props
- ✅ We currently use this
- ✅ Flexible for future enhancement
- Good for per-event processing

**Cons:**
- Requires multiple calls (one per event)
- More complex response

**Cost:** ~3-5 credits per event (cost = markets returned × regions)

---

### 3. MARKETS DISCOVERY
```
GET /v4/sports/basketball_nba/events/{eventId}/markets
```

**Parameters:**
```
regions=us
```

**Returns:** List of market keys available for an event

**Example Response:**
```json
{
  "bookmakers": [
    {
      "key": "fanduel",
      "markets": ["h2h", "spreads", "totals", "player_points", "player_assists", ...]
    }
  ]
}
```

**Use Case:** Discover what's available BEFORE fetching odds

**Cost:** ~1 credit per event

---

## Side-By-Side Comparison

| Feature | Main Odds | Event Odds | Markets List |
|---------|-----------|-----------|--------------|
| **Multiple Events** | ✅ Yes | ❌ No (one per call) | ❌ No (one per call) |
| **Player Props** | ❌ No | ✅ Yes | ✅ Lists them |
| **Spread Points** | ✅ All | ✅ All | - |
| **Bookmakers** | ✅ All | ✅ All | ✅ Lists only |
| **Single Call Efficiency** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Market Flexibility** | ⭐ Limited | ⭐⭐⭐ Full | - |
| **Typical Cost per Run** | 3-5 credits | 30-55 credits | 11-15 credits |

---

## Our Current Strategy

```
STEP 1: Fetch all events
GET /v4/sports/basketball_nba/events
  (no markets param - just lists games)

STEP 2: For each event, fetch odds
GET /v4/sports/basketball_nba/events/{eventId}/odds
  ?markets=h2h,spreads,totals
  &regions=au,us,us2,eu
  &oddsFormat=decimal

STEP 3: Process and save to CSV
- Parse all bookmakers
- Preserve all point variations
- Create row per unique (market, selection, point)

COST: ~40-50 credits per run (11 events × 3-5 credits)
DATA: 226 rows, all variations, all bookmakers
```

✅ **This is optimal for current MVP**

---

## If We Add Player Props

```
STEP 1-2: Same as above
  (fetch events, fetch event odds)

STEP 3: For each event, ALSO fetch player props
GET /v4/sports/basketball_nba/events/{eventId}/odds
  ?markets=player_points,player_assists,player_rebounds
  &regions=us
  &oddsFormat=decimal

STEP 4: Process both regular + player props
- Combine regular market rows
- Add player prop rows (sparse, only if bookmaker has it)
- Create row per unique (market, player_name, point)

COST: ~70-90 credits per run (add +30 for player props)
DATA: ~400-500 rows (regular + player props)
```

⏸️ **Would do this only if user requests player betting opportunities**

---

## Decision Matrix

**Use MAIN ODDS endpoint if:**
- Need all events in single call
- Only want h2h, spreads, totals
- Want maximum efficiency

**Use EVENT ODDS endpoint if:** ✅ (This is us)
- Processing events individually anyway
- Want flexibility for player props later
- Can afford multiple API calls

**Use MARKETS DISCOVERY if:**
- Want to list "what's available" before deciding
- Building a market explorer UI
- Optimizing for only available props (save quota)

---

**Conclusion:** We're using the right endpoint ✅
