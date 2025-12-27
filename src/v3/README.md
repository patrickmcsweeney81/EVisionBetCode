# EVisionBet v3 - Architecture & Migration Guide

**Status:** Fresh start with modular architecture  
**Date:** December 25, 2025  
**Version:** 3.0.0

---

## 📋 Overview

EVisionBet v3 is a **complete architectural redesign** addressing all issues from v1/v2:

✅ **Fair odds calculations fixed** - Separate weight totals for Over/Under  
✅ **Missing sports/markets** - Modular per-sport extractors  
✅ **Wrong data per sport** - Sport-specific configuration  
✅ **Cost/performance issues** - Optimized API calls per sport  
✅ **Hard to debug/tune** - Isolated testing per sport  

---

## 🏗️ Architecture

### New Directory Structure

```
EVisionBetCode/
├── src/v3/                          ← NEW modular architecture
│   ├── __init__.py
│   ├── config.py                    Config: sports, bookmakers, weights, EV thresholds
│   ├── base_extractor.py            Base class: common extraction logic
│   │
│   ├── extractors/                  Sport-specific extractors
│   │   ├── __init__.py
│   │   ├── nba_extractor.py         NBA: 7 player props, 48h window
│   │   ├── nfl_extractor.py         NFL: 4 player props, 168h window
│   │   └── [other sports]           → Add as needed
│   │
│   ├── processors/                  Data processing & calculation
│   │   ├── __init__.py
│   │   ├── fair_odds_v2.py          Fair odds (FIXED: separate weights)
│   │   ├── ev_calculator.py         EV detection from fair + best odds
│   │   └── deduplicator.py          Remove duplicate markets
│   │
│   └── tests/                       Sport-specific unit tests
│       ├── test_nba.py
│       ├── test_nfl.py
│       └── test_fair_odds_v2.py
│
├── data/v3/                         NEW structured data directories
│   ├── extracts/                    Individual sport CSVs
│   │   ├── nba_raw.csv              ← Output of NBAExtractor
│   │   ├── nfl_raw.csv              ← Output of NFLExtractor
│   │   └── [sport]_raw.csv
│   │
│   ├── calculations/                EV hits per sport
│   │   ├── nba_ev.csv
│   │   ├── nfl_ev.csv
│   │   └── [sport]_ev.csv
│   │
│   └── merged/                      Combined outputs (for backend)
│       ├── all_raw_odds.csv         All sports merged
│       └── all_ev_hits.csv          All EV opportunities
│
├── pipeline_v3.py                   ← NEW main entry point (orchestrator)
├── backend_api.py                   ← EXISTING (adapt to read v3/)
├── src/pipeline_v2/                 ← LEGACY (keep for reference)
└── src/legacy/                      ← LEGACY (keep for reference)
```

---

## 🚀 Quick Start

### 1. Run All Sports

```bash
cd C:\EVisionBetCode
python pipeline_v3.py
```

This will:
1. Run NBA extractor → `data/v3/extracts/nba_raw.csv`
2. Run NFL extractor → `data/v3/extracts/nfl_raw.csv`
3. Merge both → `data/v3/merged/all_raw_odds.csv`

### 2. Run Specific Sport(s)

```bash
python pipeline_v3.py --sports basketball_nba americanfootball_nfl
```

### 3. Merge Only (Use Existing Extracts)

```bash
python pipeline_v3.py --merge-only
```

---

## 🎯 Key Design Decisions

### 1. **Per-Sport Extractors (Not Monolithic)**

**Why:** Each sport has different:
- Markets (NBA has more props than cricket)
- Time windows (NFL is weekly, NBA is every 2 days)
- Regions (some AU-only, some worldwide)
- Bookmaker coverage (AU books vs US vs EU)

**Benefit:** Fine-tune each sport independently without affecting others.

**Example:** If NBA props are broken, fix only `nba_extractor.py`, not 12-sport pipeline.

---

### 2. **Base Extractor Class (DRY)**

All sport extractors inherit common logic:
- API authentication & request handling
- Data validation
- CSV output formatting
- Error handling & retries
- Time window filtering

**Code reuse:** ~200 lines shared vs. duplicated in 12 sport files.

---

### 3. **Config-Driven (Not Hardcoded)**

**Bookmaker Ratings** (`config.py`):
```python
BOOKMAKER_RATINGS = {
    "pinnacle": {"stars": 4, "category": "sharp"},
    "sportsbet": {"stars": 1, "category": "target"},
}
```

**Sport Profiles** (`config.py`):
```python
SPORTS_CONFIG = {
    "basketball_nba": {
        "regions": ["au", "us", "eu"],
        "player_props": ["player_points", ...],
        "time_window_hours": 48,
    }
}
```

**Weights** (`config.py`):
```python
SPORT_WEIGHT_PROFILES = {
    "basketball_nba": {
        "pinnacle": 0.40,
        "draftkings": 0.35,
        "fanduel": 0.25,
    }
}
```

**Benefit:** Change rating/weight without editing Python files.

---

### 4. **Separated Extraction & Calculation**

**Extraction** (`pipeline_v3.py`):
- Calls Odds API
- Writes raw CSVs
- ~2 min for all sports

**Calculation** (NOT YET IMPLEMENTED):
- Reads raw CSVs
- Calculates fair odds (with FairOddsCalculatorV2)
- Calculates EV%
- Writes EV CSVs
- ~30 sec

**Benefit:** Rerun calculation without API costs. Use cached data for testing.

---

## 🐛 Bug Fixes (v2 → v3)

### Fair Odds Over/Under Bug (FIXED)

**Problem (v2):**
```python
# BROKEN: Used single weight total for both sides
total_weight = sum(w for _, w in over_weighted)
fair_over = sum(o*w for o,w in over_weighted) / total_weight  ✓
fair_under = sum(o*w for o,w in under_weighted) / total_weight  ❌ WRONG!
```

If Over had 5 books and Under had 3, this gave wrong Under odds.

**Solution (v3):**
```python
# FIXED: Separate weight totals per side
over_weight_total = sum(w for _, w in over_weighted)
under_weight_total = sum(w for _, w in under_weighted)

fair_over = sum(o*w for o,w in over_weighted) / over_weight_total  ✓
fair_under = sum(o*w for o,w in under_weighted) / under_weight_total  ✓
```

See `src/v3/processors/fair_odds_v2.py` for full implementation.

---

## 📊 Enhanced Data Storage (For Frontend Expansion)

### New CSV Columns (All Raw Odds)

```csv
extracted_at, sport, league, event_id, event_name, commence_time,
market_type, point, selection, player_name,
bookmaker, stars_rating, odds_decimal, implied_prob,
is_sharp, is_target, notes
```

**New fields:**
- `stars_rating` - Bookmaker strength (1-4)
- `is_sharp`, `is_target` - Category
- `implied_prob` - Auto-calculated

**Analytics possibilities:**
- Track sharp vs target odds per sport
- Identify unreliable bookmakers
- Monitor line movement

---

### Suggested Database Schema (PostgreSQL)

If using database instead of CSVs:

```sql
-- Events (de-duplicated)
CREATE TABLE events (
    event_id VARCHAR(100) PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    event_name VARCHAR(200),
    commence_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Markets (event + market_type + selection combos)
CREATE TABLE markets (
    market_id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) REFERENCES events(event_id),
    market_type VARCHAR(50),
    point DECIMAL(6,2),
    selection VARCHAR(200),
    player_name VARCHAR(200),
    UNIQUE(event_id, market_type, point, selection)
);

-- Odds (one row per bookmaker per market)
CREATE TABLE odds (
    odds_id SERIAL PRIMARY KEY,
    market_id INT REFERENCES markets(market_id),
    bookmaker VARCHAR(50),
    stars_rating INT,
    odds_decimal DECIMAL(10,2),
    implied_prob DECIMAL(5,3),
    extracted_at TIMESTAMP,
    INDEX (market_id, bookmaker, extracted_at)
);

-- Fair Odds & EV
CREATE TABLE ev_calculations (
    calc_id SERIAL PRIMARY KEY,
    market_id INT REFERENCES markets(market_id),
    fair_odds DECIMAL(10,2),
    sharp_count INT,
    sharp_books_used VARCHAR(500),  -- "Pinnacle,DraftKings"
    ev_percent DECIMAL(5,2),
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Daily Analytics
CREATE TABLE daily_analytics (
    date DATE,
    sport VARCHAR(50),
    league VARCHAR(100),
    total_opportunities INT,
    avg_ev_percent DECIMAL(5,2),
    max_ev_percent DECIMAL(5,2),
    sharp_coverage_pct DECIMAL(5,2),
    extraction_cost INT,  -- API credits
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Frontend analytics with this:**
- "EV by Sport" pie chart (from daily_analytics)
- "Sharp Book Comparison" (from ev_calculations + odds)
- "Historical Trends" (time-series from daily_analytics)
- "Data Quality %" (based on sharp_count)

---

## 🔄 Migration Path (Current → v3)

### Phase 1: Set Up v3 (DONE ✓)
- ✅ Created directory structure
- ✅ Created base extractor
- ✅ Created NBA & NFL extractors
- ✅ Created pipeline orchestrator
- ✅ Created FairOddsCalculatorV2

### Phase 2: Implement Calculation
- ⏳ Create EV calculator (uses fair_odds_v2.py)
- ⏳ Create deduplicator
- ⏳ Create backend adaptor (read v3/ CSVs)
- ⏳ Unit tests for each component

### Phase 3: Add More Sports
- ⏳ NHL extractor
- ⏳ Soccer extractors (EPL, Champions League)
- ⏳ Tennis extractors (ATP, WTA)
- ⏳ Cricket extractors (Big Bash, IPL)
- ⏳ Baseball (MLB), NCAAF, NBL

### Phase 4: Optimize & Deploy
- ⏳ Cost benchmarking
- ⏳ Performance optimization
- ⏳ Database integration (if needed)
- ⏳ Deploy to Render with v3

### Phase 5: Frontend Expansion
- ⏳ Add analytics pages
- ⏳ Add historical trending
- ⏳ Add sharp book comparison
- ⏳ Add data quality monitoring

---

## 🧪 Testing Strategy

### Unit Tests (Per Extractor)

```python
# tests/test_nba.py
def test_nba_base_markets():
    extractor = NBAExtractor()
    markets = extractor.fetch_odds()
    assert len(markets) > 0
    assert all("event_id" in m for m in markets)

def test_nba_time_window():
    extractor = NBAExtractor()
    markets = extractor.fetch_odds()
    # All should be within 48h window
    assert all(extractor._is_event_in_window(m["commence_time"]) for m in markets)
```

### Fair Odds Unit Tests

```python
# tests/test_fair_odds_v2.py
def test_separate_weight_totals():
    calc = FairOddsCalculatorV2()
    market = {
        "over_odds": [1.90, 1.88],
        "under_odds": [1.77, 1.75, 1.74],  # 3 books vs 2
        "over_books": ["pinnacle", "draftkings"],
        "under_books": ["pinnacle", "draftkings", "fanduel"],
    }
    fair_over, fair_under, _, _, _ = calc.calculate_fair_odds("basketball_nba", market)
    # Under should NOT use weight total from Over
    assert fair_under > 1.85  # Correct value
    assert fair_under < 2.00  # Not artificially low
```

---

## 📝 Configuration Reference

### Enable/Disable Sports

Edit `src/v3/config.py`:
```python
SPORTS_CONFIG = {
    "basketball_nba": {"enabled": True, ...},
    "americanfootball_ncaaf": {"enabled": False, ...},  # Disabled
}
```

### Change Bookmaker Rating

Edit `src/v3/config.py`:
```python
BOOKMAKER_RATINGS = {
    "sportsbet": {"stars": 1, "category": "target"},  # Change from 1 to 2
}
```

### Adjust EV Threshold

Edit `src/v3/config.py`:
```python
EV_CONFIG = {
    "min_ev_percent": 2.0,  # Change from 2.0 to 1.5 for more sensitive
}
```

### Change Sport Weights

Edit `src/v3/config.py`:
```python
SPORT_WEIGHT_PROFILES = {
    "basketball_nba": {
        "pinnacle": 0.50,  # Increased from 0.40
        "draftkings": 0.30,
        "fanduel": 0.20,
    }
}
```

---

## ❓ FAQ

**Q: Do I need to rewrite my backend?**  
A: No. Backend can keep reading CSVs. Just point it to `data/v3/merged/all_raw_odds.csv` instead of `data/raw_odds_pure.csv`.

**Q: Can I run NBA without NFL?**  
A: Yes! `python pipeline_v3.py --sports basketball_nba`

**Q: What if I want to add a new sport?**  
A: Create `src/v3/extractors/[sport]_extractor.py`, inherit from `BaseExtractor`, implement `fetch_odds()`, add to `EXTRACTORS` in pipeline.

**Q: How do I debug a specific sport?**  
A: Edit the extractor, add `logger.debug()` statements, run just that sport with `--sports [key]`.

**Q: Will v3 work with Render?**  
A: Yes. Render cron job will call `python pipeline_v3.py`, output goes to `data/v3/`, backend reads from there.

---

## 🔗 References

- [FairOddsCalculatorV2 Docs](fair_odds_v2.py)
- [Config Reference](config.py)
- [Base Extractor Class](base_extractor.py)
- [Pipeline Orchestrator](../../pipeline_v3.py)

---

**Status:** 🟡 Work in Progress (Extraction & Config complete, Calculation TBD)  
**Next Steps:** Implement EV calculator, add more sports, unit tests
