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

## 📍 CURRENT STATUS (December 28, 2025)

| Component | Status | Details |
|-----------|--------|---------|
| **NBA Extraction (V3)** | ✅ Working | `extract_nba_v3.py` → 286 rows, 53 bookmakers |
| **Backend API** | ✅ Ready | FastAPI on :8000, CORS enabled |
| **Frontend** | ✅ Ready | React 19 + TypeScript on :3000 |
| **Git Repos** | ✅ Clean | main branch only, 0 PRs, no dangling branches |
| **Documentation** | ✅ Consolidated | PATS_FILE, READMEs, copilot-instructions only |
| **Code Quality** | ✅ Clean | Old docs/tests/configs removed, only active code remains |

**Just Completed (Dec 28):**
- Removed 36 stale files (old docs, analysis scripts, caches, configs)
- Deleted all old CSV files (kept only latest: `basketball_nba_raw_20251228_110850.csv`)
- Consolidated documentation to single source of truth
- Fixed data extraction bug: spreads/totals now preserve all bookmaker line variations

**What's Active:**
- Extract: `extract_nba_v3.py` (single entry point)
- Backend: `backend_api.py` (FastAPI + CSV reader)
- Config: `bookmaker_ratings.py` (book weights), `pyproject.toml` (deps)
- Data: Latest CSV in `data/v3/extracts/`

**On Hold (Intentional):**
- EV calculation pipeline (secondary feature, not part of current MVP)
- Database/Postgres integration (CSV is source of truth for now)
- Advanced scheduling/automation (manual runs only)

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
| **Legacy code reference** | [archive/README.md](archive/README.md) | Understanding old approaches |
| **This file** | PATS_FILE.md | Every session start |

**Rule:** All docs point to each other. No conflicting info.

---

## 🚀 COMMON WORKFLOWS

### Extract Fresh NBA Data
```bash
cd C:\EVisionBetCode
python extract_nba_v3.py
# Check: data/v3/extracts/basketball_nba_raw_*.csv
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
data/v3/extracts/basketball_nba_raw_*.csv
    ↓
backend_api.py (reads latest CSV)
    ↓
FastAPI endpoints (/health, /api/csv, etc.)
    ↓
Frontend React app
    ↓
User sees EV opportunities
```

**No transformations, no DB, no complex logic.** Just extraction → serving.

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

