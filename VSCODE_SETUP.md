# VS Code Setup Guide for EV_ARB Bot

Complete guide to configure VS Code for local development.

## Step 1: Install Required Extensions

Open VS Code and go to **Extensions** (`Ctrl+Shift+X`):

### Essential Extensions
1. **Python** (by Microsoft)
   - ID: `ms-python.python`
   - Latest language support, debugging, terminal integration

2. **Pylance** (by Microsoft)
   - ID: `ms-python.vscode-pylance`
   - Smart IntelliSense, type hints, refactoring

3. **Black Formatter** (by Microsoft)
   - ID: `ms-python.black-formatter`
   - Auto-format code on save (PEP 8 compliant)

### Recommended Extensions
4. **Flake8** (by Microsoft)
   - ID: `ms-python.flake8`
   - Real-time linting (code quality warnings)

5. **isort** (by Microsoft)
   - ID: `ms-python.isort`
   - Auto-organize imports

6. **Git Graph** (by mhutchie)
   - ID: `mhutchie.git-graph`
   - Visual git history (optional, helpful)

## Step 2: Configure Python Interpreter

### Option A: Via Command Palette (Recommended)
1. Press `Ctrl+Shift+P`
2. Type `Python: Select Interpreter`
3. Choose `.venv\Scripts\python.exe`
4. Confirm: Status bar (bottom right) shows `.venv`

### Option B: Via settings.json
1. Press `Ctrl+Shift+P`
2. Type `Preferences: Open Settings (JSON)`
3. Add:
```json
{
  "python.defaultInterpreterPath": "C:\\EVisionBetCode\\.venv\\Scripts\\python.exe",
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

## Step 3: Activate Virtual Environment in Terminal

### PowerShell
```powershell
& C:\EVisionBetCode\.venv\Scripts\Activate.ps1
```

If you get an error like "execution policy", run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then rerun the activation script.

### Expected Prompt
```
(.venv) PS C:\EVisionBetCode>
```

The `(.venv)` prefix confirms the venv is active.

## Step 4: Install Dependencies

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or use make
make dev-install
```

Verify:
```bash
python --version  # Should be 3.9+
pip list | grep -E "pandas|sqlalchemy|fastapi"
```

## Step 5: Create .env File

In project root (`C:\EVisionBetCode\`), create `.env`:

```
ODDS_API_KEY=81d1ac74594d5d453e242c14ad479955
DATABASE_URL=postgresql://user:password@localhost:5432/evision
ADMIN_PASSWORD_HASH=your_hash_here
SPORTS=basketball_nba,basketball_nbl,americanfootball_nfl,americanfootball_ncaaf,icehockey_nhl,soccer_epl,soccer_uefa_champs_league,tennis_atp,tennis_wta,cricket_big_bash,cricket_ipl,baseball_mlb
MARKETS=h2h,spreads,totals
```

⚠️ **Never commit `.env`** – it's in `.gitignore`

## Step 6: Test Setup

### Python Import Test
```bash
python -c "import pandas; import sqlalchemy; import fastapi; print('✅ All deps installed')"
```

### Path Check
```bash
python -c "from pathlib import Path; import sys; sys.path.insert(0,'src/pipeline_v2'); from extract_odds import get_data_dir; print(f'Data dir: {get_data_dir()}')"
```

Expected: `C:\EVisionBetCode\data`

### Run Extract (First Time - Uses API Credits)
```bash
python src/pipeline_v2/extract_odds.py
```

Check output:
```
[OK] Data directory ready: C:\EVisionBetCode\data
[PARALLEL] Fetching 12 sports concurrently...
...
[CSV] Appended 6616 rows
[OK] 6616 rows written to database (raw_odds_pure)
[DONE] Total rows: 6616
[FILE] C:\EVisionBetCode\data\raw_odds_pure.csv
```

### Run Calculate (No API Calls)
```bash
python src/pipeline_v2/calculate_opportunities.py
```

Expected:
```
[OK] Read 22256 rows from C:\EVisionBetCode\data\raw_odds_pure.csv
...
Total opportunities across all sports: 288
[OK] Wrote 288 opportunities to C:\EVisionBetCode\data\ev_opportunities.csv
[DONE] Complete
```

## Step 7: Start API Locally

```bash
uvicorn backend_api:app --reload
```

Expected:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test in another terminal:
```bash
curl http://localhost:8000/health
# {"status":"ok","timestamp":"...","database":"connected"}

curl http://localhost:8000/api/ev/hits?limit=3
# [{"sport":"basketball_nba","event_id":"...","ev_percent":6.36,...}, ...]
```

## Step 8: Configure Linting & Formatting

### Enable Auto-Format on Save

Press `Ctrl+,` (Settings) or:
1. **View** → **Command Palette** → `Preferences: Open Settings (JSON)`
2. Add:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=120"],
  "python.formatting.blackArgs": ["--line-length=120"]
}
```

### Pre-Commit Checks (Before Pushing)

```bash
make pre-commit  # Runs: format, lint, type-check, test
```

## Step 9: Debug in VS Code

### Run Python File
1. Open any `.py` file
2. Click **Run** (▶) in top-right
3. Output appears in **Terminal** panel

### Debug with Breakpoints
1. Click left margin to set breakpoint (red dot)
2. Press `F5` to start debugger
3. Step through code with `F10`, `F11`, etc.

### Debug Configuration
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Extract Odds",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/pipeline_v2/extract_odds.py",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "ODDS_API_KEY": "81d1ac74594d5d453e242c14ad479955"
      }
    },
    {
      "name": "Calculate EV",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/pipeline_v2/calculate_opportunities.py",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

Then press `F5` to debug.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: pandas` | Activate venv: `. .venv/Scripts/Activate.ps1` |
| Pylance shows false errors | Restart VS Code (`Ctrl+Shift+P` → "Reload Window") |
| Formatter doesn't auto-run | Check settings: `editor.formatOnSave` should be `true` |
| Git shows all files as modified | Run `git config core.autocrlf false` |
| Python not found | Select interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter" |

## Quick Command Reference

```bash
# Activate venv (every new terminal)
& .\.venv\Scripts\Activate.ps1

# Install deps
pip install -e ".[dev]"

# Run pipeline
python src/pipeline_v2/extract_odds.py
python src/pipeline_v2/calculate_opportunities.py

# Run API
uvicorn backend_api:app --reload

# Pre-commit checks
make pre-commit

# Push to Render
git push origin main
```

---

**Setup complete!** You're ready to develop locally. See `README.md` for next steps.
