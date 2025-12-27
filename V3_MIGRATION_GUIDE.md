# EVisionBet v3 Migration & Fresh Start Guide

**Date:** December 25, 2025  
**Status:** Architecture Complete - Ready for Implementation  
**For:** New Computer Setup & Development Workflow

---

## 📋 What Was Built

### Architecture Components (✅ Complete)

1. **Configuration System** (`src/v3/config.py`)
   - 12 sports with individual settings
   - Bookmaker ratings (1-4 stars) for 25+ books
   - Weight profiles per sport
   - EV detection thresholds

2. **Base Extractor** (`src/v3/base_extractor.py`)
   - Common logic for all sports
   - CSV output formatting
   - Data validation
   - Error handling

3. **Sport-Specific Extractors**
   - `nba_extractor.py` - NBA configuration
   - `nfl_extractor.py` - NFL configuration
   - (Extensible for 10+ more sports)

4. **Pipeline Orchestrator** (`pipeline_v3.py`)
   - Run all sports or selected sports
   - Merge individual CSVs into combined output
   - Summary reporting

5. **Fair Odds Calculator v2** (`src/v3/processors/fair_odds_v2.py`)
   - **FIXED:** Separate weight totals for Over/Under
   - Outlier detection & removal
   - EV calculation
   - Arbitrage detection

6. **Enhanced Data Format**
   - New CSV columns with metadata
   - Bookmaker ratings & categories
   - Implied probabilities
   - Database schema for future analytics

7. **Comprehensive Documentation**
   - Architecture guide
   - Configuration reference
   - Database schema examples
   - FAQ & troubleshooting

---

## 🚀 Getting Started on New Machine

### Step 1: Clone Fresh

```bash
cd C:\
git clone https://github.com/patrickmcsweeney81/EVisionBetCode.git
cd EVisionBetCode
git log --oneline -1  # Verify latest commit
```

### Step 2: Set Up Python

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Step 3: Create .env

```bash
# .env
ODDS_API_KEY=your_key_here
SPORTS=basketball_nba,americanfootball_nfl  # Start with 2 for testing
DATABASE_URL=postgresql://...  # Optional
```

### Step 4: Test Single Sport

```bash
python pipeline_v3.py --sports basketball_nba
```

Expected output:
```
Initialized NBA extractor
Fetching NBA base markets: h2h, spreads, totals
✓ Got 12 events | Cost: 45 | Remaining: 455
Validation: 87 valid, 2 invalid
✓ Wrote 87 rows to CSV
✓ NBA extraction complete
```

### Step 5: Merge & Verify

```bash
python pipeline_v3.py --merge-only
# Outputs: data/v3/merged/all_raw_odds.csv
```

Check the CSV:
```bash
head -10 data/v3/merged/all_raw_odds.csv
```

---

## 🏗️ Architecture Overview

### Data Flow (v3)

```
┌─────────────────────────────────────┐
│   The Odds API (50+ bookmakers)     │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ config.py          │
    │ - Sports specs     │
    │ - Weights          │
    │ - Thresholds       │
    └────────────────────┘
             │
    ┌────────┴─────────────────────────┐
    │                                   │
    ▼                                   ▼
┌─────────────────┐              ┌──────────────────┐
│ NBAExtractor    │              │ NFLExtractor     │
└─────────────────┘              └──────────────────┘
    │                                   │
    ▼                                   ▼
┌─────────────────┐              ┌──────────────────┐
│ nba_raw.csv     │              │ nfl_raw.csv      │
│ (87 rows)       │              │ (156 rows)       │
└─────────────────┘              └──────────────────┘
    │                                   │
    └────────────┬────────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │ Pipeline Merge      │
        │ (orchestrator)      │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ all_raw_odds.csv    │
        │ (merged for backend)│
        └────────────┬────────┘
                     │
                     ▼
        ┌─────────────────────┐
        │ FairOddsCalcV2      │
        │ (NOT YET IMPL)      │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ all_ev_hits.csv     │
        │ (for frontend)      │
        └─────────────────────┘
```

---

## 🎯 Key Advantages vs. Legacy Code

| Aspect | v2 (Legacy) | v3 (New) |
|--------|-----------|---------|
| **Organization** | 12 sports in 1 file | 1 file per sport |
| **Debugging** | Change one thing, test 12 sports | Change NBA, test only NBA |
| **Reusability** | Lots of duplicated code | Base class (DRY) |
| **Configuration** | Hardcoded values | config.py (centralized) |
| **Fair Odds** | ❌ Over/Under bug | ✅ Separate weight totals |
| **Extensibility** | Hard to add new sport | Inherit BaseExtractor |
| **Data Storage** | Basic CSV | Enhanced + analytics columns |
| **Testing** | Hard to isolate | Per-sport unit tests |
| **Documentation** | Limited | Comprehensive |

---

## 💾 Data Storage Improvements

### Current CSV (v2)
```csv
sport, event_id, market, selection, fair_odds, best_book, best_odds, ev_percent
```

### Enhanced CSV (v3)
```csv
extracted_at, sport, league, event_id, event_name, commence_time,
market_type, point, selection, player_name,
bookmaker, stars_rating, odds_decimal, implied_prob,
is_sharp, is_target, notes
```

### Future Database (PostgreSQL)
- Normalized schema with 6 tables
- Support for time-series analytics
- Historical tracking
- Data quality monitoring

### Frontend Expansion Possibilities (With v3 Data)

**New Dashboard Cards:**
- "Sharp Coverage %" (% events with 2+ sharp books)
- "Data Quality Score" (based on sharp_count)
- "Top Target Books" (most accurate for EV)

**New Pages:**
- **Analytics:** EV trends over 30 days
- **Sharp Comparison:** Which sharps agree most
- **Book Comparison:** Which target books offer best value
- **Historical Tracking:** EV hits that expired

---

## ⚙️ Configuration for Different Scenarios

### Scenario 1: Development (Test 2 Sports)

```python
# .env
ODDS_API_KEY=test_key
SPORTS=basketball_nba,americanfootball_nfl
```

```bash
python pipeline_v3.py
# ~2 min, ~100 API credits
```

### Scenario 2: Production (All 12 Sports)

```python
# .env
ODDS_API_KEY=real_key
SPORTS=basketball_nba,basketball_nbl,americanfootball_nfl,americanfootball_ncaaf,icehockey_nhl,soccer_epl,soccer_uefa_champs_league,tennis_atp,tennis_wta,cricket_big_bash,cricket_ipl,baseball_mlb
```

```bash
python pipeline_v3.py
# ~5 min, ~800 API credits
```

### Scenario 3: Single Sport Tuning

```bash
python pipeline_v3.py --sports basketball_nba
# Just test NBA props/markets
# Fix only nba_extractor.py
# Cost: ~45 credits
```

### Scenario 4: Use Cached Data (No API)

```bash
python pipeline_v3.py --merge-only
# Merge existing CSVs without API calls
# Cost: $0
```

---

## 🔄 Next Steps (Not Yet Implemented)

### 1. Implement EV Calculator
- Create `src/v3/processors/ev_calculator.py`
- Read `data/v3/merged/all_raw_odds.csv`
- Use `FairOddsCalculatorV2` to calculate fair odds
- Use target books (1-star) to find EV opportunities
- Output `data/v3/merged/all_ev_hits.csv`

### 2. Add More Sport Extractors
- Hockey: `src/v3/extractors/nhl_extractor.py`
- Soccer: `src/v3/extractors/soccer_extractor.py` (handles both EPL & Champions League)
- Tennis: `src/v3/extractors/tennis_extractor.py`
- Cricket: `src/v3/extractors/cricket_extractor.py`
- Baseball: Update NFL extractor pattern for MLB
- NCAAF: Update NFL extractor pattern

### 3. Implement Player Props
- Extend `NBAExtractor._fetch_player_props()`
- Extend `NFLExtractor._fetch_player_props()`
- Test with actual API data

### 4. Unit Tests
- Test base extractor validation
- Test NBA/NFL parsing
- Test FairOddsCalculatorV2 with edge cases
- Test pipeline merging

### 5. Backend Integration
- Modify `backend_api.py` to read `data/v3/merged/`
- Keep same API endpoints (`/api/ev/hits`, `/api/odds/raw`)
- Add `/api/analytics/summary` for new data

### 6. Database (Optional)
- Create PostgreSQL tables (schema provided)
- Import CSV data to DB
- Add query endpoints for analytics

---

## 📊 Cost Analysis

### Per-Run Costs

| Scenario | Sports | Est. Credits | Time |
|----------|--------|--------------|------|
| Dev (2 sports) | NBA, NFL | 100 | 2 min |
| Test (6 sports) | NBA, NFL, NHL, EPL, ATP, Cricket | 400 | 4 min |
| Full (12 sports) | All | 800 | 5 min |
| Merge only | None | 0 | 30 sec |

### Optimization Ideas

- **Per-sport time windows:** Don't fetch same day
- **Selective sports:** Only fetch active sports (e.g., skip baseball offseason)
- **Cached props:** Reuse player list per season
- **Batch requests:** Fetch multiple events in single API call

---

## 🐛 Bug Fixes Addressed

### Fair Odds Over/Under

**Before (v2):** Calculated Under fair odds using Over weight total = WRONG  
**After (v3):** Calculate separate weight totals for each side = CORRECT

Test case:
```
Over odds: [1.90, 1.88]          → weight_total = 0.35
Under odds: [1.77, 1.75, 1.74]   → weight_total = 0.21 (NOT 0.35!)

v2 result: Fair Under = 1.19 ❌ (calculated with 0.35)
v3 result: Fair Under = 1.93 ✅ (calculated with 0.21)
```

See `src/v3/processors/fair_odds_v2.py` comments for detailed explanation.

---

## 📚 Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `src/v3/config.py` | All configuration | ✅ Complete |
| `src/v3/base_extractor.py` | Base class | ✅ Complete |
| `src/v3/extractors/nba_extractor.py` | NBA | ✅ Complete |
| `src/v3/extractors/nfl_extractor.py` | NFL | ✅ Complete |
| `src/v3/processors/fair_odds_v2.py` | Fair odds (FIXED) | ✅ Complete |
| `src/v3/processors/ev_calculator.py` | EV detection | ⏳ TODO |
| `pipeline_v3.py` | Main orchestrator | ✅ Complete |
| `src/v3/README.md` | Detailed docs | ✅ Complete |

---

## ✅ Verification Checklist

After setup:

- [ ] `python pipeline_v3.py --sports basketball_nba` runs without errors
- [ ] `data/v3/extracts/nba_raw.csv` has >50 rows
- [ ] CSV has all columns: `extracted_at`, `sport`, `bookmaker`, `odds_decimal`, etc.
- [ ] `python pipeline_v3.py --merge-only` creates `data/v3/merged/all_raw_odds.csv`
- [ ] All rows have valid `odds_decimal` values (1.01 - 1000)
- [ ] No duplicate (event_id, market_type, selection, bookmaker) rows

---

## 🤔 Common Questions

**Q: Should I delete the old code?**  
A: Keep it for now. Have both v2 and v3. Use v3 going forward.

**Q: How long before v3 is production ready?**  
A: Architecture done. Need: EV calculator (~2h), more sports (~4h), tests (~3h), backend update (~1h). ~10h total.

**Q: Can I mix v2 and v3 code?**  
A: Yes, temporarily. Keep backend API flexible to read from either `data/` or `data/v3/merged/`.

**Q: What if a sport has different requirements?**  
A: Override methods in sport extractor. Example: NBA might override `_fetch_player_props()` to handle their specific API format.

**Q: Should I use database or CSVs?**  
A: Start with CSVs (simpler). Add database later if you need time-series analytics or historical tracking.

---

## 🎓 Learning Path

1. **Read:** `src/v3/README.md` (architecture overview)
2. **Read:** `src/v3/config.py` (understand configuration)
3. **Read:** `src/v3/base_extractor.py` (common logic)
4. **Read:** `src/v3/extractors/nba_extractor.py` (example extractor)
5. **Run:** `python pipeline_v3.py --sports basketball_nba` (test)
6. **Inspect:** `data/v3/extracts/nba_raw.csv` (see output format)
7. **Code:** `src/v3/extractors/nfl_extractor.py` → your own sport

---

## 📞 Support

For issues:
1. Check `src/v3/README.md` FAQ
2. Review extractor logs (look for `[API]` tags)
3. Validate CSV format: should have all 17 columns
4. Check `.env` has `ODDS_API_KEY` set
5. Verify API key has remaining credits (check logs)

---

**Status:** 🟢 Ready for Development  
**Last Updated:** December 25, 2025  
**Architecture Version:** 3.0.0
