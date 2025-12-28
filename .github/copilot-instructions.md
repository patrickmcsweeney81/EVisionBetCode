---
# EVisionBet – AI Agent Quick Reference

**👉 START HERE:** Read [PATS_FILE.md](../PATS_FILE.md) first. This file is the quick reference.

**Scope:** Two-repo workspace:
- Backend + extraction: [EVisionBetCode](../README.md)
- Frontend: [EVisionBetSite/frontend](../../EVisionBetSite/frontend/README.md)

---

## Current Architecture (V3 - Active)

**Data Flow:**
```
The Odds API → extract_nba_v3.py → data/v3/extracts/*.csv → backend_api.py → Frontend React
```

**Active Files:**
- `extract_nba_v3.py` - NBA odds extraction (186 lines)
- `backend_api.py` - FastAPI server + CSV reader (CORS enabled)
- `bookmaker_ratings.py` - Bookmaker weight tiers (1⭐ target vs 3⭐/4⭐ sharp)
- `pyproject.toml` - Dependencies (canonical source)
- `data/v3/extracts/` - Latest timestamped CSV (286 rows, 53 bookmakers)

**Archived (Reference Only):**
- `archive/` folder contains v1/v2 pipeline code (two-stage calculation, EV math, fair odds logic)
- Not active but available if patterns needed

---

## Critical Pattern: Multi-Line Extraction ✅ FIXED (Dec 28)

**Each unique `(market_type, selection, point)` gets its own row.**

❌ **Wrong:** Consolidate all spreads to "most common point" (loses data)
✅ **Right:** Every spread variation (-6.5, -7.0, -7.5, etc.) is a separate row with all bookmakers' odds

**Example (correct):**
```
| market | selection | point | book1_odds | book2_odds | ... |
| spread | home      | -6.5  | -110       | -108       | ... |
| spread | home      | -7.0  | -110       | -105       | ... |
| spread | home      | -7.5  | -112       | -110       | ... |
```

Result: 12 NBA events → 286 total rows (124 spreads + 162 other markets)

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
