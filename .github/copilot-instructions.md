# EV Bot AI Agent Instructions

**Project:** EV_ARB Bot – Sports Betting Expected Value Finder  
**Status:** Production-ready (Pipeline V2 + Backend API + Render Deployment)  
**Last Updated:** December 12, 2025

---

## Project Overview

This project identifies **expected value (EV) opportunities** in sports betting by analyzing odds from multiple bookmakers using The Odds API. The system calculates fair prices from sharp bookmakers and detects profitable edges for Australian and international bookmakers.

**Core Focus:** EV-only analysis (arbitrage removed)  
**Current Version:** Pipeline V2 (two-stage extraction + calculation) + FastAPI backend deployed on Render

---

## Developer Workflows & Essential Commands

### Local Development Setup

```bash
# 1. Install dependencies
make dev-install
# OR: pip install -e ".[dev]"

# 2. Create/update `.env` file with:
ODDS_API_KEY=your_api_key
DATABASE_URL=postgresql://...  # Optional for local dev (uses SQLite fallback)
ADMIN_PASSWORD_HASH=...        # For backend API auth

# 3. Test pipeline stages independently
python src/pipeline_v2/extract_odds.py         # Stage 1: Fetch odds
python src/pipeline_v2/calculate_opportunities.py  # Stage 2: Calculate EV
```

### Code Quality & Testing

```bash
# Run all checks
make pre-commit

# Individual checks
make test              # pytest with coverage
make lint              # flake8, pylint
make format            # black, isort
make type-check        # mypy
```

### FastAPI Backend (Local)

```bash
# Start dev server
uvicorn backend_api:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/ev/hits?limit=10

# With admin auth header
curl -H "X-Admin-Password: admin123" http://localhost:8000/api/admin/stats
```

### Render Deployment Checklist

1. **Cron jobs already running** - No action needed
2. **Backend API deployment:**
   - Create new Web Service on Render dashboard
   - Use `render.yaml` startCommand: `uvicorn backend_api:app --host 0.0.0.0 --port $PORT`
   - Set env vars: `DATABASE_URL` (from `.env`)
   - Test with `/health` endpoint
3. **Monitor health:** Check Render dashboard logs for cron job errors

---

## Core Architecture

### Two-Stage Pipeline

**Stage 1: Raw Odds Extraction** (`pipeline_v2/raw_odds_pure.py`)
- Fetches odds from The Odds API v4
- Supports: NBA, NFL, NHL
- Markets: h2h, spreads, totals, player props (NBA/NFL only)
- Output: `data/raw_odds_pure.csv` (wide format, one row per market/selection)
- Cost: ~194 API credits per run

**Stage 2: EV Calculation** (`pipeline_v2/calculate_ev.py`)
- Reads raw odds from CSV
- Calculates fair prices from 12 sharp bookmakers
- Detects EV opportunities (>= 1% edge)
- Output: `data/ev_opportunities.csv`
- Cost: Zero API calls

### Data Files

**Inputs:**
- `raw_odds_pure.csv` - All odds across all sports/markets/bookmakers

**Outputs:**
- `ev_opportunities.csv` - EV opportunities above 1% threshold

**Internal:**
- `seen_hits.json` - Deduplication storage
- `api_usage.json` - API quota tracking
- `cache_events.json` - Event caching

---

## Key Concepts

### 1. Fair Price Calculation

Fair odds represent the "true" market price without bookmaker margins.

**Bookmaker Ratings System (52 total books):**
- **4-star (4 books):** Pinnacle, Betfair_EU, Draftkings, Fanduel - 35% weight (8.75% each)
- **3-star (7 books):** Betfair_AU, Betfair_UK, Betmgm, Betrivers, Betsson, Marathonbet, Lowvig - 40% weight (5.71% each)
- **2-star (4 books):** Nordicbet, Mybookie, Betonline, Betus - 15% weight (3.75% each)
- **1-star (37 books):** Target bookmakers (Sportsbet, Pointsbet, etc.) - 10% weight (used for EV detection, not fair odds)

**Calculation Method:**
1. Devig each sharp bookmaker's two-way odds (Over/Under)
2. Remove outliers (5% tolerance from median)
3. Calculate **weighted average** using bookmaker ratings
4. Use **separate weight totals** for Over and Under sides (critical - see BUGFIX_FAIR_ODDS_DEC10_2025.md)
5. Requires minimum 10% weight coverage for validity

**Sport-Specific Weight Profiles:**
- NBA/NFL/Soccer: Standard (35/40/15/10)
- NHL: Pinnacle-heavy (50/30/10/10)
- Cricket/Tennis: Betfair-dominated (65-75/15-25/5/5)

### 2. Player Props Grouping (Critical)

Player props are isolated per player using 5-tuple key:
```python
(sport, event_id, market, point, player_name)
```

**Why:** Multiple players in same market were previously grouped together, preventing individual player EV calculation. **Fixed Dec 2025:** Each player now has isolated fair odds calculation.

### 3. Expected Value (EV)

```
EV% = (fair_odds / market_odds - 1) × 100
```

**Thresholds:**
- **EV >= 1%** = Reported opportunity
- **EV < 1%** = Filtered out

**Current Results (Dec 10, 2025):**
- 3,238 raw rows extracted (NBA only)
- 1 EV opportunity identified (conservative detection with accurate fair odds)
- Fair odds calculation fixed: weighted average now uses separate totals for Over/Under sides

---

## Configuration

All settings in `.env`:

```bash
# API
ODDS_API_KEY=your_key                     # Required
REGIONS=au,us                             # AU + US bookmakers only
MARKETS=h2h,spreads,totals                # Core markets

# Sports
SPORTS=basketball_nba,americanfootball_nfl,icehockey_nhl

# EV Thresholds
EV_MIN_EDGE=0.01                          # Minimum 1% edge

# Betfair Commission
BETFAIR_COMMISSION=0.06

# Kelly Betting
BANKROLL=1000
KELLY_FRACTION=0.25
```

---

## Development Patterns

1. **Error Handling**:
   - Graceful 422 errors on unsupported prop markets (skipped)
   - Soft fallback for missing bookmaker odds (market excluded)
   - Missing 2+ sharps → market excluded from EV analysis

2. **Data Management**:
   - Deduplication via SHA1 hashes of event details
   - CSV logging with UTC timestamps on all rows
   - Automatic directory/file creation on first run
   - Event caching to reduce API calls

3. **Code Organization**:
   - Pipeline V2 separated into two focused modules
   - Functions grouped by purpose with clear headers
   - Configuration helpers at module top level
   - Core logic separated into discrete mathematical functions

---

## Integration Points

1. **External APIs**:
   - The Odds API v4 (primary data source)
   - Endpoint: `https://api.the-odds-api.com/v4/sports/{sport}/odds`
   - Format: Decimal odds
   - Regions: au, us

2. **File System**:
   - Uses `pathlib` for cross-platform path handling
   - Data directory auto-created in same location as script
   - CSV format with UTF-8 encoding

---

## Common Tasks

### Running Full Pipeline

```bash
# 1. Extract raw odds
python pipeline_v2/raw_odds_pure.py

# 2. Calculate EV (no API calls)
python pipeline_v2/calculate_ev.py

# Output: data/ev_opportunities.csv
```

### Adding a New Sport

1. Add to `SPORTS` in `.env`
2. Define props in `raw_odds_pure.py`
3. Update `get_props_for_sport()` function
4. Run pipeline → automatic

### Modifying Fair Price Logic

File: `pipeline_v2/bookmaker_ratings.py`
- `BOOKMAKER_RATINGS` - Dict of all 52 bookmakers with 1-4 star ratings
- `SPORT_WEIGHT_PROFILES` - Sport-specific weight distributions
- `load_weight_config(sport)` - Get weights for specific sport
- `get_sharp_books_only()` - Returns 3⭐+4⭐ books for fair odds

File: `pipeline_v2/calculate_ev.py`
- `fair_from_sharps()` - Weighted fair odds calculation with outlier removal
- `EV_MIN_EDGE` - Threshold (default 1%)

---

## Sports & Markets Status

| Sport | Core Markets | Player Props | Status |
|-------|-------------|--------------|--------|
| NBA | h2h, spreads, totals | ✅ 10+ markets | Full support |
| NFL | h2h, spreads, totals | ✅ 15+ markets | Full support |
| NHL | h2h, spreads, totals | ❌ Not available | Core only |

---

## System Deployment Architecture

### Three-Service Architecture (Render)

The system runs on **Render.com** with three coordinated services:

1. **`evision-extract-odds` (Cron Job)**
   - Schedule: Every 30 minutes
   - Script: `src/pipeline_v2/extract_odds.py`
   - Output: `data/raw_odds_pure.csv` + PostgreSQL `live_odds` table
   - Cost: ~194 API credits per run

2. **`evision-calculate-opportunities` (Cron Job)**
   - Schedule: Every 35 minutes (5 min after extraction)
   - Script: `src/pipeline_v2/calculate_opportunities.py`
   - Input: `raw_odds_pure.csv` from PostgreSQL
   - Output: PostgreSQL `ev_opportunities` table
   - Cost: Zero API calls

3. **`evision-api` (Web Service - FastAPI)**
   - Script: `backend_api.py`
   - Health endpoint: `/health`
   - API endpoints: `/api/ev/hits`, `/api/ev/summary`, `/api/odds/latest`
   - Secured with SHA256 admin password (hashed)
   - CORS enabled for EVisionBetSite frontend

**Database:** PostgreSQL on Render (credentials in `.env`, synced to Render)

### Local Development vs. Render

- **Local:** Test pipeline stages independently with `.env` configuration
- **Render:** Automatic cron schedule + Web Service API
- **Frontend:** Auto-detects localhost (dev) vs production (evisionbet.com)

### File Organization After Deployment

```
EVisionBetCode/
├── backend_api.py            FastAPI service (Render Web)
├── src/pipeline_v2/
│   ├── extract_odds.py       Stage 1 (Render Cron)
│   ├── calculate_opportunities.py  Stage 2 (Render Cron)
│   └── ratings.py            Bookmaker 1-4 star system (52 books)
├── src/core/
│   ├── book_weights.py       Dynamic weight lookup
│   ├── fair_prices.py        Fair odds calculation
│   ├── config.py             Bookmaker lists & CSV headers
│   └── [market handlers]     h2h.py, spreads.py, etc.
├── data/
│   ├── raw_odds_pure.csv     All odds (input for stage 2)
│   └── ev_opportunities.csv  EV hits (output)
└── [database files]
```

## Recent Changes (December 2025)

✅ **Backend API Deployed (Dec 10):** FastAPI service with `/api/ev/hits`, `/api/odds/latest`, `/health`. Admin authentication via SHA256 password hash.

✅ **Bookmaker Ratings System (Dec 10):** Implemented 1-4 star rating system (52 books total) with weighted fair odds calculation. Sport-specific weight profiles for 8 sports.

✅ **Fair Odds Bug Fixed (Dec 10):** CRITICAL - Fixed weighted average calculation that was using single weight total for both Over/Under sides. Fair odds now accurate (~1.93 instead of 1.19). See docs/BUGFIX_FAIR_ODDS_DEC10_2025.md.

✅ **Outlier Detection (Dec 10):** Added 5% tolerance filter to remove stale/aberrant odds before weighting.

✅ **Player Props Grouping Fixed:** Critical bug where multiple players were grouped together is now fixed. Each player evaluated independently.

✅ **Bookmaker Expansion (Dec 10):** 52 bookmakers supported (from 15). Configurable BOOKMAKER_ORDER environment variable.

✅ **sharp_book_count Column:** Added to output showing number of sharp sources per opportunity.

✅ **NHL Support:** Added NHL core markets. Player props not available per API.

---

## When Modifying Code

### Preservation Rules
1. **Deduplication:** Maintain seen_hits.json logic
2. **Per-player isolation:** Keep 5-tuple grouping key in calculate_ev.py
3. **Separate weight totals:** CRITICAL - Over and Under sides must have independent weight totals after outlier filtering
4. **Sharp list:** Expand carefully; validate fair price logic
5. **Error handling:** Graceful degradation for missing sharps/props
6. **API efficiency:** Cache events; minimize redundant calls

### Testing Requirements
- Run with 3+ sports / 100+ rows to validate grouping
- Verify sharp_book_count accuracy
- Check EV% calculations against manual spot checks
- Validate CSV headers and column order

---

## Cross-System Patterns

### Frontend-Backend Integration (EVisionBetCode ↔ EVisionBetSite)

**Frontend Configuration:** EVisionBetSite/frontend/src/config.js
- Auto-detects localhost (dev) vs production URL
- Fallback to `https://evision-api.onrender.com` (production)
- Used by all API client calls in `frontend/src/api/client.js`

**Backend Endpoints:**
- `GET /health` - Health check (no auth required)
- `GET /api/ev/hits?limit=50&sport=nba` - Latest EV opportunities
- `GET /api/odds/latest?sport=nba` - All latest odds with bookmaker columns
- `POST /api/admin/stats` - Stats endpoint (requires X-Admin-Password header)

**CORS Configuration:** `backend_api.py` allows requests from localhost and evisionbet.com

**Data Refresh:** Frontend polls `/api/ev/hits` every 2 minutes (auto-refresh)

### Render Service Coordination

**Timing critical:** 
- Extract runs at :00 and :30 every hour
- Calculate runs 5 minutes later (at :05 and :35)
- Failure in extract = calculate skipped
- Monitor `log_runner` pattern in both scripts for debugging

**Environment sync:**
- Changes to `.env` locally must be manually updated in Render service env vars
- Use Render dashboard to update DATABASE_URL and ODDS_API_KEY
- Do NOT commit `.env` to git (contains credentials)

---

---

## Critical Architectural Patterns for AI Agents

### Data Flow & File Organization
- **Raw odds extraction** → `data/raw_odds_pure.csv` (stage 1: wide format, one row = market/outcome combo across all bookmakers)
- **EV calculation** → `data/ev_opportunities.csv` (stage 2: filtered hits >=1% edge)
- **Database sync** → PostgreSQL `live_odds` and `ev_opportunities` tables (optional but required for Render deployment)
- **Frontend connection** → Backend API endpoints return database rows; frontend polls `/api/ev/hits` every 2 min

### File Path Resolution (Critical for Render)
Both pipeline stages use `get_data_dir()` function that tries multiple locations:
1. `Path(__file__).parent.parent / "data"` (script-relative, local dev)
2. `Path.cwd() / "data"` (current working dir, Render cron jobs)
3. Parent folder detection if `"src"` is in path
4. Fallback to script-relative location

**When adding file I/O:** Always use `get_data_dir()` pattern, never hardcoded paths. This ensures code works in both local and Render environments.

### Bookmaker Rating System (Core Logic)
File: `src/pipeline_v2/ratings.py`
- **BOOKMAKER_RATINGS** dict: 52 bookmakers with 1-4 star ratings
- **SPORT_WEIGHT_PROFILES**: Weight distributions per sport (NBA: 35/40/15/10, NHL: 50/30/10/10, etc.)
- `get_sharp_books_only()`: Returns 3⭐+4⭐ books for fair odds calculation
- `get_target_books_only()`: Returns 1⭐ books used for EV detection only

**Critical rule:** Fair odds calculated ONLY from sharp books (3⭐+4⭐), but EV detection uses all books to identify opportunities at 1⭐ bookmakers.

### Fair Odds Calculation (High-Priority Bug Zone)
File: `src/pipeline_v2/calculate_opportunities.py` - look for `fair_from_sharps()` function
```python
# CRITICAL: Separate weight totals for Over/Under sides
weight_over = sum(weights for book in over_sharps)
weight_under = sum(weights for book in under_sharps)
# Don't use single total - this was a dec 10 bugfix!
fair_over = sum(devig_odds[book] * weights[book] for book in over_sharps) / weight_over
fair_under = sum(devig_odds[book] * weights[book] for book in under_sharps) / weight_under
```
**When modifying fair odds:** Test with sports containing 100+ rows and verify `fair_odds` column values make sense (~1.5-2.0 typically).

### Player Props Grouping (5-Tuple Key)
Critical bug fixed December 2025: Player props must be isolated per player using:
```python
grouping_key = (sport, event_id, market, point, player_name)
```
**Never:** Group by just (market, point) - this causes multiple players to share same fair odds.  
**When fixing props issues:** Search for "grouping_key" or "5-tuple" in calculate_opportunities.py to find isolation logic.

### Environment Variable Patterns
- **Local dev:** `ODDS_API_KEY`, `DATABASE_URL` (optional), `REGIONS=au,us`
- **Render cron:** Same vars in Render service dashboard, not in `.env` (env synced but not committed)
- **Render API:** Add `ADMIN_PASSWORD_HASH` for fastapi backend auth
- **Frontend:** Checks `window.location.hostname` to auto-detect localhost vs production API URL

### Timing Dependencies (Render Cron)
- Extract job runs at :00 and :30 every hour (194 API credits per run)
- Calculate job runs 5 minutes later (:05, :35) - depends on extract success
- If extract fails, calculate is skipped automatically
- **Monitor pattern:** Both scripts log via `log_runner()` function for debugging on Render

### Testing Patterns
**Unit testing sports logic:**
```bash
python -m pytest tests/test_fair_odds.py -v
python -m pytest tests/test_grouping.py -v
```
**Integration testing full pipeline:**
```bash
python src/pipeline_v2/extract_odds.py  # Needs ODDS_API_KEY
python src/pipeline_v2/calculate_opportunities.py  # Zero API calls
```
**Manual spot checks:**
- Verify `sharp_book_count` (>= 2) indicates number of sharp sources
- Check `ev_percent` formula: `(fair_odds / market_odds - 1) * 100`
- Ensure CSV headers match expected columns (see `config.py` for standard headers)

### Common Implementation Errors to Avoid
1. **Hardcoded `/data` paths** - Use `get_data_dir()` instead
2. **Single weight total for both Over/Under** - Bug: breaks fair odds calculation
3. **Player prop grouping on (market, point) only** - Creates grouped fair odds instead of per-player
4. **Missing deduplication check** - Always check `seen_hits.json` before writing to CSV
5. **Direct database writes without fallback** - Code should work even if DATABASE_URL not set
6. **Time filtering edge cases** - The Odds API returns ALL events; must filter by `commence_time` client-side

---

## Documentation

- **README.md** - Overview and quick start
- **pipeline_v2/README.md** - Detailed pipeline architecture
- **SYSTEM_ARCHITECTURE.md** - Three-service Render deployment diagram
- **docs/BUGFIX_FAIR_ODDS_DEC10_2025.md** - Fair odds calculation history
- **.env** - Configuration reference