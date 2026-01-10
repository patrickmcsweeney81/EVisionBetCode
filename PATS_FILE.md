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

## 📍 CURRENT STATUS (January 10, 2026 - Multi-Sport Pipeline Complete)

| Component | Status | Details |
|-----------|--------|---------|
| **NBA Extraction** | ✅ Production | `extract_nba_v3.py` → Raw odds, 12 events |
| **NFL Extraction** | ✅ Production | `extract_nfl_v3.py` → Raw odds, 8 events |
| **NBA Filtering** | ✅ Production | `filter_nba_v3.py` → Composite Key pairing, 728 pairs |
| **NFL Filtering** | ✅ Production | `filter_nfl_v3.py` → Composite Key pairing, 461 pairs |
| **Composite Key Algorithm** | ✅ NEW | Groups by (event, market_type, point, player_name) |
| **Strict Spreads Validator** | ✅ NEW | +x/-x enforcement, multi-sport support |
| **Outlier Detection** | ✅ Production | MAD-based filtering (NBA + NFL) |
| **EV Calculation** | ✅ Production | De-vigging, fair odds, 47-column output |
| **Pipeline Orchestrator** | ✅ Production | `orchestrate_pipeline.py` → Parallel execution, audit |
| **Backend API** | ✅ Ready | FastAPI on :8000, CORS enabled, reads latest CSV |
| **Frontend** | ✅ Ready | React 19 + TypeScript on :3000 |
| **Git Repos** | ✅ Clean | main branch, all changes pushed to GitHub |
| **Documentation** | ✅ Updated | PAIRING_IMPLEMENTATION_SUMMARY.md added |

**Just Completed (Jan 10, Latest - Commit 7707182):**
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

**Last Updated:** December 28, 2025, 1:00 PM  
**Status:** ✅ All systems operational, documentation consolidated, ready for development  
**Next Review:** When major changes made or Pat requests update

