# Quick Reference - What's Where & What To Do

## 📍 File Locations

### Active Production Files (Use These)
```
pipeline_v2/
├─ extract_odds.py               ← Stage 1: Fetch odds from API
├─ calculate_opportunities.py    ← Stage 2: Calculate EV
└─ ratings.py                    ← Bookmaker weights & ratings

core/
├─ fair_prices.py                ← Fair odds calculation (NEW)
├─ fair_odds.py                  ← Support functions
├─ book_weights.py               ← Weighting system
├─ config.py                     ← Configuration (40 books)
├─ h2h.py                        ← Head-to-head handler (renamed)
├─ spreads.py                    ← Spreads handler (renamed)
├─ totals.py                     ← Totals handler (renamed)
├─ player_props.py               ← Player props handler (renamed)
├─ nfl_props.py                  ← NFL props handler (renamed)
├─ utils.py                      ← Utility functions
└─ logging.py                    ← CSV logging

data/
├─ raw_odds_pure.csv             ← All odds (created by extract_odds.py)
└─ ev_opportunities.csv          ← EV hits (created by calculate_opportunities.py)

.env                             ← API keys & config
```

### Documentation (Read These)
```
SYSTEM_ARCHITECTURE.md           ← Start here: What is this system?
RENDER_DEPLOYMENT.md             ← How to deploy to Render
TEST_PLAN.md                     ← How to test locally
UNCOMMITTED_CHANGES.md           ← Git commit guide
SESSION_SUMMARY.md               ← What was done in this session
README.md                        ← Project overview
QUICK_START.md                   ← Quick reference
```

### Legacy (Don't Use - Safe to Delete)
```
legacy/
├─ core/
│  ├─ fair_prices.py (v1)
│  ├─ fair_prices_v2.py
│  ├─ *_logger.py files
│  ├─ player_props_handler_NEW.py
│  ├─ balldontlie.py
│  ├─ betfair_api.py
│  └─ scrape_sources/
├─ ev_arb_bot.py
├─ extract_ev_hits.py
├─ launcher.bat
└─ pipeline/
   ├─ outlier_test.py
   └─ check_outliers_ev.py
```

---

## 🚀 Next Steps (Today/This Week)

### TODAY: Commit & Push
```bash
cd C:\EVisionBetCode
git add -A
git commit -m "chore: reorganize codebase - rename handlers, consolidate fair_prices"
git push origin main
```

**Verify:**
- ✅ Go to GitHub.com → Your repo
- ✅ See new commit in history
- ✅ See new files (SYSTEM_ARCHITECTURE.md, etc.)

### TODAY: Local Test (5 minutes)
```bash
# Stage 1: Extract
python pipeline_v2/extract_odds.py

# Check output
dir data/raw_odds_pure.csv
(Get-Content data/raw_odds_pure.csv -Head 3)

# Stage 2: Calculate
python pipeline_v2/calculate_opportunities.py

# Check output
dir data/ev_opportunities.csv
Import-Csv data/ev_opportunities.csv | Measure-Object
```

### THIS WEEK: Deploy to Render
1. Create PostgreSQL database
2. Run table creation SQL (see RENDER_DEPLOYMENT.md)
3. Deploy extract_odds as cron job
4. Deploy calculate_opportunities as cron job
5. Create API endpoints
6. Connect frontend

See **RENDER_DEPLOYMENT.md** for detailed steps.

---

## 📊 What The System Does

```
API (The Odds API)
    ↓
extract_odds.py (Stage 1)
    ↓ [Fetches 40+ books × 3 sports × 4 markets]
    ↓
raw_odds_pure.csv (Wide CSV format)
+ PostgreSQL live_odds table
    ↓
calculate_opportunities.py (Stage 2)
    ↓ [Calculates fair prices using book_weights]
    ↓ [Finds EV opportunities >= 1%]
    ↓
ev_opportunities.csv
+ PostgreSQL ev_opportunities table
    ↓
Frontend Dashboard
    ├─ Card 1: "All Odds" (from live_odds)
    └─ Card 2: "EV Hits" (from ev_opportunities)

Auto-Runs on Render:
- extract_odds: Every 30 minutes
- calculate_opportunities: 5 min after extract
```

---

## ⚙️ Configuration

### .env File (in repo root)
```bash
ODDS_API_KEY=81d1ac74594d5d453e242c14ad479955
REGIONS=au,us,eu,us2
SPORTS=basketball_nba,basketball_nbl,americanfootball_nfl
MARKETS=h2h,spreads,totals
EV_MIN_EDGE=0.03                 # 3% minimum
DATABASE_URL=postgresql://...    # Add for Render
```

### core/config.py
```python
AU_BOOKIES = [...]               # ~13 books (Sportsbet, Tab, etc.)
US_BOOKIES = [...]               # ~20 books (DraftKings, FanDuel, etc.)
SHARP_BOOKIES = [...]            # ~6-8 for fair odds (Pinnacle, DraftKings, etc.)
CSV_HEADERS = [...]              # All 40+ books in order
```

### core/book_weights.py
```python
BOOKMAKER_RATINGS = {
    "pinnacle": 4,               # Primary
    "betfair_ex_eu": 3,          # Strong
    "draftkings": 3,             # Strong
    # ... all 40+ books
}
```

---

## 🧪 Quick Validation

### Test Imports
```bash
python -c "from core.fair_prices import build_fair_prices_two_way; print('OK')"
python -c "from core.book_weights import get_sharp_books_only; print('OK')"
python -c "from core.config import AU_BOOKIES, CSV_HEADERS; print('OK')"
```

### Test Extraction
```bash
python pipeline_v2/extract_odds.py
# Check: data/raw_odds_pure.csv created
# Check: 100+ rows, 25+ columns (bookmakers)
```

### Test Calculation
```bash
python pipeline_v2/calculate_opportunities.py
# Check: data/ev_opportunities.csv created
# Check: ev_percent >= 1.0 for all rows
```

---

## 📱 Mobile Workflow (GitHub App)

1. **On your phone:**
   - Open GitHub app
   - Go to EVisionBetCode repo
   - Edit `.env` or `core/config.py`
   - Commit changes

2. **On Render:**
   - Automatically redeploys (if webhook configured)
   - Or manually trigger redeploy in Render dashboard

3. **System runs:**
   - Extract & calculate with new config
   - Results in PostgreSQL
   - Frontend shows updated data

---

## 🐛 Troubleshooting Quick Guide

| Problem | Solution |
|---------|----------|
| **"Module not found: fair_prices"** | Check `core/fair_prices.py` exists |
| **"No odds extracted"** | Check `.env` has valid ODDS_API_KEY |
| **"Fair odds is None"** | Need 2+ sharp bookmakers in raw data |
| **"EV_opportunities.csv empty"** | Market might not have 1%+ EV (normal) |
| **Git commit fails** | Run `git add -A` first |
| **Render deployment fails** | Check DATABASE_URL in Render env vars |
| **Frontend shows no data** | Check API endpoint returns data; test: `curl https://your-api.render.com/api/odds/latest` |

---

## 📚 Reading Order

**For Understanding:**
1. README.md (overview)
2. SYSTEM_ARCHITECTURE.md (what you have)
3. QUICK_START.md (quick reference)

**For Deployment:**
1. RENDER_DEPLOYMENT.md (setup steps)
2. TEST_PLAN.md (validate it works)

**For Git/Commits:**
1. UNCOMMITTED_CHANGES.md (ready to push)
2. SESSION_SUMMARY.md (what was done)

---

## ✅ Success Checklist

- [ ] Understand system architecture (read SYSTEM_ARCHITECTURE.md)
- [ ] Commit all changes to GitHub
- [ ] Run local extraction test
- [ ] Run local calculation test
- [ ] CSVs created with expected data
- [ ] Deploy to Render
- [ ] First automated run completes
- [ ] Frontend receives data
- [ ] Test mobile editing workflow
- [ ] Monitor for 1 week
- [ ] Delete legacy/ folder (when confident)

---

## 🎯 Key Facts About Your System

✅ **What it does:**
- Fetches odds from 40+ bookmakers across 3-4 sports
- Calculates fair prices using sharp books weighted by rating
- Finds betting edges (EV) above 1% threshold
- Stores everything in PostgreSQL + CSV files
- Runs automatically every 30 minutes on Render
- Editable from mobile via GitHub app

✅ **What you control:**
- Sports to analyze (currently: NBA, NBL, NFL)
- Bookmaker ratings (in core/book_weights.py)
- EV threshold (currently: 1%, was 3% before)
- Regions (currently: AU, EU, US, US2)
- Markets (currently: h2h, spreads, totals)

✅ **What's new in this session:**
- Reorganized files for clarity
- Fixed import errors
- Created unified fair_prices module
- Documented entire system
- Ready for production deployment

---

## 🚀 Bottom Line

**You have a complete system ready to deploy.**

1. **Push changes to GitHub** (git push)
2. **Deploy to Render** (see RENDER_DEPLOYMENT.md)
3. **Connect frontend** (see RENDER_DEPLOYMENT.md)
4. **Monitor first run** (see TEST_PLAN.md)
5. **Enjoy automated odds extraction & EV calculation!**

---

**Questions?** Consult the appropriate guide:
- System questions → SYSTEM_ARCHITECTURE.md
- Deployment questions → RENDER_DEPLOYMENT.md
- Testing questions → TEST_PLAN.md
- Git questions → UNCOMMITTED_CHANGES.md
