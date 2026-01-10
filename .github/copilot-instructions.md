---
# EVisionBet – AI Agent Quick Reference

**👉 START HERE:** Read [PATS_FILE.md](../PATS_FILE.md) first. This file is the quick reference.

**Scope:** Two-repo workspace:
- Backend + extraction: [EVisionBetCode](../README.md)
- Frontend: [EVisionBetSite/frontend](../../EVisionBetSite/frontend/README.md)

---

## Current Architecture (V3 - Multi-Sport Active)

**Data Flow:**
```
The Odds API → extract_nba_v3.py + extract_nfl_v3.py → orchestrate_pipeline.py → AllSports_EV.csv → backend_api.py → Frontend React
```

**Active Files:**
- `extract_nba_v3.py` / `extract_nfl_v3.py` - Sport-specific odds extraction
- `filter_nba_v3.py` / `filter_nfl_v3.py` - Composite Key pairing + filtering
- `orchestrate_pipeline.py` - Parallel multi-sport pipeline orchestrator
- `manage_allsports_ev.py` - Date archiving and retention (4 days)
- `audit_pipeline.py` - Stage counts and line-loss analysis
- `validate_pairing_results.py` - 7-point validation (strict spreads +x/-x)
- `backend_api.py` - FastAPI server + CSV reader (CORS enabled)
- `bookmaker_ratings.py` - Bookmaker weight tiers (4⭐ sharp vs 0⭐ AU target)
- `pyproject.toml` - Dependencies (canonical source)
- `data/v3/extracts/` - AllSports_EV.csv (6,270 rows: NBA 3,208 + NFL 2,766)

**Archived (Reference Only):**
- `archive/` folder contains v1/v2 pipeline code (two-stage calculation, EV math, fair odds logic)
- Not active but available if patterns needed

---

## Critical Pattern: Composite Key Pairing ✅ ACTIVE (Jan 10)

**Each unique `(event_name, market_type, point, player_name)` gets its own pair_id.**

❌ **Wrong:** Group by point only (causes cross-player pairing bugs)
✅ **Right:** Every market is uniquely identified by event + market + point + player

**Example (correct):**
```
| event_name | market_type | player_name | point | selection | pair_id |
| Game A     | player_pts  | Player X    | 3.5   | Over      | 0       |
| Game A     | player_pts  | Player X    | 3.5   | Under     | 0       |
| Game A     | player_pts  | Player Y    | 3.5   | Over      | 1       |
| Game A     | player_pts  | Player Y    | 3.5   | Under     | 1       |
```

Result: NBA 728 pairs (1,456 rows), NFL 461 pairs (922 rows), zero cross-player bugs

---

## Backend Development

**API Endpoints (backend_api.py):**
- `/health` - Status check
- `/api/csv` - Latest CSV data (JSON format)
- Routes auto-read from latest file in `data/v3/extracts/`

**Key Pattern:**
```python
# Read latest CSV
def get_latest_csv():
    files = sorted(glob.glob("data/v3/extracts/*.csv"))
    return files[-1] if files else None

# Serve to frontend
@app.get("/api/csv")
async def get_csv_data():
    df = pd.read_csv(get_latest_csv())
    return df.to_dict(orient="records")
```

**Important:** CSV is source of truth. No DB transformation. No calculations.

---

## Frontend Development

**Config (EVisionBetSite/frontend/src/config.js):**
- Auto-detects backend URL (localhost:8000 or production)
- React components read from `/api/csv` endpoint
- Real-time updates (user can refresh or set auto-refresh)

**Key Pattern:**
- Read config to get API_URL
- Fetch from `${API_URL}/api/csv`
- Parse response, display in table

---

## Bookmaker Configuration

**Ratings (bookmaker_ratings.py):**
```python
BOOKMAKER_RATINGS = {
    "DraftKings": 1,      # 1⭐ = Target book (shows opportunities)
    "FanDuel": 1,         # 1⭐
    "BetMGM": 3,          # 3⭐ = Sharp book (use for fair odds only)
    "Pinnacle": 4,        # 4⭐ = Sharpest
    # ... 49 total books
}
```

**Usage Rule:**
- Extract uses all books (no filtering)
- EV calculations (when added) will use 3⭐/4⭐ for fair odds, 1⭐ for targets

---

## Developer Commands

```bash
# Extract NBA data
python extract_nba_v3.py

# Backend API
uvicorn backend_api:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd ../EVisionBetSite/frontend
npm start

# Git status (should always be clean)
git status
```

---

## Non-Negotiable Rules

1. **Multi-line preservation:** Never consolidate spread/total lines by point value
2. **CSV-first approach:** Always write CSV before DB (CSV is source of truth)
3. **Extraction complete:** Extract all markets, all bookmakers, no filtering
4. **Bookmaker mixing:** When doing fair odds: only 3⭐/4⭐. When surfacing opportunities: only 1⭐
5. **API CORS:** Keep enabled for frontend (unless explicitly changed)
6. **Git hygiene:** Commit with clear messages, no dangling branches

---

## Reference Files

- **Main README:** [README.md](../README.md)
- **Frontend README:** [EVisionBetSite/README.md](../../EVisionBetSite/README.md)
- **Project Start:** [PATS_FILE.md](../PATS_FILE.md)
- **Archive:** [archive/README.md](../archive/README.md)

---

**Last Updated:** December 28, 2025  
**Status:** ✅ All active code documented, consolidated to single source of truth
