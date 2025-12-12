# Handoff Document – December 10, 2025

## Current Project State

### Three Separate Repos (Multi-Root Workspace Setup)
1. **`C:\EVisionBetCode`** (Pipeline & Backend)
   - Core EV detection system; two-stage odds extraction + calculation
   - Python venv: `.venv`
   - Key files: `src/pipeline_v2/extract_odds.py`, `src/pipeline_v2/calculate_opportunities.py`
   - Data outputs: `data/raw_odds_pure.csv` (760 rows), `data/ev_opportunities.csv` (EV hits)
   - Sports: NBA (834 rows props), NFL (306 rows props), NHL (69 rows core)

2. **`C:\EVisionBetSite`** (Web UI & API)
   - Front-end + API experiments
   - Status: scaffold exists; needs wiring to pipeline data
   - Next: build FastAPI endpoint reading CSV from pipeline folder

3. **`C:\EVisionBetSite`** (Deployment & Docs)
   - Deployment guides, README, and site assets
   - Reference only for this phase

### Multi-Root VS Code Workspace
- **File:** `C:\EVisionBetCode\project.code-workspace`
- **Setup:** Open with `File > Open Workspace from File…`
- **Folders visible:** Pipeline & Backend | Web UI & API | Deployment & Docs
- **Excludes:** data/, .venv*, node_modules/, __pycache__, .pytest_cache (for speed)

### Documentation Status
- `README.md` (EVisionBetCode) – Updated; quick start included
- `docs/PROJECT_ANALYSIS_DEC2025.md` – Strategic roadmap (CSV pivot + web dashboard)
- `docs/TWO_STAGE_PIPELINE.md` – Architecture of extraction → EV calculation
- `docs/RAW_ODDS_EXTRACTION.md` – Raw odds CSV structure
- `docs/SETUP_GUIDE.md` – Development workflow (make commands, dependencies)
- `HANDOFF_NEXT_CHAT.md` – Previous handoff (older notes)

---

## What Works (✅ Verified)

### Pipeline V2
- **Stage 1 (extract_odds.py):** Extracts odds from Odds API v4 → wide CSV (one row per market/selection, all bookmakers as columns).
- **Stage 2 (calculate_opportunities.py):** Reads raw CSV → calculates fair odds from sharp books (Pinnacle, DK, FD, etc.) → outputs EV opportunities ≥ 1% edge.
- **Cost:** ~190 API credits per run (optimized: AU+US regions only, 2-way markets, time window filtering).
- **Output:** `ev_opportunities.csv` with fair odds, EV%, implied probability, Kelly stakes.

### Data Quality
- No zero-fair issues (spreads < 2%, totals = 0).
- Player props properly isolated per player (5-tuple key: sport, event_id, market, point, player_name).
- Deduplication working (SHA1 hashes, seen_hits.json).

### Recent Updates (Dec 10, 2025)

**Bookmaker Ratings System (MAJOR):**
- Implemented 1-4 star rating system for 52 bookmakers
- 4⭐ (4 books): Pinnacle, Betfair_EU, Draftkings, Fanduel - 35% weight
- 3⭐ (7 books): Betfair_AU, Betfair_UK, Betmgm, Betrivers, Betsson, Marathonbet, Lowvig - 40% weight
- 2⭐ (4 books): Nordicbet, Mybookie, Betonline, Betus - 15% weight
- 1⭐ (37 books): Target bookmakers (AU/US secondaries) - 10% weight
- Created `src/pipeline_v2/ratings.py` with sport-specific weight profiles

**Fair Odds Calculation - CRITICAL BUG FIX:**
- **Issue:** Fair odds were showing 1.1877 when they should be ~1.93 (calculation was using single weight total for both Over/Under sides)
- **Root cause:** After outlier filtering, Over and Under sides had different book coverage but shared one weight denominator
- **Fix:** Calculate separate weight totals for Over and Under sides after outlier filtering
- **Impact:** 26 false positives reduced to 1 legitimate opportunity; fair odds now accurate
- **Documentation:** `docs/BUGFIX_FAIR_ODDS_DEC10_2025.md`

**Outlier Detection:**
- Added 5% tolerance filter to remove stale/aberrant odds before weighting
- Weighted average now used instead of simple median
- Sport-specific profiles: NBA/NFL (35/40/15/10), NHL (50/30/10/10), Cricket/Tennis (65-75/15-25/5/5)

**Duplicate Row Issue (DISCOVERED):**
- Raw CSV has duplicate rows from multiple API calls (different timestamps)
- `extract_sides()` was picking first row which often had missing bookmaker data
- **Fix implemented:** Now selects row with most bookmaker coverage
- **Result:** 7 missed EV opportunities now being detected (e.g., Mikal Bridges Under @Betr 2.40 vs fair 2.14 = +12.16%)

**Outlier Test Tool (NEW):**
- Created `src/pipeline_v2/outlier_test.py` - highlights AU books 3%+ above best sharp
- Output: `data/outlier_highlights.csv` with YELLOW flag column
- Found 63 outlier opportunities, 7 of which are true EV opportunities
- Created `src/pipeline_v2/check_outliers_ev.py` to validate outliers against fair odds engine

---

## Outstanding Items & Next Steps

### 🔴 CRITICAL - Fix Duplicate Rows in Raw CSV
**Issue:** Multiple API calls create duplicate rows with different timestamps/bookmaker coverage
**Impact:** 7 EV opportunities missed (Mikal Bridges +12.16%, Scottie Barnes +6.65%, etc.)
**Current workaround:** `extract_sides()` now picks row with most bookmaker coverage
**Permanent fix needed:**
- **Option 1 (RECOMMENDED):** Deduplicate in `extract_odds.py` - keep only latest timestamp per (event_id, market, point, selection)
- **Option 2:** Separate CSV per extraction with timestamp in filename
- **Option 3:** Switch to database with proper schema (see database design below)

### 🟡 HIGH PRIORITY - Database Architecture for Web App
**Requirements from user:**
1. Website always uses newest raw odds data
2. Track line movement (flag large odds changes between extractions)
3. Auto-archive: Move started games to "Post Game" DB, auto-delete after 48hrs

**Proposed PostgreSQL Schema:**
```sql
-- Active odds (pre-game)
CREATE TABLE live_odds (
    id SERIAL PRIMARY KEY,
    extracted_at TIMESTAMP DEFAULT NOW(),
    sport VARCHAR(50),
    event_id VARCHAR(100),
    commence_time TIMESTAMP,
    market VARCHAR(50),
    point DECIMAL,
    selection VARCHAR(100),
    bookmaker VARCHAR(50),
    odds DECIMAL(10,2),
    odds_previous DECIMAL(10,2),  -- From last extraction
    line_movement DECIMAL(10,2),  -- Percentage change
    INDEX(event_id, market, selection),
    INDEX(commence_time),
    INDEX(extracted_at)
);

-- Line movement alerts
CREATE TABLE line_movements (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP DEFAULT NOW(),
    event_id VARCHAR(100),
    market VARCHAR(50),
    selection VARCHAR(100),
    bookmaker VARCHAR(50),
    old_odds DECIMAL(10,2),
    new_odds DECIMAL(10,2),
    change_pct DECIMAL(10,2),
    INDEX(detected_at)
);

-- Post-game archive (48hr retention)
CREATE TABLE postgame_odds (
    id SERIAL PRIMARY KEY,
    archived_at TIMESTAMP DEFAULT NOW(),
    original_data JSONB,  -- Full row from live_odds
    game_started_at TIMESTAMP,
    expires_at TIMESTAMP,  -- archived_at + 48hrs
    INDEX(expires_at)
);

-- Scheduled cleanup job: DELETE FROM postgame_odds WHERE expires_at < NOW()
```

**Pipeline Integration:**
- `extract_odds.py` writes to `live_odds` table (upsert by event_id+market+selection+bookmaker)
- Detect line movement: if `ABS((new_odds - old_odds) / old_odds) > 0.05` → insert to `line_movements`
- Cron job (every 5 min): `INSERT INTO postgame_odds SELECT * FROM live_odds WHERE commence_time < NOW()`
- Cron job (hourly): `DELETE FROM postgame_odds WHERE expires_at < NOW()`

### 🟢 MEDIUM PRIORITY - Enhancements
- **Outlier highlights on web UI:** Show YELLOW flag for AU books 3%+ above sharps
- **Line movement widget:** Display recent significant odds changes
- **Bookmaker coverage indicator:** Show which sharps available per market
- **Historical EV tracking:** Log all detected opportunities for pattern analysis

### 🔵 LOW PRIORITY - Web UI Phase 1
**Goal:** Show EV opportunities in web table
1. Build FastAPI endpoint reading `ev_opportunities.csv`
2. Front-end table with filters (sport, market, minEV, bookmaker)
3. Mobile-responsive design

### 🔵 LOW PRIORITY - Web UI Phase 2
- Detail drawer (all bookmaker odds for market)
- Column chooser
- Sort/export
- Bookmarking filters

### 🔵 LOW PRIORITY - Production
- Auth (email magic link)
- Scheduled bot runs
- Telegram/Email alerts
- Subscription logic

---

## Key Configuration Files

### `.env` (EVisionBetCode)
```bash
ODDS_API_KEY=your_key
SPORTS=basketball_nba,americanfootball_nfl,icehockey_nhl
REGIONS=au,us
EV_MIN_EDGE=0.01
BETFAIR_COMMISSION=0.06
```

### Python Environments
- **Pipeline:** `.venv` in `C:\EVisionBetCode`
- **API (if new):** Create `.venv` in `C:\EVisionBetSite` and install FastAPI, pandas, etc.
- **Activation:** `& ".\.venv\Scripts\Activate.ps1"` (PowerShell) or `.\.venv\Scripts\activate` (CMD)

---

## Common Commands

### Pipeline (from `C:\EVisionBetCode`)
```powershell
# Activate venv
& ".\.venv-1\Scripts\Activate.ps1"

# Extract raw odds (~2 min, 190 credits)
python src/pipeline_v2/extract_odds.py

# Calculate EV (instant, no API calls)
python src/pipeline_v2/calculate_opportunities.py

# View sample data
type data/ev_opportunities.csv | head -5
```

### API (from `C:\EVisionBetSite`, once set up)
```powershell
# Activate venv
& ".\.venv\Scripts\Activate.ps1"

# Run API server
python main.py  # or uvicorn app:app --reload
```

### Git (from any repo root)
```powershell
git status
git add .
git commit -m "message"
git push
```

---

## Critical Notes

### Sharps & Fair Prices (UPDATED DEC 10)
- **52 bookmakers** with 1-4 star ratings (see `src/pipeline_v2/ratings.py`)
- **Sharp books (3⭐+4⭐):** Pinnacle, Betfair_EU, Draftkings, Fanduel, Betfair_AU, Betfair_UK, Betmgm, Betrivers, Betsson, Marathonbet, Lowvig (11 total)
- **Target books (1⭐):** Sportsbet, Pointsbet, Tab, Tabtouch, Betr, Neds, Boombet, plus 30 US/EU secondaries (37 total)
- **Fair odds = weighted average** of sharp books (after devig + outlier removal) with 10% minimum weight coverage
- **Sport-specific profiles:** 8 sports configured with different weight distributions

### Player Props Grouping (Critical Fix Dec 2025)
- Each player gets isolated evaluation (5-tuple key prevents cross-player contamination).
- 2-way markets only (Over/Under pairs; filters out Yes/No single bets).
- DK + FD coverage required for cost optimization.

### EV Calculation
```
EV% = (market_odds / fair_odds - 1) × 100
Threshold: ≥ 1% edge reported
Kelly stake = bankroll × kelly_fraction × edge / (odds - 1)
```

### Data Files (Gitignored)
- `data/raw_odds_pure.csv` – Raw odds (wide format)
- `data/ev_opportunities.csv` – EV hits only
- `data/seen_hits.json` – Deduplication
- `data/api_usage.json` – API quota tracking
- **Never commit data CSVs to Git.**

---

## Troubleshooting

### "Module not found" errors
- Confirm venv activated: `python -c "import sys; print(sys.prefix)"`
- Reinstall deps: `pip install -r requirements.txt`

### API rate limits (Odds API)
- Free tier: 500 calls/month (~2 pipeline runs/day).
- Check remaining: check response headers `x-requests-remaining`.

### File locked errors (Windows)
- Close the CSV in Excel before re-running extraction.
- Fallback: script writes to timestamped file if primary is locked.

### Git merge conflicts
- Use `git diff` to inspect; resolve manually or ask in chat.

---

## Next Chat Checklist

- [ ] Open `C:\EVisionBetCode\project.code-workspace` in VS Code.
- [ ] Activate `.venv-1` in Pipeline folder.
- [ ] Run `python src/pipeline_v2/extract_odds.py` to verify pipeline works.
- [ ] Check `data/ev_opportunities.csv` row count (should have several hundred).
- [ ] Start building FastAPI in `EVisionBetSite` (or ask for skeleton).
- [ ] Wire front-end to API endpoint.

---

## Questions to Ask Next Chat

1. Should I scaffold a FastAPI app in `EVisionBetSite`, or use an existing one?
2. Do you want SQLite now or keep CSV for MVP?
3. What's the priority: filters/UX or auth/scheduling?
4. Any specific design preferences for the web UI (Tailwind, Material-UI, etc.)?

---

## Recent Commits (Dec 10, 2025)
- `439a4fa` - Add bookmaker ratings system with weighted fair odds
- `349545f` - Document fair odds calculation bug fix
- `1250b27` - Update Copilot instructions with bookmaker ratings and bug fix

## Files Added/Modified (Dec 10)
- `src/pipeline_v2/ratings.py` (NEW) - 52 bookmakers with 1-4 star ratings, sport profiles
- `src/pipeline_v2/calculate_opportunities.py` (MODIFIED) - Fixed fair odds bug, updated extract_sides() for duplicate handling
- `src/pipeline_v2/outlier_test.py` (NEW) - Detects AU books 3%+ above sharps
- `src/pipeline_v2/check_outliers_ev.py` (NEW) - Validates outliers with fair odds engine
- `docs/BUGFIX_FAIR_ODDS_DEC10_2025.md` (NEW) - Critical bug fix documentation
- `docs/FAIR_ODDS_CALCULATION.md` (NEW) - Methodology documentation
- `.github/copilot-instructions.md` (UPDATED) - Latest system changes

---

**Last updated:** December 10, 2025 16:45 UTC  
**Status:** Bookmaker ratings system complete. Fair odds bug fixed. Database architecture pending for web app.
