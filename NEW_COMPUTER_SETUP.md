# EVisionBet - Current Status & New Computer Setup Guide
**Created:** December 28, 2025  
**For:** Fresh Start on New Computer  

---

## 🎯 WHERE YOU ARE RIGHT NOW

### ✅ Completed
- **V3 Standardized Extractor** (`extract_nba_v3.py`)
  - Produces clean 196×61 CSVs (8 core columns + 53 bookmakers)
  - Tested and working
  - Committed to git main

- **Backend API** (`backend_api.py`)
  - FastAPI server ready
  - Not yet connected to V3 CSV

- **Project Cleaned Up**
  - All old code in `archive/` for reference
  - Root folder focused on active files only
  - Everything committed to git

- **Documentation**
  - `V3_STANDARDIZED_SETUP.md` - Full setup guide
  - `README.md` - Quick reference
  - `archive/README.md` - Reference index

### ⏸️ ON HOLD (Intentional)
- **Backend-Frontend Integration** - Waiting for CSV quality work
- **Frontend Display** - Waiting for backend connection
- **Pipeline Scheduling** - Manual runs only for now
- **EV Calculations** - Not yet implemented

### 📊 CURRENT DATA
- Latest NBA CSV: `data/v3/extracts/basketball_nba_raw_20251228_*.csv`
- Contains: h2h, spreads, totals, h2h_lay markets
- 53 bookmakers: EU, US, AU, specialized regions

---

## 🚀 WHEN NEW COMPUTER ARRIVES

### Step 1: Clone Repository (15 min)
```bash
git clone https://github.com/your-repo/EVisionBetCode.git
cd EVisionBetCode

# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"
```

### Step 2: Setup .env (2 min)
```bash
# Create .env with API key
echo ODDS_API_KEY=your_key_here > .env
```

### Step 3: Verify Extraction Works (5 min)
```bash
python extract_nba_v3.py

# Should see:
# ✅ Found 9 events
# ✅ Extracted 196 rows
# ✅ Saved: data/v3/extracts/basketball_nba_raw_YYYYMMDD_HHMMSS.csv
```

### Step 4: Understand Current CSV (15 min)
```bash
# Open latest CSV
code data/v3/extracts/basketball_nba_raw_*.csv

# Review:
# - 8 core columns (event metadata)
# - 53 bookmakers (all with decimal odds)
# - Market types: h2h, spreads, totals, h2h_lay
# - All rows have full coverage or NaN (no fake data)
```

---

## 📋 CSV QUALITY FOCUS (Your Priority)

Before connecting to backend/frontend:

### 1. Verify Data Completeness
- [ ] All 53 bookmakers have columns
- [ ] No missing/corrupt odds values
- [ ] Market pairs matched (Over-Under, Both sides)
- [ ] Point values correct (no whole numbers except where needed)
- [ ] Event metadata accurate (team names, times, IDs)

### 2. Add Data Validation
Consider adding to `extract_nba_v3.py`:
```python
# Validate 2-way pairs
# Check for outlier odds
# Flag low-coverage lines
# Log data quality metrics
```

### 3. Test Expansion Capability
- [ ] Can easily add NFL, NHL, etc.
- [ ] CSV format stays consistent across sports
- [ ] Bookmaker list is comprehensive

### 4. Document Data Dictionary
Create `docs/CSV_FORMAT.md`:
- Explain each column
- Bookmaker coverage by region
- Market type definitions
- Known quirks/limitations

---

## 🔗 THEN (Not Yet)

Once CSV is stable and well-documented:

### 1. Connect Backend
Update `backend_api.py` to:
- Read latest CSV from `data/v3/extracts/`
- Parse bookmaker columns
- Calculate metrics (if needed)
- Serve via REST endpoints

### 2. Connect Frontend
React frontend reads from API:
- Display odds table
- Filter by market/team/bookmaker
- Show data refresh time

### 3. Optional: Add Calculations
- Fair odds (using sharp books)
- EV detection
- Implied probability
- Vig calculations

---

## 📁 PROJECT STRUCTURE (Remember)

```
EVisionBetCode/
├── extract_nba_v3.py              ← YOU RUN THIS
├── backend_api.py                 ← NOT YET CONNECTED
├── data/v3/extracts/              ← CSV OUTPUT
├── V3_STANDARDIZED_SETUP.md       ← FULL GUIDE
├── README.md                      ← QUICK START
├── archive/                       ← OLD CODE (reference)
└── [config files]
```

**Keep It Simple:**
- Only run `extract_nba_v3.py` manually
- Quality-check CSVs
- Document what you find
- Then expand

---

## 💾 GIT HISTORY (You're Safe)

Current commit: `9bb952f`
- Message: "V3 standardization: clean archive, create extract_nba_v3.py, consolidate documentation"
- All changes backed up
- Can revert anything anytime with `git revert <commit>`

---

## ❓ COMMON QUESTIONS FOR NEW COMPUTER

**Q: Should I use the same .env file?**
→ Yes, copy the same ODDS_API_KEY

**Q: Should I delete old CSVs?**
→ Keep them for comparison, archive if storage limited

**Q: Can I run backend/frontend together with extractor?**
→ Depends on new computer specs. Monitor CPU/RAM.

**Q: What if extraction fails on new computer?**
→ Check: API key valid, internet connection, Python 3.11+, dependencies installed

**Q: Should I change anything before running?**
→ No. Run as-is first, then modify based on what you learn.

---

## 📝 NOTES FOR YOURSELF

**Why you're doing this:**
- Ensure clean, reliable data before integration
- Understand system deeply (not just running it)
- Set up foundation for multi-sport expansion
- Avoid rework due to unclear requirements

**Key principle:**
- CSV quality first
- Integration second
- Optimization third

**What matters now:**
- Can you reliably extract 196 rows of clean data?
- Are all 53 bookmakers properly captured?
- Does the CSV structure support future expansion?

---

## ✅ CHECKLIST FOR NEW COMPUTER SETUP

- [ ] Git clone repository
- [ ] Create venv and install dependencies
- [ ] Configure .env with API key
- [ ] Run `python extract_nba_v3.py` successfully
- [ ] Verify CSV in `data/v3/extracts/`
- [ ] Review CSV structure (all 61 columns, 196 rows)
- [ ] Check bookmaker coverage (53 books present)
- [ ] Understand market types (h2h, spreads, totals, h2h_lay)
- [ ] Document any anomalies
- [ ] Read `V3_STANDARDIZED_SETUP.md` carefully
- [ ] Open this file again as reference

---

**You've got a solid foundation. New computer will let you focus on quality without system lag. Take time to understand the data before rushing to integration.**

Ready to go when your computer arrives! 🚀
