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

## 📍 CURRENT STATUS (January 7, 2026 - CLEANED UP)

| Component | Status | Details |
|-----------|--------|---------|
| **NBA Extraction (V3)** | ✅ Production | `extract_nba_v3.py` → **3,496 rows** |
| **NBA Filtering (V3)** | ✅ Production | `filter_nba_v3.py` → **1,102 rows** (sharp + AU books, dedupe) |
| **Outlier Detection** | ✅ Production | `outlier_nba_v3.py` → MAD-based filtering |
| **EV Calculation** | ✅ Production | `calculate_nba_ev_full.py` → 46 columns, MAD-based fair odds |
| **Pipeline Orchestrator** | ✅ New | `run_nba_pipeline.py` → All 4 stages in one command |
| **Backend API** | ✅ Ready | FastAPI on :8000, CORS enabled, reads latest CSV |
| **Frontend** | ✅ Ready | React 19 + TypeScript on :3000 |
| **Git Repos** | ✅ Clean | main branch, all debug scripts removed |
| **Documentation** | ✅ Updated | Consolidated and cleaned up |

**Just Completed (Jan 7, Latest):**
- ✅ Created `run_nba_pipeline.py` (Extract → Filter → Outlier → EV in one command)
- ✅ Removed 22 debug/test scripts (analyze_*, check_*, compare_*, debug_*, etc.)
- ✅ Removed old documentation (test reports, analysis, comparisons)
- ✅ Updated PATS_FILE.md with current status
- ✅ Updated README.md with orchestrator workflow

**Production Data Pipeline:**
```
extract_nba_v3.py (3,496 raw rows)
    ↓ (filter_nba_v3.py)
basketball_nba_filtered.csv (1,102 rows, sharp+AU books)
    ↓ (outlier_nba_v3.py)
Outlier detection applied
    ↓ (calculate_nba_ev_full.py)
basketball_nba_ev_full.csv (1,102 rows, 46 columns, MAD-based fair odds)
    ↓ (backend_api.py)
FastAPI /api/csv endpoint
    ↓ (frontend React)
User sees 29 positive EV opportunities
```

**What's Active:**
- **Scripts** (7 total): extract, filter, outlier, calculate, orchestrator, backend, ratings config
- **Backend**: FastAPI server reads latest CSV from `data/v3/extracts/`
- **Data**: Latest CSV output with fair odds (MAD-based), EV, and all bookmakers
- **Orchestration**: `run_nba_pipeline.py` (command: `python run_nba_pipeline.py`)

**On Hold (Intentional):**
- Period-specific markets (q1, h1, q2, etc. - can add if requested)
- Additional player props (blocks, steals, combos - available on demand)
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

