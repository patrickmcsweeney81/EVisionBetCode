# Quick Test: What You Can See Right Now (Phase 5)

## Backend API Running ✅
```
Status: http://localhost:8000 is LIVE
```

## Test These Endpoints in Your Browser or Terminal

### 1. API Root (All Endpoints)
```
http://localhost:8000/
```
**What You'll See:**
```json
{
  "name": "EV_ARB Bot API",
  "version": "2.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "ev_hits": "/api/ev/hits?limit=50&min_ev=0.01&sport=basketball_nba",
    "ev_summary": "/api/ev/summary",
    "odds_latest": "/api/odds/latest?limit=500&sport=basketball_nba",
    "config_weights": "/api/config/weights",  // ← NEW!
    ...
  }
}
```

### 2. Weight Configuration (NEW!)
```
http://localhost:8000/api/config/weights
```
**What You'll See (Formatted):**
```json
{
  "sports": {
    "basketball_nba": {
      "weights": {
        "pinnacle": 4,
        "betfair": 3,
        "draftkings": 3,
        "fanduel": 3,
        "betfairaus": 2,
        "sportsbet": 1
      },
      "title": "NBA"
    },
    "americanfootball_nfl": {
      "weights": {
        "pinnacle": 4,
        "draftkings": 4,
        "fanduel": 3,
        "betfair": 2
      },
      "title": "NFL"
    }
  },
  "timestamp": "2025-12-26T10:30:00...",
  "note": "These are EVisionBet's hidden weights..."
}
```

### 3. EV Opportunities (Pre-Calculated)
```
http://localhost:8000/api/ev/hits?limit=10&sport=basketball_nba
```
**What You'll See:**
- 10 NBA opportunities ranked by EV%
- Fair odds pre-calculated with EVisionBet weights
- Best odds from different books
- EV percentage (how much edge you have)
- Example: Julian Champagnie Under at 1.97 odds with 11.34% EV

### 4. Health Check
```
http://localhost:8000/health
```
**What You'll See:**
```json
{
  "status": "healthy",
  "backend": "connected",
  "database": "csv_fallback",
  "timestamp": "2025-12-26T..."
}
```

---

## Example: Full Weight Flow (Phase 6 Will Implement This)

### Step 1: Frontend Loads Weights
```javascript
const weights = await fetch('http://localhost:8000/api/config/weights').then(r => r.json());
console.log(weights.sports.basketball_nba.weights);
// {pinnacle: 4, betfair: 3, draftkings: 3, fanduel: 3, betfairaus: 2, sportsbet: 1}
```

### Step 2: Frontend Shows Sliders
```
[ Pinnacle    ] 0 ━━━━━━━◉━━━━━ 4  (User can adjust)
[ Betfair     ] 0 ━━━━━━━━━━━━━ 4
[ DraftKings  ] 0 ━━━━━━━━━━━━━ 4
[ FanDuel     ] 0 ━━━━━━━━━━━━━ 4
[ BetfairAus  ] 0 ━━━━━━━━━━━━━ 4
[ SBet        ] 0 ━━━━━━━━━━━━━ 4
```

### Step 3: User Adjusts Weights
```
[ Pinnacle    ] 0 ━━━━━━━━━━━━◉ 4  ← User moves slider to 3
[ Betfair     ] 0 ━━━━━━━◉━━━━━ 4  ← User moves slider to 2
[ DraftKings  ] 0 ━━━━━━━━━━━━━ 4
[ FanDuel     ] 0 ━━━━━━━━━━━━━ 4
```

### Step 4: Fair Odds Recalculated
```
Backend:  Fair Odds = 1.7693 (EVisionBet weighted)
          EV% = 11.34%

User:     Fair Odds = 1.7812 (with your weights)
          EV% = 10.89%
          
Difference: -0.45% (slightly lower edge with your preferences)
```

### Step 5: Frontend Shows Comparison
```
┌─────────────────────────────────────────────┐
│ Julian Champagnie Under                     │
│ New York Knicks vs San Antonio Spurs        │
├─────────────────────────────────────────────┤
│                                             │
│ Backend (EVisionBet)      Your Calculation  │
│ Fair: 1.7693              Fair: 1.7812     │
│ EV%:  11.34%              EV%:  10.89%     │
│                                             │
│ [Place Bet]               [Adjust Weights] │
└─────────────────────────────────────────────┘
```

---

## Current Architecture Files (What Exists)

### Configuration (src/v3/configs/)
✅ `sports.py` - Master sports config (NBA, NFL enabled)
✅ `weights.py` - EVisionBet hidden weights per sport
✅ `bookmakers.py` - 10+ bookmakers with star ratings
✅ `fair_odds.py` - Per-sport outlier & sharp config
✅ `regions.py` - Per-sport region selection
✅ `api_tiers.py` - Tier 1/2/3 strategy per sport
✅ `__init__.py` - Config package

### Fair Odds Classes (src/v3/processors/)
✅ `fair_odds_nba.py` - NBA logic (5% outlier, min 2 sharps)
✅ `fair_odds_nfl.py` - NFL logic (3% outlier, min 1 sharp)

### Extractors (src/v3/extractors/)
✅ `base_extractor.py` - Config-aware base class
✅ `nba_extractor.py` - NBA extraction (config-driven)
✅ `nfl_extractor.py` - NFL extraction (config-driven)

### Backend API
✅ `backend_api.py` - FastAPI with 3+ endpoints
✅ NEW: `/api/config/weights` endpoint
✅ `/api/ev/hits` - Pre-calculated opportunities
✅ `/api/odds/raw` - Raw odds for recalculation

### Documentation (docs/)
✅ `BACKEND_API_V3.md` - API reference
✅ `API_TESTING_GUIDE.md` - Testing commands
✅ `FRONTEND_DEVELOPER_REFERENCE.md` - React examples
✅ `PHASE_5_COMPLETION.md` - Build summary
✅ `PHASE_5_COMPLETE.md` - Detailed report
✅ `PHASES_1_TO_5_COMPLETE.md` - Full overview

---

## What's Ready for Frontend Dev (Phase 6)

### You Have:
1. ✅ Weight configuration (`/api/config/weights`)
2. ✅ Pre-calculated EV hits (`/api/ev/hits`)
3. ✅ Raw odds for recalculation (`/api/odds/raw`)
4. ✅ Fair odds calculation examples (in docs)
5. ✅ React component examples (in docs)

### Frontend Can Now:
- Load weight config from API
- Display weight sliders
- Recalculate fair odds on weight change
- Show live EV% updates
- Compare backend vs user-calculated EV

---

## How to Test Everything

### Option 1: Browser
Just visit:
- http://localhost:8000/api/config/weights
- http://localhost:8000/api/ev/hits?limit=10
- http://localhost:8000/api/odds/raw?limit=20

### Option 2: PowerShell
```powershell
# Test weights config
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/config/weights" -UseBasicParsing
($response.Content | ConvertFrom-Json).sports | ConvertTo-Json

# Test EV hits
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/ev/hits?limit=5" -UseBasicParsing
($response.Content | ConvertFrom-Json).hits | Select-Object selection,ev_percent | ConvertTo-Json
```

### Option 3: JavaScript Console
```javascript
// In browser console (http://localhost:8000/)
fetch('/api/config/weights').then(r => r.json()).then(d => console.log(d.sports))
fetch('/api/ev/hits?limit=5').then(r => r.json()).then(d => console.log(d.hits.length + ' hits'))
```

---

## What's Happening Behind the Scenes

### When You Load `/api/config/weights`:
1. Backend loads `src/v3/configs/sports.py`
2. Gets all enabled sports (NBA, NFL)
3. For each sport, loads `evisionbet_weights` from config
4. Returns to frontend as JSON
5. Frontend displays as weight sliders (0-4 range, default 0)

### When Frontend Recalculates EV:
1. User adjusts slider for a bookmaker
2. Frontend gets new weight value (0-4)
3. Normalizes all weights (sum to 1.0)
4. Gets raw odds from `/api/odds/raw`
5. Calculates weighted fair odds (same formula as backend)
6. Calculates new EV% = (fair × best - 1) × 100
7. Updates display with new numbers

### Backend Pre-Calculation Flow:
1. Pipeline extracts raw odds
2. Loads fair odds config per sport
3. Loads EVisionBet weights per sport
4. Calculates fair odds with EVisionBet weights
5. Calculates EV% with fair odds
6. Saves to CSV/DB
7. Backend serves via `/api/ev/hits`
8. Frontend displays (users can recalculate with different weights)

---

## Summary of What You Can See Now

✅ **Backend API running and healthy**
✅ **Weight config accessible** (`/api/config/weights`)
✅ **EV opportunities available** (106+ in database)
✅ **Pre-calculated fair odds working**
✅ **All endpoints documented**
✅ **Frontend can load and use weights**

🚀 **Ready for Phase 6: Frontend weight slider component**

---

## One-Click Test

Open your browser and visit:
```
http://localhost:8000/api/config/weights
```

If you see this, Phase 5 is ✅ working:
```json
{
  "sports": {
    "basketball_nba": {
      "weights": { ... },
      "title": "NBA"
    }
  }
}
```

---

That's it! The foundation is built. Frontend dev can now build the UI components using the API responses documented in the docs.

Next: Phase 6 (Frontend) or Phase 7 (Pipeline)
