# 📋 PATS_FILE - START HERE
**For Any AI Model Reading This Project**

---

## 🎯 YOUR INSTRUCTIONS

**Read these files IN ORDER to understand the project:**

### 1. **QUICK STATUS** (This file - 2 min)
- Current date/time and status
- What just happened
- What's next

### 2. **SETUP GUIDES** (Choose one - 5 min)
- **New to project?** → Read `V3_STANDARDIZED_SETUP.md`
- **New computer arriving?** → Read `NEW_COMPUTER_SETUP.md`
- **Need reference?** → Read `archive/README.md`

### 3. **PROJECT STRUCTURE** (5 min)
- Read: `README.md` (main project overview)
- Check: Root folder file list
- Understand: What files are active vs archived

### 4. **VERIFY SETUP** (2 min)
- Check: `.env` exists and has `ODDS_API_KEY`
- Check: `pyproject.toml` dependencies installed
- Check: `.vscode/` folder has config

### 5. **CONFIRM EVERYTHING WORKS**
```bash
# Run this
python extract_nba_v3.py

# You should see:
# ✅ Found X events
# ✅ Extracted XXX rows
# ✅ Saved: data/v3/extracts/basketball_nba_raw_*.csv
```

---

## 📍 CURRENT STATUS

**As of: December 28, 2025**

| Item | Status |
|---|---|
| V3 Extractor | ✅ Working |
| CSV Output | ✅ 196 rows × 61 columns |
| Git Repo | ✅ Committed (9bb952f) |
| Backend API | ⏸️ Ready but not connected |
| Frontend | ⏸️ Ready but not connected |
| New Computer | ⏸️ Being built |

**What's Done:**
- Clean standardized extraction pipeline
- Comprehensive bookmaker coverage (53 books)
- Archive of old code for reference
- Documentation complete

**What's On Hold:**
- Backend-frontend integration (intentional, waiting for CSV quality work)
- EV calculations (not started)
- Scheduling/automation (manual runs only)

**What's Next:**
- New computer arrives
- Focus on CSV data quality
- Document findings
- THEN integrate with backend/frontend

---

## ✅ CHECKLIST - Is Everything Ready?

Before running anything, verify:

- [ ] Read this file (PATS_FILE.md) - you're doing it ✓
- [ ] Read `V3_STANDARDIZED_SETUP.md` or `NEW_COMPUTER_SETUP.md`
- [ ] Read `README.md` (project overview)
- [ ] `.env` has `ODDS_API_KEY` (ask Pat if missing)
- [ ] Python venv activated (`python --version` should be 3.11+)
- [ ] Dependencies installed (`pip list | grep pandas`)
- [ ] Can see `data/v3/extracts/` folder exists

**All good?** → Run: `python extract_nba_v3.py`

---

## 🔗 QUICK FILE REFERENCE

| File | Read When | Purpose |
|---|---|---|
| **V3_STANDARDIZED_SETUP.md** | Starting fresh | Complete setup guide |
| **NEW_COMPUTER_SETUP.md** | New computer | Setup instructions |
| **README.md** | Need overview | Quick project summary |
| **archive/README.md** | Need old code ideas | Reference old approaches |
| **.env** | Configuring API | API key storage |
| **extract_nba_v3.py** | Running extraction | Main executable |
| **backend_api.py** | Understanding backend | FastAPI code |

---

## 🤖 IF YOU'RE AN AI MODEL

1. **You just read this file** ✓
2. **Read all the files listed above** in order
3. **Verify setup** using the checklist
4. **Check git status** to see what's uncommitted
5. **Ask Pat** if anything is unclear or missing

**Golden Rule:** If Pat asks "what's our status?", read this file first, then reference the appropriate .md file.

---

## 💬 COMMON QUESTIONS

**Q: Where's the latest data?**
→ `data/v3/extracts/basketball_nba_raw_*.csv` (newest first)

**Q: How do I extract fresh data?**
→ `python extract_nba_v3.py`

**Q: Where's the old code?**
→ `archive/` folder (everything organized there)

**Q: What should I NOT do yet?**
→ Don't integrate with backend/frontend. Wait for new computer and CSV quality work.

**Q: Is everything tested?**
→ Extraction works perfectly. Backend/frontend not connected yet (intentional).

---

**Last Updated:** December 28, 2025  
**Next: Wait for new computer, focus on CSV quality**

