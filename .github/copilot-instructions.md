---
# EVisionBet – AI Agent Guide

**Scope:** Two-repo workspace. Backend and pipeline live in [EVisionBetCode](README.md). React frontend lives in [EVisionBetSite/frontend](../EVisionBetSite/frontend/README.md). Keep both in sync.

## Big Picture
- Flow: The Odds API → [src/pipeline_v2/extract_odds.py](src/pipeline_v2/extract_odds.py) → [data/raw_odds_pure.csv](data/raw_odds_pure.csv) → [src/pipeline_v2/calculate_opportunities.py](src/pipeline_v2/calculate_opportunities.py) → [data/ev_opportunities.csv](data/ev_opportunities.csv) + Postgres → [backend_api.py](backend_api.py) FastAPI → EVisionBetSite React table (2‑minute refresh).
- Two-stage pipeline is intentional: rerun calculate without spending API credits; supports future multi-source merges.
- Data paths must come from `get_data_dir()` (Render mounts twice). Never hardcode `/data`.

## Critical Patterns
- Fair odds (`fair_from_sharps()` in [src/pipeline_v2/calculate_opportunities.py](src/pipeline_v2/calculate_opportunities.py)): only 3⭐/4⭐ books from [src/pipeline_v2/ratings.py](src/pipeline_v2/ratings.py); keep separate weight totals per side (Over vs Under); remove 5% outliers; skip if `sharp_count < 2`.
- Grouping: Player props keyed by `(sport, event_id, market, point, player_name)` using `_player_key()`; non-player markets keep `player_name` empty.
- Market guards: skip `EXCLUDE_MARKETS`, require 2-way pairs for totals, and h2h/spreads must have both sides.
- Target vs sharp: target books (1⭐) surface EV hits; sharp books (3⭐/4⭐) only for fair odds. Do not mix.
- Outputs: CSV first, DB best-effort. Never let missing DB block CSV writes.

## Developer Workflows
- Setup: `make dev-install` or `pip install -e .[dev]`; `.env` must define `ODDS_API_KEY` (+ `DATABASE_URL`, `ADMIN_PASSWORD_HASH` as needed).
- Pipeline: `python src/pipeline_v2/extract_odds.py` then `python src/pipeline_v2/calculate_opportunities.py` (or VS Code task “Pipeline: Run Full (Extract + Calculate)”). Calculation can run without fresh API fetch if CSV exists.
- Backend: `uvicorn backend_api:app --reload` (http://localhost:8000). Health at `/health`, data at `/api/ev/hits?limit=10`.
- Frontend: from [EVisionBetSite/frontend](../EVisionBetSite/frontend/README.md) run `npm start`; API URL auto-detects but `.env.local` with `REACT_APP_API_URL=http://localhost:8000` avoids surprises.
- Quality: `make pre-commit` (black+isort, flake8+pylint, mypy, pytest). Prefer `make test` for quick runs.

## Files to Grab First
- Pipeline logic: [src/pipeline_v2/calculate_opportunities.py](src/pipeline_v2/calculate_opportunities.py), [src/pipeline_v2/extract_odds.py](src/pipeline_v2/extract_odds.py), [src/pipeline_v2/ratings.py](src/pipeline_v2/ratings.py).
- Backend/API: [backend_api.py](backend_api.py) (CORS, schemas, endpoints) and [render.yaml](render.yaml) (service wiring).
- Docs: [src/pipeline_v2/README.md](src/pipeline_v2/README.md), [docs/BUGFIX_FAIR_ODDS_DEC10_2025.md](docs/BUGFIX_FAIR_ODDS_DEC10_2025.md), [docs/TWO_STAGE_PIPELINE.md](docs/TWO_STAGE_PIPELINE.md).
- Frontend reference: [EVisionBetSite/frontend/src/config.js](../EVisionBetSite/frontend/src/config.js) for API detection.

## Non-Negotiable Pitfalls
- Do not change grouping keys or weight totals sharing; EV math will break.
- Never include 1⭐/2⭐ books in fair odds. Only use sharp list for fair prices.
- Keep CSV writes resilient: missing/invalid odds should be skipped or zeroed, not fatal.
- Respect time windows and market filters in extraction to avoid API credit blowups.
- Always route file paths through `get_data_dir()` and avoid absolute `/data` usage.

## Extension Tips
- New sports/markets: adjust `SPORTS` env and props lists in [src/pipeline_v2/extract_odds.py](src/pipeline_v2/extract_odds.py).
- Bookmaker tweaks: edit ratings/weights in [src/pipeline_v2/ratings.py](src/pipeline_v2/ratings.py); update tests ([tests/test_book_weights.py](tests/test_book_weights.py)).
- Formatting/outputs: use `pretty_float()` helpers; keep EV minimum edge (`EV_MIN_EDGE`) intact unless business directs.

Questions or unclear areas? Tell me which section needs more detail and I’ll tighten it up.