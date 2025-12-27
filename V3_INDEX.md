'
/# EVisionBet v3 - Complete Index & Getting Started

**Welcome!** You now have a fresh, modular architecture ready for production.

---

## 📖 Read These First (In Order)

1. **[V3_BUILD_SUMMARY.md](V3_BUILD_SUMMARY.md)** (5 min)
   - What was delivered
   - Problems solved
   - Quick overview

2. **[V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md)** (10 min)
   - Setup on new machine
   - Configuration guide
   - Cost analysis

3. **[V3_QUICK_REFERENCE.md](V3_QUICK_REFERENCE.md)** (Keep open!)
   - Commands you'll use daily
   - Configuration changes
   - Copy-paste patterns

4. **[src/v3/README.md](src/v3/README.md)** (Deep dive)
   - Architecture details
   - Database schema
   - Frontend expansion ideas

---

## 🚀 30-Second Start

```bash
cd C:\EVisionBetCode
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
echo ODDS_API_KEY=your_key > .env
python pipeline_v3.py --sports basketball_nba
```

✅ Done! Check: `data/v3/extracts/nba_raw.csv`

---

## 🎯 What You Have Now

### ✅ Modular Extractors
- Per-sport files (not monolithic)
- Easy to debug & tune individually
- Copy-paste pattern to add sports

### ✅ Fixed Fair Odds Math
- Separate weight totals for Over/Under
- No more bugs from v2
- Comprehensive logging

### ✅ Enhanced Data Format
- 17 columns with metadata
- Bookmaker ratings & categories
- Ready for analytics

### ✅ Configuration-Driven
- No hardcoding
- Change weights/ratings without coding
- Enable/disable sports easily

### ✅ Comprehensive Documentation
- 4 main guides
- Code comments
- Self-documenting config

---

## 📁 Directory Guide

```
EVisionBetCode/
├── V3_BUILD_SUMMARY.md          ← Start here
├── V3_MIGRATION_GUIDE.md        ← Then here
├── V3_QUICK_REFERENCE.md        ← Keep open
├── pipeline_v3.py               ← Main entry point
│
├── src/v3/                      ← ALL NEW CODE
│   ├── README.md                ← Architecture
│   ├── config.py                ← Configuration
│   ├── base_extractor.py        ← Base class
│   ├── extractors/
│   │   ├── nba_extractor.py     ← Copy this
│   │   ├── nfl_extractor.py     ← Copy this
│   │   └── __init__.py
│   ├── processors/
│   │   ├── fair_odds_v2.py      ← Fair odds (FIXED)
│   │   └── ev_calculator.py     ← TODO: EV detection
│   └── tests/                   ← Unit tests
│
├── data/v3/                     ← NEW DATA
│   ├── extracts/                ← Individual sports
│   ├── calculations/            ← EV hits
│   └── merged/                  ← Combined output
│
├── src/pipeline_v2/             ← Legacy (keep for ref)
├── src/legacy/                  ← Legacy (keep for ref)
├── backend_api.py               ← Existing (use v3/ data)
└── pyproject.toml               ← Dependencies
```

---

## 💡 Quick Decisions

### "Should I understand the code first?"
**Yes!** Read in this order:
1. `src/v3/config.py` (what gets configured)
2. `src/v3/base_extractor.py` (how extraction works)
3. `src/v3/extractors/nba_extractor.py` (example)

**Time:** ~30 minutes

### "Should I add more sports now?"
**No.** Get the two (NBA, NFL) working perfectly first. Pattern is identical for all.

### "Should I implement EV calculator now?"
**Optional.** Extract is standalone. Calculate separately when ready.

### "Should I use database?"
**No.** CSVs work fine. Add database later if you need time-series.

---

## 🔄 Workflow Overview

### Daily Development
```bash
# 1. Make changes to a sport extractor
# 2. Test just that sport
python pipeline_v3.py --sports basketball_nba

# 3. Check output
head data/v3/extracts/nba_raw.csv

# 4. Verify merged
python pipeline_v3.py --merge-only
```

### Adding a New Sport
```bash
# 1. Copy an extractor
cp src/v3/extractors/nba_extractor.py src/v3/extractors/tennis_extractor.py

# 2. Customize it
# 3. Register in pipeline_v3.py
# 4. Test
python pipeline_v3.py --sports tennis_atp tennis_wta
```

### Debugging
```bash
# 1. Add logging to extractor
logger.debug("Here's what I found...")

# 2. Run just that sport
python pipeline_v3.py --sports basketball_nba

# 3. Check logs and output CSV
```

---

## ⚡ Commands You'll Use Most

```bash
# Run single sport
python pipeline_v3.py --sports basketball_nba

# Run 2-3 sports
python pipeline_v3.py --sports basketball_nba americanfootball_nfl icehockey_nhl

# Merge existing (no API calls)
python pipeline_v3.py --merge-only

# Check output
head -5 data/v3/extracts/nba_raw.csv
wc -l data/v3/merged/all_raw_odds.csv

# Test code quality
pytest
black src/v3
```

---

## 🎓 Learning Path (1-2 Hours)

**Hour 1: Understand Structure**
1. Read: `V3_BUILD_SUMMARY.md` (what was built)
2. Read: `src/v3/config.py` (skim, understand sections)
3. Read: `src/v3/base_extractor.py` (understand methods)
4. Read: `src/v3/extractors/nba_extractor.py` (see example)

**Hour 2: Hands-On**
1. Run: `python pipeline_v3.py --sports basketball_nba`
2. Check: `data/v3/extracts/nba_raw.csv` (look at actual data)
3. Edit: Disable one bookmaker in `config.py`
4. Run: Again to see difference

---

## ⚠️ Common Mistakes (Avoid These!)

❌ **Don't:** Edit `base_extractor.py` unless you know what you're doing  
✅ **Do:** Override methods in your sport extractor

❌ **Don't:** Hardcode values in extractors  
✅ **Do:** Add to `config.py`, import with `from src.v3.config import ...`

❌ **Don't:** Run all 12 sports until NBA/NFL work perfectly  
✅ **Do:** Test 1-2 sports, fine-tune, add more

❌ **Don't:** Delete v2/legacy code  
✅ **Do:** Keep for reference until v3 is proven

---

## 📊 Architecture at a Glance

```
┌──────────────┐
│ The Odds API │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ config.py (Sports, Books)│
└──────┬───────────────────┘
       │
  ┌────┴─────────────────────┐
  │                           │
  ▼                           ▼
┌─────────────┐          ┌──────────────┐
│ NBA Extract │          │ NFL Extract  │
└─────┬───────┘          └──────┬───────┘
      │                         │
      ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ nba_raw.csv  │          │ nfl_raw.csv  │
└──────┬───────┘          └──────┬───────┘
       │                         │
       └────────────┬────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Merge (orchestrator) │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ all_raw_odds.csv     │
         │ (for backend/frontend)
         └──────────────────────┘
```

---

## ✅ Your First Steps (Today)

### Step 1: Setup (5 min)
```bash
cd C:\EVisionBetCode
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
echo ODDS_API_KEY=your_real_key > .env
```

### Step 2: Test (2 min)
```bash
python pipeline_v3.py --sports basketball_nba
# Should complete with ✓
```

### Step 3: Verify (1 min)
```bash
head data/v3/extracts/nba_raw.csv
# Should show headers and data rows
```

### Step 4: Read Documentation (15 min)
- Read: `V3_MIGRATION_GUIDE.md`
- Read: `src/v3/README.md`
- Bookmark: `V3_QUICK_REFERENCE.md`

### Step 5: Explore Code (15 min)
- Open: `src/v3/config.py`
- Scroll through (understand structure)
- Open: `src/v3/extractors/nba_extractor.py`
- Understand how it uses config

**Total time:** ~40 minutes to be productive

---

## 🤔 FAQ

**Q: Do I need to implement everything?**  
A: No. Extract works now. EV calculation is next phase.

**Q: Can I use this with old backend?**  
A: Yes. Just change file path from `data/raw_odds_pure.csv` → `data/v3/merged/all_raw_odds.csv`

**Q: How do I add a new sport?**  
A: Copy `nba_extractor.py`, customize, register in `pipeline_v3.py`. Done!

**Q: What if an API call fails?**  
A: BaseExtractor handles it. Check logs. Likely API rate limit or key issue.

**Q: Should I use database?**  
A: CSVs work great. Add database later for analytics.

---

## 🔗 Quick Links

| File | Purpose |
|------|---------|
| [V3_BUILD_SUMMARY.md](V3_BUILD_SUMMARY.md) | What was built |
| [V3_MIGRATION_GUIDE.md](V3_MIGRATION_GUIDE.md) | How to setup |
| [V3_QUICK_REFERENCE.md](V3_QUICK_REFERENCE.md) | Commands & config |
| [src/v3/README.md](src/v3/README.md) | Architecture deep dive |
| [src/v3/config.py](src/v3/config.py) | Configuration reference |
| [src/v3/base_extractor.py](src/v3/base_extractor.py) | Base class |
| [src/v3/extractors/nba_extractor.py](src/v3/extractors/nba_extractor.py) | Example to copy |
| [src/v3/processors/fair_odds_v2.py](src/v3/processors/fair_odds_v2.py) | Fair odds math |
| [pipeline_v3.py](pipeline_v3.py) | Main entry point |

---

## 🎉 You're Ready!

Everything is built and documented. You have:

✅ Modular, maintainable code  
✅ Fixed fair odds calculation  
✅ Per-sport configuration  
✅ Enhanced data format  
✅ Comprehensive guides  

**Start with:** `python pipeline_v3.py --sports basketball_nba`

**Then read:** `V3_MIGRATION_GUIDE.md`

**Questions?** See `V3_QUICK_REFERENCE.md` FAQ or code comments.

---

**Status:** 🟢 Ready to Go  
**Version:** 3.0.0  
**Date:** December 25, 2025  

Happy coding! 🚀
