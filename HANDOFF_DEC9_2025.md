# Handoff Document – December 9, 2025

## Current Project State

### Three Separate Repos (Multi-Root Workspace Setup)
1. **`C:\EV_ARB Bot VSCode`** (Pipeline & Backend)
   - Core EV detection system; two-stage odds extraction + calculation
   - Python venv: `.venv-1`
   - Key files: `pipeline_v2/raw_odds_pure.py`, `pipeline_v2/calculate_ev.py`
   - Data outputs: `data/raw_odds_pure.csv` (760 rows), `data/ev_opportunities.csv` (EV hits)
   - Sports: NBA (834 rows props), NFL (306 rows props), NHL (69 rows core)

2. **`C:\EV_Finder`** (Web UI & API)
   - Front-end + API experiments
   - Status: scaffold exists; needs wiring to pipeline data
   - Next: build FastAPI endpoint reading CSV from pipeline folder

3. **`C:\EVisionBetSite`** (Deployment & Docs)
   - Deployment guides, README, and site assets
   - Reference only for this phase

### Multi-Root VS Code Workspace
- **File:** `C:\EVision Project VSCode\project.code-workspace`
- **Setup:** Open with `File > Open Workspace from File…`
- **Folders visible:** Pipeline & Backend | Web UI & API | Deployment & Docs
- **Excludes:** data/, .venv*, node_modules/, __pycache__, .pytest_cache (for speed)

### Documentation Status
- `README.md` (EV_ARB Bot VSCode) – Updated; quick start included
- `docs/PROJECT_ANALYSIS_DEC2025.md` – Strategic roadmap (CSV pivot + web dashboard)
- `docs/TWO_STAGE_PIPELINE.md` – Architecture of extraction → EV calculation
- `docs/RAW_ODDS_EXTRACTION.md` – Raw odds CSV structure
- `docs/SETUP_GUIDE.md` – Development workflow (make commands, dependencies)
- `HANDOFF_NEXT_CHAT.md` – Previous handoff (older notes)

---

## What Works (✅ Verified)

### Pipeline V2
- **Stage 1 (raw_odds_pure.py):** Extracts odds from Odds API v4 → wide CSV (one row per market/selection, all bookmakers as columns).
- **Stage 2 (calculate_ev.py):** Reads raw CSV → calculates fair odds from sharp books (Pinnacle, DK, FD, etc.) → outputs EV opportunities ≥ 1% edge.
- **Cost:** ~190 API credits per run (optimized: AU+US regions only, 2-way markets, time window filtering).
- **Output:** `ev_opportunities.csv` with fair odds, EV%, implied probability, Kelly stakes.

### Data Quality
- No zero-fair issues (spreads < 2%, totals = 0).
- Player props properly isolated per player (5-tuple key: sport, event_id, market, point, player_name).
- Deduplication working (SHA1 hashes, seen_hits.json).

### Recent Cleanup (Dec 9, 2025)
- Removed 8 helper/debug/backup files from `pipeline_v2/` (apply_fixes.py, FILTER_LOGIC.py, check_data.py, debug_props.py, sample_raw.py, test_api_simple.py, raw_odds_pure.py.backup, FIXES_TO_APPLY.py).
- Kept core files: raw_odds_pure.py, calculate_ev.py, README.md.

---

## What's Next (Priority Order)

### Phase 1: Wire Web UI to Pipeline Data (This Week)
**Goal:** Show EV opportunities in a web table with filters.

1. **Build minimal FastAPI endpoint** (in `EV_Finder`):
   - `GET /api/hits` → reads `..\..\EV_ARB Bot VSCode\data\ev_opportunities.csv`, returns JSON.
   - Filters: sport, market, minEV, bookmaker, page/limit.
   - CORS enabled for local dev.

2. **Front-end integration**:
   - Fetch from API → display in table.
   - Add filters (min EV slider, sport dropdown, market dropdown).
   - Mobile-responsive.

3. **Deploy locally** → test end-to-end.

### Phase 2: Enhance (Next Week)
- Detail drawer (click row → see all bookmaker odds for that market).
- Column chooser (toggle which columns visible).
- Sort/export options.
- Bookmarking filters.

### Phase 3: Production (2+ Weeks)
- Auth (email magic link).
- Database (SQLite/Postgres instead of CSV).
- Scheduled bot runs (cron).
- Telegram/Email alerts.
- Subscription logic.

---

## Key Configuration Files

### `.env` (EV_ARB Bot VSCode)
```bash
ODDS_API_KEY=your_key
SPORTS=basketball_nba,americanfootball_nfl,icehockey_nhl
REGIONS=au,us
EV_MIN_EDGE=0.01
BETFAIR_COMMISSION=0.06
```

### Python Environments
- **Pipeline:** `.venv-1` in `C:\EV_ARB Bot VSCode`
- **API (if new):** Create `.venv` in `C:\EV_Finder` and install FastAPI, pandas, etc.
- **Activation:** `& ".\.venv\Scripts\Activate.ps1"` (PowerShell) or `.\.venv\Scripts\activate` (CMD)

---

## Common Commands

### Pipeline (from `C:\EV_ARB Bot VSCode`)
```powershell
# Activate venv
& ".\.venv-1\Scripts\Activate.ps1"

# Extract raw odds (~2 min, 190 credits)
python pipeline_v2/raw_odds_pure.py

# Calculate EV (instant, no API calls)
python pipeline_v2/calculate_ev.py

# View sample data
type data/ev_opportunities.csv | head -5
```

### API (from `C:\EV_Finder`, once set up)
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

### Sharps & Fair Prices
- Sharp books (for fair odds): Pinnacle, Betfair_EU/AU, DraftKings, FanDuel, BetMGM, Betonline, Bovada, Lowvig, MyBookie, Betus, Marathonbet, Matchbook.
- AU target books: Sportsbet, Pointsbet, Betright, Tab, Neds, Ladbrokes, Bet365, Dabble, Unibet, Playup, Tabtouch, Betr, Boombet.
- Fair odds = **median** of sharp books with 2+ coverage requirement.

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

- [ ] Open `C:\EVision Project VSCode\project.code-workspace` in VS Code.
- [ ] Activate `.venv-1` in Pipeline folder.
- [ ] Run `python pipeline_v2/raw_odds_pure.py` to verify pipeline works.
- [ ] Check `data/ev_opportunities.csv` row count (should have several hundred).
- [ ] Start building FastAPI in `EV_Finder` (or ask for skeleton).
- [ ] Wire front-end to API endpoint.

---

## Questions to Ask Next Chat

1. Should I scaffold a FastAPI app in `EV_Finder`, or use an existing one?
2. Do you want SQLite now or keep CSV for MVP?
3. What's the priority: filters/UX or auth/scheduling?
4. Any specific design preferences for the web UI (Tailwind, Material-UI, etc.)?

---

**Last updated:** December 9, 2025 09:14 AM UTC  
**Status:** Ready for Phase 1 (Web UI integration).
