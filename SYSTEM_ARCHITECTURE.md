# EVision Betting System - Architecture & Setup Guide

**Last Updated:** December 10, 2025  
**Status:** Ready for Backend Deployment (Render)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVISION BETTING SYSTEM                        │
└─────────────────────────────────────────────────────────────────────┘

BACKEND (Render - Auto-Running)
├─ pipeline_v2/extract_odds.py      [Periodic] Fetch all sports odds
├─ core handlers (h2h, spreads, etc) [Periodic] Calculate fair prices
├─ pipeline_v2/calculate_opportunities.py [Periodic] Find EV opportunities
└─ PostgreSQL Database              [Persistent] Store all odds + calcs

LOCAL/RENDER CSV OUTPUT
├─ data/raw_odds_pure.csv           All 40 bookmakers × all sports
├─ data/ev_opportunities.csv        EV hits only (threshold >= 1%)
└─ [Mobile Git edits on GitHub app]  Push any config changes

FRONTEND (EVisionBetSite)
├─ Dashboard Card 1: "All Odds"      Display all bookmaker odds
├─ Dashboard Card 2: "EV Hits"       Display calculated opportunities
├─ Dashboard Card 3: [Other]         ...
└─ Data Source: Render PostgreSQL    Real-time data from backend

MOBILE
└─ GitHub App                        Edit config files on the go
```

---

## Component Breakdown

### 1. BACKEND PIPELINE (Render - Auto-Scheduled)

#### Stage 1: Extract Raw Odds
**File:** `pipeline_v2/extract_odds.py`  
**Runs:** Periodically (recommend: every 30 min during game hours)  
**Input:** The Odds API v4  
**Output:** 
- `data/raw_odds_pure.csv` (wide format, one row per market)
- PostgreSQL `live_odds` table (if DB configured)

**Configured Sports:** NBA, NBL, NFL (expand as needed)  
**Configured Regions:** AU, EU, US, US2  
**Configured Markets:** h2h, spreads, totals, player_props  
**Configured Bookmakers:** ~40 books (see config.py)

#### Stage 2: Calculate EV Opportunities
**File:** `pipeline_v2/calculate_opportunities.py`  
**Runs:** After Stage 1 completes  
**Input:** `data/raw_odds_pure.csv` + `live_odds` table  
**Output:**
- `data/ev_opportunities.csv` (opportunities >= 1% EV)
- PostgreSQL `ev_opportunities` table
- Used by frontend for "EV Hits" card

**Uses:**
- `core/fair_prices.py` → `build_fair_prices_two_way()`
- `core/book_weights.py` → Weighted fair odds calculation
- `core/ratings.py` → Bookmaker 1-4 star ratings

### 2. DATABASE (PostgreSQL on Render)

**Tables to Create:**
```sql
-- All odds (latest from all extractions)
CREATE TABLE live_odds (
    id SERIAL PRIMARY KEY,
    extracted_at TIMESTAMP,
    sport VARCHAR(50),
    event_id VARCHAR(100),
    market VARCHAR(50),
    selection VARCHAR(100),
    bookmaker VARCHAR(50),
    odds DECIMAL(10,2),
    ...
    INDEX(event_id, market, bookmaker)
);

-- Calculated EV opportunities
CREATE TABLE ev_opportunities (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP,
    sport VARCHAR(50),
    event_id VARCHAR(100),
    market VARCHAR(50),
    selection VARCHAR(100),
    fair_odds DECIMAL(10,2),
    best_odds DECIMAL(10,2),
    best_book VARCHAR(50),
    ev_percent DECIMAL(5,2),
    ...
    INDEX(detected_at, sport)
);
```

### 3. FRONTEND (EVisionBetSite)

#### Card 1: "All Odds" (Dashboard)
**Data Source:** PostgreSQL `live_odds` table  
**Displays:**
- All bookmaker odds for each market
- Latest extraction timestamp
- Bookmaker count per market
- Regions: AU, EU, US, US2

**Implementation:**
```javascript
// Fetch from backend API (Render)
GET /api/odds/latest?sport=basketball_nba&market=h2h
Returns: { bookmakers: [...], timestamp: ... }
```

#### Card 2: "EV Hits" (Dashboard)
**Data Source:** PostgreSQL `ev_opportunities` table  
**Displays:**
- Calculated EV opportunities
- Fair odds vs best odds
- EV percentage
- Recommended stake (Kelly calculation)
- Last updated timestamp

**Implementation:**
```javascript
// Fetch from backend API (Render)
GET /api/opportunities/current?sport=basketball_nba
Returns: { opportunities: [...], count: ... }
```

### 4. LOCAL CSV BACKUP (Your Computer)

**When System Runs:**
- If you're online: `extract_odds.py` writes to `data/raw_odds_pure.csv`
- If you're online: `calculate_opportunities.py` writes to `data/ev_opportunities.csv`
- Frontend reads from Render PostgreSQL
- You can analyze CSVs locally for testing/validation

---

## Configuration Files

### Core Configuration
**File:** `core/config.py`  
**Purpose:** Centralized bookmaker lists, AU/US/EU definitions  
**Key Settings:**
```python
AU_BOOKIES = ["sportsbet", "tab", "neds", "pointsbetau", ...]  # AU target books
US_BOOKIES = ["draftkings", "fanduel", "caesars", ...]
SHARP_BOOKIES = ["pinnacle", "betfair_ex_eu", "draftkings", ...]  # Fair price sources
CSV_HEADERS = [list of 40+ bookmakers]  # CSV column order
```

### Bookmaker Ratings
**File:** `core/book_weights.py`  
**Purpose:** 1-4 star ratings for fair price weighting  
**Your Configuration:**
```python
BOOKMAKER_RATINGS = {
    "pinnacle": 4,           # Primary sharp
    "betfair_ex_eu": 3,      # Strong
    "draftkings": 3,         # Strong
    "fanduel": 3,            # Strong
    # ... etc for all 40 books
}
```

### Pipeline Configuration
**File:** `.env`  
**Purpose:** API keys, regions, markets, thresholds  
**Your Settings:**
```bash
ODDS_API_KEY=81d1ac74594d5d453e242c14ad479955
REGIONS=au,us,eu,us2
MARKETS=h2h,spreads,totals
SPORTS=basketball_nba,basketball_nbl,americanfootball_nfl
EV_MIN_EDGE=0.03              # 3% minimum edge (adjust as needed)
LINE_TOLERANCE=0.25           # Half-point matching tolerance
```

---

## Deployment Flow

### Phase 1: Local Testing ✅
1. Run `pipeline_v2/extract_odds.py` locally
2. Verify `data/raw_odds_pure.csv` has data
3. Run `pipeline_v2/calculate_opportunities.py` locally
4. Verify `data/ev_opportunities.csv` has EV hits
5. Analyze CSVs for data quality

### Phase 2: Render Backend Setup
1. Create PostgreSQL database on Render
2. Create tables (`live_odds`, `ev_opportunities`)
3. Deploy `pipeline_v2/extract_odds.py` as scheduled job
4. Deploy `pipeline_v2/calculate_opportunities.py` as scheduled job
5. Configure Render environment variables (.env)
6. Test scheduled runs

### Phase 3: Frontend Integration
1. Create API endpoints (FastAPI or Express):
   ```
   GET /api/odds/latest → Returns live_odds
   GET /api/opportunities/current → Returns ev_opportunities
   ```
2. Update Dashboard cards to fetch from Render API
3. Display real-time data on frontend
4. Test frontend-to-backend integration

### Phase 4: Mobile Editing (GitHub App)
1. Configure `.env` in GitHub repo (encrypted or local)
2. Edit `core/config.py` from GitHub mobile app
3. Commit changes
4. Render auto-deploys on push (if configured)

---

## What's In Use (Active Components)

✅ **KEEP & USE:**
- `pipeline_v2/extract_odds.py` → Stage 1 extraction
- `pipeline_v2/calculate_opportunities.py` → Stage 2 EV calculation
- `pipeline_v2/ratings.py` → Bookmaker ratings
- `core/fair_prices.py` → Fair odds calculation
- `core/book_weights.py` → Weight system
- `core/config.py` → Configuration
- `core/utils.py` → Utility functions
- `.env` → Secrets & settings
- `tests/` → Unit tests
- `docs/` → Documentation

❌ **MOVE TO LEGACY (Already Done):**
- `ev_arb_bot.py` (legacy all-in-one)
- `extract_ev_hits.py` (legacy extraction)
- Old `fair_prices_v1.py`, `fair_prices_v2.py`
- `balldontlie.py`, `betfair_api.py`
- All `*_logger.py` files
- Scrape sources (for local bookmakers)

📋 **OPTIONAL (Can Enable Later):**
- `core/h2h.py`, `spreads.py`, etc. (needed if you switch from Pipeline V2 to custom handlers)
- Telegram alerts (configured in .env but currently disabled)
- Historical tracking (for line movement)

---

## Key Files Changed in This Session

### Renamed (Pipeline V2)
- `raw_odds_pure.py` → `extract_odds.py` ✅
- `calculate_ev.py` → `calculate_opportunities.py` ✅
- `bookmaker_ratings.py` → `ratings.py` ✅

### Renamed (Core Handlers)
- `h2h_handler.py` → `h2h.py` ✅
- `spreads_handler.py` → `spreads.py` ✅
- `totals_handler.py` → `totals.py` ✅
- `player_props_handler.py` → `player_props.py` ✅
- `nfl_props_handler.py` → `nfl_props.py` ✅

### Created/Updated
- `core/fair_prices.py` (NEW - unified interface) ✅
- Documentation updated (README.md, QUICK_START.md, etc.) ✅
- `legacy/` folder created with old files ✅

### Not Yet Committed
- All changes above are uncommitted
- Ready to push when you verify testing

---

## Testing Checklist

Before deploying to Render, test locally:

```bash
# Test Stage 1
python pipeline_v2/extract_odds.py
# Check: data/raw_odds_pure.csv created, 100+ rows, 25+ columns

# Test Stage 2
python pipeline_v2/calculate_opportunities.py
# Check: data/ev_opportunities.csv created, fair_odds valid, EV% >= 1%

# Test imports
python -c "from core.fair_prices import build_fair_prices_two_way; print('OK')"
python -c "from core.book_weights import get_sharp_books_only; print('OK')"

# Verify config
python -c "from core.config import AU_BOOKIES, CSV_HEADERS; print(f'AU books: {len(AU_BOOKIES)}, Headers: {len(CSV_HEADERS)}')"
```

---

## Next Steps

1. **Commit & Push Uncommitted Changes**
   ```bash
   git add -A
   git commit -m "chore: reorganize codebase - rename handlers, move legacy files, create fair_prices module"
   git push origin main
   ```

2. **Run Local Test** (Stage 1 + 2)
   ```bash
   python pipeline_v2/extract_odds.py
   python pipeline_v2/calculate_opportunities.py
   ```

3. **Analyze CSV Output**
   - Row counts, data quality, bookmaker coverage
   - EV opportunities found, distribution by sport

4. **Render Deployment**
   - Set up PostgreSQL
   - Configure scheduled jobs
   - Deploy extract_odds (every 30 min)
   - Deploy calculate_opportunities (after extract_odds)

5. **Frontend Integration**
   - Create API endpoints
   - Update Dashboard cards
   - Test end-to-end flow

6. **Mobile Editing**
   - Use GitHub app to edit .env or config.py
   - Commit from phone
   - Render auto-deploys

---

## Support & Questions

- All active code is in `core/` and `pipeline_v2/`
- Legacy code is in `legacy/` (safe to delete after confirming system works)
- See `TEST_PLAN.md` for detailed testing procedures
- See `.github/copilot-instructions.md` for Copilot context on current system
