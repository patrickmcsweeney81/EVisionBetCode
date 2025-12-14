---
# EVisionBetCode – AI Agent Coding Instructions

**Project:** EV_ARB Bot – Sports Betting Expected Value Finder
**Status:** Production (Pipeline V2 + FastAPI backend + Render deployment)
**Last Updated:** December 14, 2025

---

## System Overview

**Purpose:** Identify expected value (EV) betting opportunities by analyzing odds from 50+ bookmakers (via The Odds API), using sharp book weighting and per-player prop isolation.

**Key Architecture Decision:** Two-stage pipeline separates data extraction from calculation, enabling recalculation without API costs and supporting future multi-source merging.

```
The Odds API (50+ bookmakers) →
  extract_odds.py (12 sports parallel) → raw_odds_pure.csv (wide format) →
  calculate_opportunities.py → ev_opportunities.csv + PostgreSQL →
  backend_api.py (FastAPI) → EVisionBetSite (React frontend, 2-min refresh)
```

---

## Essential Workflows

**Local setup:**
```bash
make dev-install              # Install dev deps + pre-commit hooks
pip install -e ".[dev]"      # Alternative: editable install
# Create .env with ODDS_API_KEY, optional DATABASE_URL and ADMIN_PASSWORD_HASH
```

**Run pipeline (VS Code tasks available):**
```bash
python src/pipeline_v2/extract_odds.py      # → data/raw_odds_pure.csv
python src/pipeline_v2/calculate_opportunities.py  # → data/ev_opportunities.csv
# Or use task: "Pipeline: Run Full (Extract + Calculate)"
```

**Testing & QA:**
```bash
make pre-commit   # All checks (format, lint, type-check, test)
make test         # pytest with coverage
make lint         # flake8 + pylint
make format       # black + isort
make type-check   # mypy
```

**Backend API:**
```bash
uvicorn backend_api:app --reload  # Local: http://localhost:8000
curl http://localhost:8000/health
curl http://localhost:8000/api/ev/hits?limit=10
```

---

## Critical Patterns & Conventions

### Data I/O & File Paths
- **Always use `get_data_dir()`** function (never hardcode `/data` paths) – handles Render's `/src/src` duplicate and local dev
- Callable in: `extract_odds.py`, `calculate_opportunities.py`, `backend_api.py`
- Outputs: `raw_odds_pure.csv` (wide format, one row = one bookmaker/market/selection) → `ev_opportunities.csv`

### Fair Odds Calculation (`fair_from_sharps()` in calculate_opportunities.py)
- Uses only 4⭐ and 3⭐ rated books (see `ratings.py` for bookmaker star ratings)
- **Critical:** Maintain separate weight totals for Over/Under sides (not shared)
  - Weight totals: `sum(rating * sport_weight)` per side
  - Formula: `1.0 / ((sum(1/price * rating * weight) / weight_total))`
- Outlier removal: 5% tolerance from median (when multiple sharp books conflict)
- Returns: `(fair_over, fair_under, sharp_count)` – skip if `sharp_count < 2`

### Grouping Player Props
- Group by 5-tuple: `(sport, event_id, market, point, player_name)` (not just market/point)
- Extract player name from selection via `_player_key()` – handles "Player Name Over/Under" format
- Non-player markets have empty `player_name` to preserve existing grouping behavior
- See: `group_rows_wide()` and `extract_sides()` in calculate_opportunities.py

### Bookmaker Selection & Weighting
- **Sharp books** (4⭐/3⭐ only): Used for fair odds calculation (DK, FD, Pinnacle, Betfair, etc.)
- **Target books** (1⭐ only): Find EV opportunities at lower-quality sites (AU corporate books, US secondary sites)
- Rating system in `ratings.py` defines per-book stars and sport-specific weight profiles
- Example: NBA uses `{4: 0.35, 3: 0.40, 2: 0.15, 1: 0.10}` weights

### Market Exclusions & Validation
- Skip exchange-only markets: `["Specials", "In-play", ...]` (see `EXCLUDE_MARKETS` list)
- Require 2-way market pairs (Over + Under) for totals; h2h/spreads expect 2 selections
- Gracefully skip unsupported props → log warning, continue processing

### EV Calculation & Filtering
- Formula: `EV% = (odds / fair_odds) - 1.0`
- Minimum threshold: 1% edge (`EV_MIN_EDGE = 0.01`)
- Kelly stake: `kelly_stake(bankroll, fair, odds, kelly_fraction)`
- CSV output includes: sport, market, selection, best_book, best_odds, fair_odds, ev_percent, sharp_book_count

### Error Handling
- Missing/invalid odds → parse as 0 or skip row, never fail
- Database connection optional (`DATABASE_URL` env var) – file fallback always active
- API errors (throttling, timeouts) → retry with exponential backoff (in extract_odds.py)

---

## Integration & Deployment

**Render Services (3 crons + 1 web):**
- `evision-extract-odds` (cron, 30min): `python src/pipeline_v2/extract_odds.py`
- `evision-calculate-opportunities` (cron, +5min): `python src/pipeline_v2/calculate_opportunities.py`
- `evision-api` (web service): `uvicorn backend_api:app`
- All via environment variables (never commit `.env`)

**Frontend (EVisionBetSite repo):**
- React 18 + TypeScript, auto-detects dev/prod API in `frontend/src/config.js`
- Polls `/api/ev/hits?limit=10` every 2 minutes
- CORS: configured for `localhost:3000`, `localhost:8000`, and `evisionbet.com`

---

## Common Pitfalls (AI Agents Must Avoid)

1. **Hardcoded paths:** Never use `/data/` directly – call `get_data_dir()` to support Render and local dev
2. **Player prop grouping:** Group by 5-tuple including player_name, not (market, point) alone
3. **Fair odds weights:** Maintain separate weight totals for Over/Under – don't share totals
4. **Sharp book filter:** Only use 3⭐/4⭐ for fair odds; never include 1⭐/2⭐ target books in fair calculation
5. **Market filtering:** Always check `EXCLUDE_MARKETS` list; skip exchanges and in-play markets
6. **Database fallback:** Ensure CSV output works when DB is unavailable
7. **Missing sharp books:** Skip market if `sharp_count < 2`; never interpolate or guess fair odds
8. **Testing assumptions:** Always validate grouping with real 100+ row samples; spot-check EV% math

---

## Key Files & Code Patterns

| File | Purpose |
|------|---------|
| `src/pipeline_v2/extract_odds.py` | Fetch from Odds API v4, write `raw_odds_pure.csv` (wide format) |
| `src/pipeline_v2/calculate_opportunities.py` | EV calculations, grouping, fair odds logic, output CSV + DB |
| `src/pipeline_v2/ratings.py` | Bookmaker ratings (1-4⭐), sport weights, `fair_from_sharps()` formula |
| `backend_api.py` | FastAPI server, SQLAlchemy models, `/api/ev/hits`, `/health` endpoints |
| `tests/test_book_weights.py` | Rating system and weight logic validation |
| `docs/BUGFIX_FAIR_ODDS_DEC10_2025.md` | Fair odds bug history and test results |
| `.env` | ODDS_API_KEY, DATABASE_URL (optional), ADMIN_PASSWORD_HASH, SPORTS, REGIONS |

---

## When Modifying or Extending

1. **New sports/markets:** Update `SPORTS` in `.env`, add to `NBA_PROPS`/`NFL_PROPS`/etc. lists in extract_odds.py
2. **Bookmaker changes:** Edit `ratings.py` ratings and sport weight profiles; validate with real data
3. **Fair odds logic:** Preserve separate weight totals for Over/Under; test with 100+ row samples
4. **Player props:** Always group by full 5-tuple; test edge cases (multiple players same market, missing selections)
5. **Rendering output:** Use `pretty_float()` for odds/EV% formatting (2-4 decimals as needed)
6. **Database:** Ensure CSV fallback always works; test both with/without DATABASE_URL set

---