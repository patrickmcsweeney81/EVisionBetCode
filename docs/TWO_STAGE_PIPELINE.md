# TWO-STAGE RAW ODDS PIPELINE

## Phase 1: Pure Raw Data Extraction ✓ COMPLETE

### Files Created
- **`raw_odds_pure.py`** - Extracts raw odds from Odds API v4
- **`data/raw_odds_pure.csv`** - Output CSV (760 rows, 61 columns)

### What It Does
1. Fetches events for NBA & NFL
2. Gets all available markets (h2h, spreads, totals)
3. Collects odds from 40+ bookmakers across all regions (AU, US, US2, EU)
4. Pivots data: ONE ROW per market/selection, ALL bookmaker odds as columns
5. Formats all odds in decimal (never American format)

### Data Structure
```
timestamp | sport | event_id | away_team | home_team | commence_time | market | point | selection
Pinnacle | Betfair_EU | Betfair_AU | Draftkings | Fanduel | Betmgm | ... | Sportsbet | Tab | ... | (other bookies)
```

### Column Organization
- **Sharp books first** (13 cols): Pinnacle, Betfair_EU, Betfair_AU, Draftkings, Fanduel, Betmgm...
- **AU books** (13 cols): Sportsbet, Bet365, Pointsbet, Betright, Tab, Dabble...
- **US books** (7 cols): Caesars, Betrivers, Sugarhouse...
- **Unknown regional** (19 cols): Dynamically discovered

### Key Benefits
✓ **True raw data** - No calculations, pure facts from API
✓ **One row per market** - Easy to pivot, filter, analyze
✓ **All bookmakers visible** - Compare odds at a glance
✓ **Decimal format** - Ready for EV calculations
✓ **Extensible** - Add new bookmakers automatically
✓ **Cost efficient** - 24 API credits per full run

---

## Phase 2: EV Calculation & Analysis (READY TO BUILD)

### Files to Create
- **`calculate_ev.py`** - Processes raw_odds_pure.csv
- **`data/ev_opportunities.csv`** - High-EV bets only

### Calculation Pipeline
```
Raw odds CSV
    ↓
Group by (market, point, selection)
    ↓
Extract sharp book odds (Pinnacle, Betfair, DK, FD, BetMGM)
    ↓
Calculate fair odds (median of sharps)
    ↓
For each AU/US book:
  Calculate EV% = (book_odds / fair_odds) - 1
  Filter: EV% >= 3%
  Calculate probability & Kelly stake
    ↓
Write EV opportunities CSV
```

### Output Format (ev_opportunities.csv)
```
timestamp | sport | event | market | selection | best_book | odds | fair_odds | ev% | prob | stake
```

### Example Outputs
- Norman Powell Under 2.5 3PT @ Sportsbet 2.2 vs Fair 1.9 = +15.8% EV
- Over 193.5 @ DraftKings 1.95 vs Fair 1.92 = +1.6% EV
- (Shows only edge >= 3%)

---

## Architecture Benefits

### 1. Separation of Concerns
- **Extraction** (raw_odds_pure.py): Get data, no logic
- **Calculation** (calculate_ev.py): Pure math, reusable
- **Analysis** (filter_ev_hits.py): Business rules, alerts

### 2. Recalculation Without API Calls
Change fair price weights? Recalculate instantly.
Change EV threshold to 2%? Run calculate_ev.py in seconds.
No API costs, no time delay.

### 3. Multi-Source Ready
Can merge odds from:
- Odds API (current)
- Betfair Exchange API (future)
- Custom player data (future)
- Historical snapshots (future)

### 4. Debugging Friendly
Every stage produces pure data files.
Can inspect intermediate CSVs.
Know exactly which bookmakers have which odds.
Easy to spot data quality issues.

### 5. Scalability
- Add sports easily (configure in raw_odds_pure.py)
- Add bookmakers automatically (dynamic column creation)
- Handle 100+ bookmakers efficiently
- Batch process without hitting API limits

---

## Quick Start

### Run Full Pipeline
```bash
# 1. Extract raw odds (24 API credits)
python raw_odds_pure.py

# 2. Calculate EV (instant, no API calls)
python calculate_ev.py

# 3. Review results
cat data/ev_opportunities.csv
```

### Configuration

**raw_odds_pure.py**
```python
SPORTS = ["basketball_nba", "americanfootball_nfl"]
REGIONS = "au,us,us2,eu"
ODDS_FORMAT = "decimal"
```

**calculate_ev.py**
```python
EV_MIN_EDGE = 0.03  # 3% minimum EV
BANKROLL = 1000
KELLY_FRACTION = 0.25
```

---

## API Usage Tracking

**Current Session**
- Initial extraction: 24 credits
- Re-runs with adjustments: 24 credits each
- **Remaining**: ~81,000 credits
- **Cost per run**: 24 credits
- **Runs possible**: 3,375+ remaining

---

## Next Steps

1. ✓ Raw extraction system complete
2. → Build calculate_ev.py properly (with actual data grouping)
3. → Test EV calculations end-to-end
4. → Add historical tracking (keep all runs for analysis)
5. → Integrate with Telegram alerts
6. → Add more sports/markets
7. → Connect to actual betting workflow

---

## Files Legacy vs New

### Legacy (Keep for Reference)
- `ev_arb_bot.py` - Old monolithic bot
- `core/raw_odds_logger.py` - Complex calculation pipeline
- `data/raw_odds.csv` - Old format (mixed calculations)

### New (Use Going Forward)
- `raw_odds_pure.py` - New extraction
- `calculate_ev.py` - New calculation
- `data/raw_odds_pure.csv` - Pure raw data
- `data/ev_opportunities.csv` - Calculated EVs
