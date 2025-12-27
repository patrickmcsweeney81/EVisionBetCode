# EVisionBet - Daily Commands Quick Reference

**Copy & paste the commands you use most often**

---

## 🚀 Start All Services (Development)

### Terminal 1: Backend API
```powershell
cd C:\EVisionBetCode
.\.venv\Scripts\Activate.ps1
uvicorn backend_api:app --reload
# API running on http://localhost:8000
```

### Terminal 2: Frontend Dev Server
```powershell
cd C:\EVisionBetSite\frontend
npm start
# Frontend on http://localhost:3000 (hot reload enabled)
```

### Terminal 3: Python Commands (as needed)
```powershell
cd C:\EVisionBetCode
.\.venv\Scripts\Activate.ps1
# Ready for pipeline, tests, formatting commands below
```

---

## 📊 Pipeline Commands

### Extract NBA Odds (Fresh Data)
```bash
python pipeline_v3.py --sports basketball_nba
# Output: data/v3/extracts/basketball_nba_raw_YYYYMMDD_HHMMSS.csv
```

### Extract NFL Odds
```bash
python pipeline_v3.py --sports americanfootball_nfl
# Output: data/v3/extracts/americanfootball_nfl_raw_YYYYMMDD_HHMMSS.csv
```

### Merge Sport to all_raw.csv
```bash
python merge_to_all_raw.py basketball_nba
# Deduplicates and merges into data/all_raw.csv
```

### Calculate EV Opportunities (v2 pipeline)
```bash
python src/pipeline_v2/calculate_opportunities.py
# Reads: data/raw_odds_pure.csv
# Output: data/ev_opportunities.csv
```

### Run Full Pipeline (v2)
```bash
python src/pipeline_v2/extract_odds.py && python src/pipeline_v2/calculate_opportunities.py
# Complete v2 workflow
```

---

## 🧪 Testing & Quality

### Run All Tests
```bash
pytest --cov=src --cov-report=term-missing
```

### Run Tests Fast (skip slow tests)
```bash
pytest -m "not slow" -v
```

### Run Specific Test File
```bash
pytest tests/test_base_extractor.py -v
```

### Format All Code (Black)
```bash
black src/
```

### Organize Imports (isort)
```bash
isort src/ --profile=black
```

### Lint Code (Flake8)
```bash
flake8 src/ --max-line-length=100
```

### Type Check (MyPy)
```bash
mypy src/ --ignore-missing-imports
```

### Run All Pre-Commit Checks
```bash
make pre-commit
# Runs: black, isort, flake8, pylint, mypy, pytest
```

---

## 🛠️ Useful Commands

### Check Python Version & Path
```bash
python --version
python -c "import sys; print(sys.executable)"
```

### List Installed Packages
```bash
pip list | grep -E "pandas|fastapi|sqlalchemy|requests"
```

### Reinstall Dependencies
```bash
pip install -e ".[dev]"
```

### Create Fresh venv (emergency reset)
```bash
rm -r .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Check if Port 8000 is in use
```powershell
netstat -ano | findstr 8000
```

### Kill Process on Port 8000
```powershell
$PID = (Get-NetTCPConnection -LocalPort 8000).OwningProcess
Stop-Process -Id $PID -Force
```

---

## 🌐 API Testing (Keybindings or Thunder Client)

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Raw Odds (limit 5)
```bash
curl "http://localhost:8000/api/odds/raw?limit=5"
```

### Get EV Opportunities
```bash
curl "http://localhost:8000/api/ev/hits?limit=5"
```

### Get Bookmakers List
```bash
curl "http://localhost:8000/api/bookmakers"
```

### Get Specific Sport Odds
```bash
curl "http://localhost:8000/api/odds/raw?sport=basketball_nba&limit=10"
```

---

## 📁 Important File Paths

| Path | Purpose |
|------|---------|
| `C:\EVisionBetCode\.env` | API keys & secrets |
| `C:\EVisionBetCode\pyproject.toml` | Python dependencies |
| `C:\EVisionBetCode\pipeline_v3.py` | Main entry point (v3) |
| `C:\EVisionBetCode\src\v3\extractors\` | Sport extractors |
| `C:\EVisionBetCode\data\v3\extracts\` | Raw extracts |
| `C:\EVisionBetCode\data\all_raw.csv` | Merged all sports |
| `C:\EVisionBetSite\frontend\package.json` | Frontend dependencies |
| `C:\EVisionBetCode\backend_api.py` | FastAPI endpoints |

---

## ⌨️ VS Code Keyboard Shortcuts (Custom)

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+T` | Run all tests (pytest) |
| `Ctrl+Shift+E` | Extract odds (NBA) |
| `Ctrl+Shift+C` | Calculate EV |
| `Ctrl+Alt+F` | Format current file |
| `Ctrl+Shift+P` | Command palette (built-in) |
| `Ctrl+J` | Toggle terminal (built-in) |
| `Ctrl+\`` | New terminal (built-in) |

---

## 🔍 Common Troubleshooting

### Frontend won't start (ENOENT: no such file)
```bash
cd C:\EVisionBetSite\frontend
rm -r node_modules
npm install
npm start
```

### Backend port 8000 already in use
```powershell
# Find and kill process:
$PID = (Get-NetTCPConnection -LocalPort 8000).OwningProcess
Stop-Process -Id $PID -Force
# Then restart backend
```

### Python ImportError
```bash
# Ensure venv is active:
# Should see (.venv) prefix in terminal
.\.venv\Scripts\Activate.ps1
# Reinstall packages:
pip install -e ".[dev]"
```

### Excel cache showing old CSV data
```
Close Excel completely
Delete file from C:\EVisionBetCode\data\
Re-run extraction
Open fresh copy in Excel
```

---

## 📈 Makefile Commands (Legacy)

```bash
make dev-install      # Install dev dependencies
make test             # Run pytest with coverage
make lint             # Run flake8 + pylint
make format           # Run black + isort
make type-check       # Run mypy
make pre-commit       # Run all quality checks
make clean            # Remove cache files
```

---

## 💡 Pro Tips

1. **Terminal 1-3 Always Running:**
   - Keep backend, frontend, and Python terminals open during dev
   - Switch between them with `Ctrl+J` (VS Code)

2. **Thunder Client > Manual curl:**
   - Saved requests are faster and clearer
   - See in QUICK_ACTION_PLAN.md for setup

3. **Hot Reload Magic:**
   - Frontend: Save JS → see change in 1 sec
   - Backend: Save Python → auto-restarts
   - CSV: Pipeline creates new timestamped file

4. **Data Flow:**
   - Extract → CSV with all bookmakers
   - Merge → all_raw.csv with deduplication
   - Calculate → ev_opportunities.csv with EV hits

5. **Quick Quality Check:**
   - Before commit: `make pre-commit`
   - Takes ~5 sec, catches all issues

---

**Last Updated:** December 27, 2025
**Status:** Production Ready
