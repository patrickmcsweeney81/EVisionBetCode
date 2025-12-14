# EV_ARB Bot – Complete Setup & Deployment Guide

Sports betting expected value finder. Identifies EV opportunities by analyzing odds from 50+ bookmakers.

- **Status:** Production (Pipeline V2 + FastAPI + Render)
- **Technology Stack:** Python 3.9+, FastAPI, SQLAlchemy, PostgreSQL, React
- **Deployment:** Render (3 services: 2 crons + 1 web API)
- **Architecture:** Two-stage pipeline (extract → calculate) with parallel processing
- **Last Updated:** December 13, 2025

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- VS Code with extensions (see [VSCODE_SETUP.md](VSCODE_SETUP.md))
- `.env` file with `ODDS_API_KEY` from [The Odds API](https://theoddsapi.com/)

### Run These Commands
```bash
# Navigate to project
cd C:\EVisionBetCode

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"

# Create .env file with ODDS_API_KEY
copy .env.example .env

# Run pipeline
python src/pipeline_v2/extract_odds.py
python src/pipeline_v2/calculate_opportunities.py

# Start API
uvicorn backend_api:app --reload
```

**Expected Output:**
- Extract: 6,600+ rows (all available sports)
- Calculate: 250+ EV opportunities
- API: Live at http://localhost:8000/api/ev/hits

---

## 📚 Documentation

### New to This Project?

1. **[VSCODE_SETUP.md](VSCODE_SETUP.md)** – VS Code Configuration (10 min)
   - ✅ Install Python, Pylance, Black, Flake8, isort
   - ✅ Select Python interpreter (`.venv\Scripts\python.exe`)
   - ✅ Enable auto-format on save
   - ✅ Test setup with first run
   - ✅ Troubleshooting for common issues

2. **[README.md](README.md)** (this file) – Full Reference
   - Architecture overview with data flow
   - Environment variables & configuration
   - Local development workflow
   - Pre-commit checks & testing
   - Common tasks
   - Render deployment guide

3. **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** – ⚡ API Credit & Storage Optimization (NEW!)
   - Reduce API costs by 90% (props management, time windows)
   - REPLACE mode vs APPEND mode (prevent storage bloat)
   - Configuration for dev/prod/peak seasons
   - Player props cost/benefit analysis
   - Monthly cost analysis & monitoring

### Deep Dives

- **[src/pipeline_v2/README.md](src/pipeline_v2/README.md)** – Pipeline Architecture
  - How extract/calculate work internally
  - Fair odds calculation logic
  - Design decisions

- **[docs/BUGFIX_FAIR_ODDS_DEC10_2025.md](docs/BUGFIX_FAIR_ODDS_DEC10_2025.md)** – Fair Odds Math
  - EV calculation formulas
  - Weight totals for Over/Under
  - Test results and examples

- **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)** – Render Setup (if deploying)
  - Create services on Render
  - Set environment variables
  - Monitor cron logs

---

## 🏗️ Architecture

### Data Flow
```
The Odds API (50+ bookmakers)
         ↓
extract_odds.py (12 sports parallel)
  ↓ raw_odds_pure table + CSV ↓
calculate_opportunities.py
  ↓ ev_opportunities table + CSV ↓
backend_api.py (FastAPI)
  ↓ /api/ev/hits ↓
EVisionBetSite (React frontend)
```

### Key Stats
| Component | Details |
|-----------|---------|
| **Sports** | 12 (NBA, NFL, NHL, EPL, Champions League, ATP, WTA, Big Bash, IPL, NCAAF, MLB, NBL) |
| **Bookmakers** | 53+ rated 1⭐ to 4⭐ |
| **Parallel Extraction** | ThreadPoolExecutor (5 concurrent sports) |
| **Extract Time** | ~1-2 min (12 sports parallel) |
| **Calculate Time** | <30 sec |
| **Data Output** | CSV + PostgreSQL (both, with fallback) |

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/pipeline_v2/extract_odds.py` | Fetch odds from API (12 sports parallel) |
| `src/pipeline_v2/calculate_opportunities.py` | Calculate fair odds & EV opportunities |
| `src/pipeline_v2/ratings.py` | Bookmaker ratings (1⭐-4⭐) & sport weights |
| `backend_api.py` | FastAPI endpoints (`/api/ev/hits`, `/health`, etc.) |
| `.env` | Configuration (API key, DB URL, sports list) |
| `render.yaml` | Render deployment config (3 services) |
| `pyproject.toml` | Python dependencies & metadata |

---

## ⚙️ Environment Variables

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `ODDS_API_KEY` | ✅ Yes | `81d1ac74594d5d453e242c14ad479955` | The Odds API authentication |
| `DATABASE_URL` | ⚠️ Optional | `postgresql://user:pw@localhost:5432/db` | Database (DB primary, CSV fallback) |
| `SPORTS` | ❌ No | `basketball_nba,americanfootball_nfl` | Custom sports (comma-separated, default: all 12) |
| `MARKETS` | ❌ No | `h2h,spreads,totals` | Market types (default: h2h,spreads,totals) |
| `ADMIN_PASSWORD_HASH` | ✅ (Render) | `sha256:...` | Admin panel password (Render only) |

### Default 12 Sports
```
basketball_nba, basketball_nbl, americanfootball_nfl, americanfootball_ncaaf,
icehockey_nhl, soccer_epl, soccer_uefa_champs_league, tennis_atp,
tennis_wta, cricket_big_bash, cricket_ipl, baseball_mlb
```

---

## 🧪 Local Development Workflow

### First-Time Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
# Expected: (.venv) PS C:\EVisionBetCode>

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Create .env file
copy .env.example .env
# Edit and add ODDS_API_KEY from The Odds API

# 4. Verify setup
python -c "import pandas; import sqlalchemy; print('✅ Setup OK')"
```

### Run Pipeline

```bash
# Extract odds from API (uses API credits, ~1-2 min)
python src/pipeline_v2/extract_odds.py
# → Output: data/raw_odds_pure.csv

# Calculate EV opportunities (no API calls, <30 sec)
python src/pipeline_v2/calculate_opportunities.py
# → Output: data/ev_opportunities.csv

# Start API server (for local testing)
uvicorn backend_api:app --reload
# → Test: curl http://localhost:8000/api/ev/hits?limit=5
```

### Pre-Commit Checks (Before Pushing)

```bash
make pre-commit  # Format + lint + type-check + test

# Or run individually:
make format      # Black + isort (auto-fix code style)
make lint        # Flake8 + pylint (check code quality)
make type-check  # mypy (check type hints)
make test        # pytest (run unit tests)
```

---

## 🔧 Critical Design Patterns

⚠️ **These are essential. Don't change them without understanding implications.**

- ✅ **Always use `get_data_dir()`** – Never hardcode `/data` paths
- ✅ **DB primary, CSV fallback** – Writes to both; if DB fails, CSV still succeeds
- ✅ **Group player props by 5-tuple** – `(sport, event_id, market, point, player_name)`
- ✅ **Sharp book weighting** – Only use 3⭐/4⭐ books for fair odds
- ✅ **Separate weight totals** – Different totals for Over vs. Under
- ✅ **Deduplication** – Check `seen_hits.json` before writing EV hits
- ✅ **Graceful degradation** – Skip unsupported props, exclude <2 sharp books
- ✅ **Config via env vars** – Never hardcode API keys or database URLs

---

## 🚀 Render Deployment

### Create Services (via GitHub + Render)

Three services defined in `render.yaml`:

| Service | Type | Schedule | Function |
|---------|------|----------|----------|
| `evision-extract-odds` | Cron | Every 30 min | Fetch odds from API → `raw_odds_pure` table |
| `evision-calculate-ev` | Cron | +5 min after extract | Calculate EV → `ev_opportunities` table |
| `evision-api` | Web | 24/7 | FastAPI service → `/api/ev/hits` |

### Deployment Steps

1. **Verify `.env` is git-ignored** (added to `.gitignore`)

2. **Set environment variables on Render services:**
   - Go to each service → **Environment**
   - Add:
     ```
     ODDS_API_KEY=your_actual_key
     DATABASE_URL=postgresql://user:pw@dpg-xxxxx.render.com:5432/dbname
     ```

3. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

4. **Monitor logs:**
   - Render dashboard → Service → Logs
   - Extract should write to `raw_odds_pure` table
   - Calculate should process & write to `ev_opportunities` table
   - API should serve data at `/api/ev/hits`

---

## 💡 Common Tasks

### Check API Credits Remaining
```bash
python -c "
import os, requests
api_key = os.getenv('ODDS_API_KEY')
resp = requests.get('https://api.the-odds-api.com/v4/sports', params={'apiKey': api_key})
print(f'Remaining: {resp.headers.get(\"x-requests-remaining\", \"N/A\")}')
"
```

### Force Fresh Data (Local)
```bash
# Clear cached data
rm data/raw_odds_pure.csv data/ev_opportunities.csv

# Re-fetch and calculate
python src/pipeline_v2/extract_odds.py
python src/pipeline_v2/calculate_opportunities.py
```

### Use Custom Sports (Render)
On Render, set `SPORTS` env var:
```
SPORTS=basketball_nba,americanfootball_nfl,baseball_mlb
```
Next cron run automatically uses new list (no code changes).

### Test Without API Calls
```bash
# Only calculate (uses existing raw odds)
python src/pipeline_v2/calculate_opportunities.py
```

### Verify Database Connection
```bash
python -c "
import os
from sqlalchemy import create_engine, text
db_url = os.getenv('DATABASE_URL')
if db_url:
    engine = create_engine(db_url)
    result = engine.execute(text('SELECT 1'))
    print('✅ Database connected')
else:
    print('❌ DATABASE_URL not set')
"
```

---

## 🚨 Troubleshooting

| Issue | Error | Fix |
|-------|-------|-----|
| **No data fetched** | 0 rows extracted | Check `ODDS_API_KEY` in `.env`, verify API key is active |
| **Missing Python module** | `ModuleNotFoundError: pandas` | Activate venv: `. .venv/Scripts/Activate.ps1`, reinstall: `pip install -e ".[dev]"` |
| **Pylance false errors** | Red squiggles in editor | Restart VS Code: `Ctrl+Shift+P` → "Developer: Reload Window" |
| **Path error on Render** | `/opt/render/project/src/src/data` | Fixed in v2 (see `get_data_dir()` in scripts) |
| **Database connection fails** | `postgresql://` error | Check `DATABASE_URL` format, hostname, credentials |
| **Formatter doesn't auto-run** | Files not formatted on save | Check: `"editor.formatOnSave": true` in VS Code settings |
| **Calculation takes 5+ min** | Stuck/slow processing | Verify `raw_odds_pure.csv` has >1000 rows |
| **API not responding** | Connection refused | Check if `uvicorn` process is running: `uvicorn backend_api:app --reload` |

---

## 📞 Need Help?

- **VS Code setup issues?** → [VSCODE_SETUP.md](VSCODE_SETUP.md)
- **Pipeline architecture questions?** → [src/pipeline_v2/README.md](src/pipeline_v2/README.md)
- **Fair odds math?** → [docs/BUGFIX_FAIR_ODDS_DEC10_2025.md](docs/BUGFIX_FAIR_ODDS_DEC10_2025.md)
- **Render deployment?** → [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)
- **API documentation?** → [BACKEND_API_DEPLOYMENT.md](BACKEND_API_DEPLOYMENT.md)

---

## 🎯 Next Steps

1. ✅ **Read** [VSCODE_SETUP.md](VSCODE_SETUP.md) (10 min setup)
2. ✅ **Run locally** (Quick Start section, above)
3. ✅ **Test pipeline** (extract → calculate → API)
4. 🔄 **Deploy to Render** (if production ready)
5. 🔄 **Monitor cron jobs** (Render dashboard)
6. 🔄 **Celebrate!** 🎉

---

**Version:** 2.0 (Pipeline V2 + Parallel Processing)  
**Frontend:** [EVisionBetSite](https://github.com/patrickmcsweeney81/EVisionBetSite)  
**Maintainer:** Patrick McSweeney

