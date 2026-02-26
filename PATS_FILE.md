# 📋 PATS_FILE - START HERE
**For Any AI Model Reading This Project**

---

## 🎯 YOUR INSTRUCTIONS

**Read these files IN ORDER to understand the complete workflow:**

### 1. **THIS FILE** (2 min) ✓ You're reading it now
   - Current status snapshot
   - What was just completed
   - Critical project facts

### 2. **Backend Setup & Architecture** (10 min)
   - **Read:** [EVisionBetCode/README.md](README.md)
   - **Purpose:** Understand V3 extraction, data pipeline, backend API
   - **Key files:** `extract_nba_v3.py`, `backend_api.py`, `bookmaker_ratings.py`

### 3. **Frontend Setup & React Flow** (10 min)
   - **Read:** [EVisionBetSite/README.md](../EVisionBetSite/README.md)
   - **Purpose:** React components, TypeScript, API integration
   - **Key files:** Frontend config, components, state management

### 4. **Verify Everything Locally** (5 min)
   ```bash
   # Backend
   cd C:\EVisionBetCode
   python extract_nba_v3.py
   uvicorn backend_api:app --reload
   
   # Frontend (separate terminal)
   cd C:\EVisionBetSite\frontend
   npm start
   ```

---

## 📍 CURRENT STATUS (January 13, 2026 - Local Timestamps + Pats Picks)

| Component | Status | Details |
|-----------|--------|---------|
| **NBA Extraction** | ✅ Production | `extract_nba_v3.py` → Raw odds, local timestamps |
| **NFL Extraction** | ✅ Production | `extract_nfl_v3.py` → Raw odds, local timestamps |
| **NBA Filtering** | ✅ Production | `filter_nba_v3.py` → Composite Key pairing |
| **NFL Filtering** | ✅ Production | `filter_nfl_v3.py` → Composite Key pairing |
| **Composite Key Algorithm** | ✅ Production | Groups by (event, market_type, point, player_name) |
| **Strict Spreads Validator** | ✅ Production | +x/-x enforcement, multi-sport support |
| **Outlier Detection** | ✅ Production | MAD-based filtering (NBA + NFL) |
| **EV Calculation** | ✅ Production | De-vigging, fair odds, 47-column output |
| **Pipeline Orchestrator** | ✅ Production | `orchestrate_pipeline.py` → Parallel execution, audit |
| **Pats Picks Generator** | ✅ NEW | `generate_pats_picks.py` → Custom filtered CSV with Kelly |
| **Backend API** | ✅ Ready | FastAPI on :8000, CORS enabled, reads latest CSV |
| **Frontend** | ✅ Ready | React 19 + TypeScript on :3000 |
| **Git Repos** | ✅ Clean | main branch, ready to commit |
| **Documentation** | ✅ Updated | PATS_FILE.md updated with latest features |

**Just Completed (Jan 13, Latest):**
- ✅ Changed timestamps from UTC to local time (AWST UTC+8)
- ✅ Created `generate_pats_picks.py` for custom filtered output
- ✅ Pats_Picks.csv filters: +EV only, fair odds < 2.5
- ✅ Kelly column with Excel formula (auto-updates, rounded to $5)
- ✅ Removed columns: sport, event_id, extracted_at, pair_id
- ✅ Formula: `=MROUND(MAX(0, 1000 * ((I#/K#) - 1) / (I# - 1)), 5)`

**Previous Completion (Jan 10):**
- ✅ Multi-sport pairing validator (NBA + NFL)
- ✅ Strict spreads +x/-x validator (7-point validation)
- ✅ All checks passing: NBA 728 pairs, NFL 461 pairs
- ✅ Updated PAIRING_IMPLEMENTATION_SUMMARY.md with latest status
- ✅ Validated cross-sport consistency (zero violations)
- ✅ Orchestrated pipeline tested: Extract → Filter → Manage → Calculate → Merge → Audit
- ✅ AllSports_EV.csv merged output: 6,270 rows (NBA 3,208 + NFL 2,766)
- ✅ Committed and pushed to GitHub (Commit: 7707182)

**Previous Completion (Jan 7, Earlier - Commit 73534fd):**
- ✅ Removed all period-specific markets (q1-q4, h1-h2) from extraction
- ✅ Removed h2h_3_way, halftime_fulltime, overtime from extraction (cleaner focus)
- ✅ Added overtime (Yes/No) to 2-way de-vigging
- ✅ Added player_threes_alternate to 2-way de-vigging (aligned with player_threes)
- ✅ Fixed book count bug: now uses actual CSV bookmakers (30) instead of dynamic extraction
- ✅ Removed duplicate columns at end of CSV output
- ✅ Changed to static filenames (no timestamping, overwrites each run)
- ✅ API credit savings: 1,239 → 1,077 credits/run (-13%)
- ✅ Data efficiency: 23,956 → 17,240 rows (-28%, better signal)
- ✅ Positive EV improved accuracy: -2.91% → -4.95% mean (better margin removal)
- ✅ Cleaned up 14 debug/analysis scripts from repo
- ✅ Pushed to GitHub (commit 73534fd)

**Production Data Pipeline (Current - Multi-Sport):**
```
Parallel Extraction (NBA + NFL)
    ↓
NBA_Raw.csv (11,669 rows) | NFL_Raw.csv (4,424 rows)
    ↓
Parallel Filtering (Composite Key pairing)
    ↓
NBA_Filtered.csv (1,456 rows, 728 pairs) | NFL_Filtered.csv (922 rows, 461 pairs)
    ↓
manage_allsports_ev.py (archive dated, keep 4 days)
    ↓
Parallel EV Calculation (fair odds + de-vigging)
    ↓
NBA_EV.csv | NFL_EV.csv
    ↓
Merge → AllSports_EV.csv (6,270 rows total)
    ↓
audit_pipeline.py (stage counts + line-loss)
    ↓
backend_api.py (serves merged AllSports_EV.csv)
    ↓
Frontend React app
```

**What's Active (12 Production Scripts):**
- extract_nba_v3.py / extract_nfl_v3.py - Fetch odds from API
- filter_nba_v3.py / filter_nfl_v3.py - Composite Key pairing + filtering
- outlier_nba_v3.py / outlier_nfl_v3.py - MAD-based outlier detection
- calculate_nba_ev_full.py / calculate_nfl_ev_full.py - Fair odds + EV calculation
- orchestrate_pipeline.py - Parallel multi-sport orchestrator
- manage_allsports_ev.py - Date archiving + retention (4 days)
- audit_pipeline.py - Stage counts + line-loss analysis
- validate_pairing_results.py - 7-point validation (NBA + NFL)
- backend_api.py - FastAPI server
- bookmaker_ratings.py - Bookmaker weight config

**Bookmaker Coverage (30 Total):**
- 4⭐ Sharp: pinnacle, betfair_ex_eu, matchbook, draftkings, fanduel, lowvig
- 0⭐ AU Targets: bet365, betfair_ex_au, sportsbet, dabble_au, pointsbetau, neds, ladbrokes_au, unibet, betright, betr_au, boombet, playup, tab, tabtouch
- 3⭐ Sharp: betonlineag, betmgm, betrivers, fanatics
- 2⭐ Decent: hardrockbet, williamhill_us, bovada, espnbet
- 1⭐ Soft: coolbet, fliff

**On Hold (Intentional):**
- Period-specific markets (q1-q4, h1-h2 removed for efficiency)
- h2h_3_way, halftime_fulltime, overtime markets (removed, not essential)
- Database/Postgres integration (CSV is source of truth)

---

## ✅ PRE-WORK CHECKLIST

Before you start ANY work:

- [ ] Read this PATS_FILE (you're here ✓)
- [ ] Read EVisionBetCode/README.md (backend overview)
- [ ] Read EVisionBetSite/README.md (frontend overview)
- [ ] Check `.env` has `ODDS_API_KEY` (ask Pat if missing)
- [ ] Verify Python venv: `python --version` → should be 3.10+
- [ ] Verify dependencies: `pip list | grep fastapi` → should be installed
- [ ] Verify data folder exists: `ls data/v3/extracts/`

**All checks pass?** → You're ready to work.

---

## 🔗 ONE SOURCE OF TRUTH

| What | Where | When to Read |
|-----|-------|--------------|
| **Backend setup & extraction** | [EVisionBetCode/README.md](README.md) | Starting backend work |
| **Frontend setup & React** | [EVisionBetSite/README.md](../EVisionBetSite/README.md) | Starting frontend work |
| **AI Agent guidelines** | [.github/copilot-instructions.md](.github/copilot-instructions.md) | For GitHub Copilot tasks |
| **Spreads/Totals Correct Structure** | [SPREADS_TOTALS_CORRECT_STRUCTURE.md](SPREADS_TOTALS_CORRECT_STRUCTURE.md) | Building EV calculation code |
| **Why Different Point Values** | [WHY_DIFFERENT_POINT_VALUES.md](WHY_DIFFERENT_POINT_VALUES.md) | Understanding vigorish/vig |
| **Legacy code reference** | [archive/README.md](archive/README.md) | Understanding old approaches |
| **This file** | PATS_FILE.md | Every session start |

**Rule:** All docs point to each other. No conflicting info.

---

## 🚀 COMMON WORKFLOWS

### Extract & Calculate Full Pipeline (One Command)
```bash
cd C:\EVisionBetCode
python run_nba_pipeline.py
# OR from VS Code: Ctrl+Shift+B → "🏀 NBA: Full Pipeline"
```
Output: Runs Extract → Filter → Outlier Detection → EV Calculation sequentially
Result: 1,102 lines with 29 positive EV opportunities

### Extract Fresh NBA Data (Raw)
```bash
python extract_nba_v3.py
# Output: data/v3/extracts/basketball_nba_raw.csv (3,496 rows)
```

### Filter NBA Data (Remove Low-Value Lines)
```bash
python filter_nba_v3.py
# Input: Latest basketball_nba_raw.csv
# Output: basketball_nba_filtered.csv (1,102 rows)
# Filters: sharp+AU books only, .5 increments, dedupe
```

### Detect Outliers
```bash
python outlier_nba_v3.py
# Input: Latest basketball_nba_filtered.csv
# Applies MAD-based outlier detection
```

### Calculate EV (Full Analysis - 46 Columns)
```bash
python calculate_nba_ev_full.py
# Input: Latest basketball_nba_filtered.csv
# Output: basketball_nba_ev_full.csv (1,102 rows, 46 columns)
# Fair odds: MAD-based consensus (rating-specific rules)
```

### Start Backend API (for testing)
```bash
cd C:\EVisionBetCode
uvicorn backend_api:app --reload --host 127.0.0.1 --port 8000
# Visit: http://localhost:8000/health
```

### Start Frontend (connects to backend)
```bash
cd C:\EVisionBetSite\frontend
npm start
# Visit: http://localhost:3000
# API auto-detects: http://localhost:8000
```

### Check Latest Data
```bash
ls -ltrh C:\EVisionBetCode\data\v3\extracts\
# Latest file is the newest extraction
```

### Git Status Check
```bash
cd C:\EVisionBetCode
git status
# Should be: "nothing to commit, working tree clean"
```

---

## 🤖 IF YOU'RE AN AI MODEL

**Your workflow each session:**

1. ✅ Read this file first (you are here)
2. ✅ Read the two main READMEs (backend & frontend)
3. ✅ Check git status: `git status` (should be clean)
4. ✅ Verify extraction works: `python extract_nba_v3.py`
5. ✅ Ask Pat if anything is unclear
6. 🔄 Proceed with the specific task

**Golden Rules:**
- This PATS_FILE is source of truth for workflow & status
- All docs are consolidated; no conflicting info elsewhere
- Data extraction is proven to work; focus on integration/features
- Archive folder contains old code for reference only
- Always commit changes and push when done
- If you add/change docs, update all references

**If Pat asks "what's our status?":**
1. Check this file (PATS_FILE)
2. Run `git status`
3. Check latest CSV timestamp
4. Report back with facts

---

## 💬 CRITICAL DECISIONS

**Q: Why is there no EV calculation pipeline in active code?**
→ It was v1/v2; v3 focuses on clean extraction + API serving. Archive has old code if needed.

**Q: Why are there no tests/ or requirements/ directories?**
→ Removed Dec 28. All dependencies in pyproject.toml now.

**Q: Why only one extraction script (extract_nba_v3.py)?**
→ Simplified, standardized, proven to work. Old scripts in archive/ if reference needed.

**Q: What about Postgres / Database?**
→ CSV is source of truth for now. No DB integration in current MVP.

**Q: How do I add a new sport?**
→ Modify extract_nba_v3.py to call different Odds API endpoint, save to new CSV path.

**Q: Can I run this on production (Render)?**
→ Yes. render.yaml has the config. Backend reads latest CSV from mounted /data dir.

---

## 📊 DATA FLOW (Current MVP)

```
The Odds API
    ↓
extract_nba_v3.py
    ↓
data/v3/extracts/basketball_nba_raw_*.csv (6,554 rows)
    ↓
filter_nba_v3.py (sharp + AU books, .5 increments, dedupe)
    ↓
data/v3/extracts/basketball_nba_filtered_*.csv (1,844 rows)
    ↓
calculate_nba_ev.py (clean) OR calculate_nba_ev_full.py (analysis)
    ↓
basketball_nba_ev_*.csv (9 cols) OR basketball_nba_ev_full_*.csv (44 cols)
    ↓
backend_api.py (reads latest EV CSV)
    ↓
FastAPI endpoints (/health, /api/csv, etc.)
    ↓
Frontend React app
    ↓
User sees EV opportunities
```

**No transformations after EV calculation, no DB, clean pipeline.**

---

## ☁️ REMOTE ACCESS & CLOUD

**Yes — the code is in GitHub. You can access it from anywhere.**

### Q: Can I access this remotely while away from my PC?

**Yes.** The project has two layers of cloud access:

| Layer | How | URL |
|-------|-----|-----|
| **Source Code** | GitHub repository | https://github.com/patrickmcsweeney81/EVisionBetCode |
| **Live API** | Render.com cloud deployment | See render.yaml (auto-deploys from `main` branch) |
| **Browser IDE** | GitHub Codespaces (no install needed) | Open repo on GitHub → click `Code` → `Codespaces` |

**From any device with a browser:**
1. Go to https://github.com/patrickmcsweeney81/EVisionBetCode
2. Click `Code` → `Codespaces` → `New codespace`
3. The full dev environment opens in the browser (no VS Code install needed)
4. Run the pipeline, edit code, and push changes — all from the browser

**Render runs the API 24/7** (see `render.yaml`) — the backend continues running even when your PC is off. It auto-re-deploys whenever you push to the `main` branch.

---

### Q: Can I find this AI chat in GitHub?

**The chat itself is not stored in GitHub, but your AI session context is.**

`PATS_FILE.md` (this file) **is the AI session memory.** Every time you commit it, the full project context is saved to GitHub. When you start a new AI session:

1. Any AI (Copilot, Claude, etc.) reads `PATS_FILE.md` first
2. It instantly knows: current status, completed tasks, active files, and what to do next
3. You pick up exactly where you left off — from any device

**To save your current chat context to GitHub:**
```bash
# After updating PATS_FILE.md with the latest status:
git add PATS_FILE.md
git commit -m "Update session context - <brief description>"
git push
```

**To resume a session on a new device:**
```bash
git pull  # Gets latest PATS_FILE.md
# Open GitHub Copilot Chat → "Read PATS_FILE.md and resume"
```

---

### Q: What runs in the cloud vs locally?

| Component | Cloud (always on) | Local (your PC) |
|-----------|-------------------|-----------------|
| API server | ✅ Render.com | ✅ localhost:8000 |
| Source code | ✅ GitHub | ✅ Cloned copy |
| Pipeline cron jobs | ✅ Render.com (every 30 min) | Manual run |
| Frontend | ✅ Deploy to Netlify | ✅ localhost:3000 |
| AI chat context | ✅ PATS_FILE.md in GitHub | ✅ Local copy |

---

## 🎯 NEXT STEPS

**Immediate:**
- [ ] Verify extraction works
- [ ] Verify backend API runs
- [ ] Verify frontend connects to backend
- [ ] All tests pass locally

**Roadmap:**
- New features requested by Pat
- Performance optimization if needed
- Add more sports (same pattern as NBA)
- Possible EV calculation pipeline (if business asks)

---

**Last Updated:** February 26, 2026  
**Status:** ✅ All systems operational, documentation consolidated, ready for development  
**Next Review:** When major changes made or Pat requests update

