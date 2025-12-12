---
# EVisionBetCode – AI Agent Coding Instructions

**Project:** EV_ARB Bot – Sports Betting Expected Value Finder
**Status:** Production (Pipeline V2 + FastAPI backend + Render deployment)
**Last Updated:** December 12, 2025

---

## System Overview

- **Purpose:** Identify expected value (EV) betting opportunities by analyzing odds from 50+ bookmakers (via The Odds API), using sharp book weighting and per-player prop isolation.
- **Architecture:**
  - **Two-stage pipeline:**
    1. `src/pipeline_v2/extract_odds.py` – Extracts raw odds to `data/raw_odds_pure.csv` (wide format, all books as columns)
    2. `src/pipeline_v2/calculate_opportunities.py` – Calculates fair odds and EV, outputs `data/ev_opportunities.csv`
  - **Backend API:** `backend_api.py` (FastAPI, deployed on Render) exposes `/api/ev/hits`, `/api/odds/latest`, `/health`.
  - **Frontend:** EVisionBetSite (separate repo) polls API every 2 min.

---

## Essential Workflows

**Local setup:**
```bash
make dev-install
# or: pip install -e ".[dev]"
# Add .env with ODDS_API_KEY, DATABASE_URL (optional), ADMIN_PASSWORD_HASH
```
**Run pipeline:**
```bash
python src/pipeline_v2/extract_odds.py
python src/pipeline_v2/calculate_opportunities.py
# Output: data/ev_opportunities.csv
```
**Testing:**
```bash
make pre-commit  # all checks
make test        # pytest
make lint        # flake8, pylint
make format      # black, isort
make type-check  # mypy
```
**Backend API (local):**
```bash
uvicorn backend_api:app --reload
curl http://localhost:8000/health
curl http://localhost:8000/api/ev/hits?limit=10
```

---

## Critical Patterns & Conventions

- **Data flow:** Odds API → `extract_odds.py` → `raw_odds_pure.csv` → `calculate_opportunities.py` → `ev_opportunities.csv` → API/DB
- **File I/O:** Always use `get_data_dir()` (never hardcode `/data` paths) for cross-platform/Render compatibility.
- **Fair odds:**
  - Only use 3⭐/4⭐ books (see `src/pipeline_v2/ratings.py`)
  - Use *separate* weight totals for Over/Under (see `fair_from_sharps()` in `calculate_opportunities.py`)
  - Outlier removal: 5% tolerance from median
- **Player props:** Always group by 5-tuple `(sport, event_id, market, point, player_name)` (never just market/point)
- **Deduplication:** Use `seen_hits.json` logic before writing new EV hits
- **Error handling:**
  - Graceful skip for unsupported props (422)
  - Exclude markets with <2 sharp books
  - Fallback for missing odds
- **Testing:**
  - Validate with 100+ row samples, check `sharp_book_count`, and spot-check EV% math
  - Use `tests/test_fair_odds.py` and `tests/test_grouping.py`

---

## Integration & Deployment

- **Render:**
  - `evision-extract-odds` (cron, every 30min): runs `extract_odds.py`
  - `evision-calculate-opportunities` (cron, +5min): runs `calculate_opportunities.py`
  - `evision-api` (web): runs `backend_api.py`
  - All use env vars (never commit `.env`)
- **Frontend:**
  - Config: `EVisionBetSite/frontend/src/config.js` auto-detects dev/prod API
  - CORS: `backend_api.py` allows localhost and evisionbet.com

---

## Common Pitfalls (AI Agents)

- Never hardcode `/data` paths – always use `get_data_dir()`
- Never group player props by (market, point) only
- Never use a single weight total for both Over/Under in fair odds
- Always check `seen_hits.json` for deduplication
- Always handle missing odds/unsupported props gracefully
- Never write DB-only logic without file fallback

---

## Key Files & Docs

- `README.md` – Project overview, quick start
- `src/pipeline_v2/README.md` – Pipeline architecture
- `src/pipeline_v2/ratings.py` – Bookmaker ratings/weights
- `src/pipeline_v2/calculate_opportunities.py` – Fair odds/EV logic
- `docs/BUGFIX_FAIR_ODDS_DEC10_2025.md` – Fair odds bug history
- `docs/TWO_STAGE_PIPELINE.md` – Architecture
- `.env` – All config

---

## When Modifying or Extending

- Preserve deduplication, per-player grouping, and fair odds logic
- Validate changes with real data and tests
- Document new sports/markets in both `.env` and extraction/calculation scripts

---