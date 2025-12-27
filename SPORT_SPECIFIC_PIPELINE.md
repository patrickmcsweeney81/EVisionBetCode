# Sport-Specific Odds Extraction Pipeline

This is a modular, sport-specific odds extraction system with half-point normalization and EV calculation.

## 🎯 Architecture Overview

The new pipeline uses **separate Python files for each sport** to provide maximum customization and control:

```
┌─────────────────┐
│  Individual     │
│  Sport Files    │
│  (raw_*.py)     │
└────────┬────────┘
         │
         ├── raw_NFL.py  → data/raw_NFL.csv
         ├── raw_NBA.py  → data/raw_NBA.csv
         ├── raw_MLB.py  → data/raw_MLB.csv
         ├── raw_NHL.py  → data/raw_NHL.csv
         └── raw_NCAAF.py → data/raw_NCAAF.csv
         
         ↓ (merge_raw_odds.py)
         
┌─────────────────┐
│  all_raw_odds   │  ← Admin view (all data)
│  .csv           │
└────────┬────────┘
         
         ↓ (calculate_ev.py)
         
┌─────────────────┐
│  all_ev_hits    │  ← User view (EV opportunities)
│  .csv           │
└─────────────────┘
```

## ✨ Key Features

### 1. **Sport-Specific Extraction**
- One Python file per sport (e.g., `raw_NFL.py`, `raw_NBA.py`)
- Each file handles sport-specific markets and player props
- Easy to customize per sport without affecting others
- Can run individually or all together

### 2. **Half-Point Normalization**
- Spreads and totals normalized to nearest 0.5 increment
- Ensures alignment across bookmakers for fair odds calculation
- Examples: 5.25 → 5.5, 6.75 → 7.0, 8.0 → 8.0

### 3. **Two-Stage CSV Output**
- **`all_raw_odds.csv`**: Complete dataset for admin analysis (all bookmakers, all markets)
- **`all_ev_hits.csv`**: Filtered EV opportunities for users (only positive EV bets)

### 4. **Modular Configuration**
- `config.py`: Central config for bookmakers, weights, regions, settings
- Easy to add new bookmakers or adjust ratings
- Sharp books (3⭐/4⭐) for fair odds, target books (1⭐) for EV

## 🚀 Quick Start

### Option 1: Run All Sports (Recommended)

```bash
# Extract all sports and merge
python run_all_sports.py

# Calculate EV opportunities
python calculate_ev.py
```

### Option 2: Run Individual Sports

```bash
# Extract specific sport
python raw_NFL.py
python raw_NBA.py

# Merge into all_raw_odds.csv
python merge_raw_odds.py

# Calculate EV
python calculate_ev.py
```

### Option 3: Extract Specific Sports Only

```bash
# Run only NFL and NBA
python run_all_sports.py --sports NFL NBA

# Merge and calculate EV
python merge_raw_odds.py
python calculate_ev.py
```

## 📁 File Structure

```
EVisionBetCode/
├── raw_NFL.py              # NFL extractor
├── raw_NBA.py              # NBA extractor
├── raw_MLB.py              # MLB extractor
├── raw_NHL.py              # NHL extractor
├── raw_NCAAF.py            # College Football extractor
├── run_all_sports.py       # Run all extractors + merge
├── merge_raw_odds.py       # Merge sport CSVs → all_raw_odds.csv
├── calculate_ev.py         # Calculate EV → all_ev_hits.csv
├── config.py               # Central configuration
├── data/
│   ├── raw_NFL.csv         # NFL raw odds
│   ├── raw_NBA.csv         # NBA raw odds
│   ├── raw_MLB.csv         # MLB raw odds
│   ├── raw_NHL.csv         # NHL raw odds
│   ├── raw_NCAAF.csv       # NCAAF raw odds
│   ├── all_raw_odds.csv    # Merged raw odds (admin)
│   └── all_ev_hits.csv     # EV opportunities (user)
└── .env                    # ODDS_API_KEY
```

## 🔧 Configuration

Edit `config.py` to customize:

### Sport Settings
```python
SPORT_CONFIGS = {
    "NFL": {
        "sport_key": "americanfootball_nfl",
        "base_markets": ["h2h", "spreads", "totals"],
        "player_props": [...],
        "enable_props": True,
    },
}
```

### Bookmaker Ratings
```python
BOOKMAKER_RATINGS = {
    # 4⭐ = Sharp (for fair odds)
    "pinnacle": 4,
    "betfair": 4,
    "draftkings": 4,
    "fanduel": 4,
    
    # 3⭐ = Sharp (for fair odds)
    "betmgm": 3,
    "betrivers": 3,
    
    # 1⭐ = Target (for EV opportunities)
    "sport316": 1,  # Sportsbet
    "pointsbetau": 1,
    "tab": 1,
}
```

### EV Settings
```python
EV_MIN_EDGE = 0.01           # 1% minimum edge
DEFAULT_BANKROLL = 1000
DEFAULT_KELLY_FRACTION = 0.25
MIN_SHARP_BOOKS = 2          # Minimum sharps for fair odds
```

## 📊 CSV Formats

### Individual Sport CSVs (e.g., `raw_NFL.csv`)

```csv
timestamp,sport,event_id,commence_time,teams,market,line,selection,player,pinnacle,draftkings,fanduel,...
2025-12-27T...,americanfootball_nfl,abc123,2025-12-28T...,Team A V Team B,spreads,-3.5,Team A Over,,1.91,1.87,1.90,...
2025-12-27T...,americanfootball_nfl,abc123,2025-12-28T...,Team A V Team B,spreads,3.5,Team B Under,,1.91,1.95,1.92,...
```

### Merged Raw Odds (`all_raw_odds.csv`)

Same format as individual sports, but includes all sports combined.

### EV Hits (`all_ev_hits.csv`)

```csv
timestamp,sport,event_id,commence_time,teams,market,line,selection,player,bookmaker,odds,fair_odds,ev_percent,implied_prob,stake
2025-12-27T...,americanfootball_nfl,abc123,2025-12-28T...,Team A V Team B,spreads,-3.5,Team A Over,,tab,2.05,1.91,7.33,52.36,18.33
```

## 🎓 How It Works

### 1. Sport Extraction (`raw_*.py`)

Each sport extractor:
1. Fetches odds from The Odds API
2. Normalizes spreads/totals to half-point increments
3. Outputs to `data/raw_SPORT.csv`
4. One row per market/bookmaker combination

### 2. Merge (`merge_raw_odds.py`)

1. Reads all `raw_*.csv` files from `data/`
2. Collects all unique bookmaker columns
3. Merges into single `all_raw_odds.csv`
4. Fills missing bookmaker columns with empty strings

### 3. EV Calculation (`calculate_ev.py`)

1. Reads `all_raw_odds.csv`
2. Groups by (sport, event_id, market, line, player)
3. Calculates fair odds from sharp books (3⭐/4⭐) using median
4. Finds EV opportunities in target books (1⭐)
5. Outputs to `all_ev_hits.csv`

## ⚙️ Normalization Logic

```python
def normalize_to_half_point(value: float) -> float:
    """Round to nearest 0.5 increment."""
    return round(value * 2) / 2

# Examples:
5.25 → 5.5
5.75 → 5.5
6.0  → 6.0
6.3  → 6.5
7.8  → 8.0
```

This ensures that spreads like 6.0, 6.2, 6.3, and 6.4 all align to 6.0 or 6.5, allowing proper fair odds calculation across bookmakers.

## 📈 Adding New Sports

1. **Create new extractor** (e.g., `raw_EPL.py`)
   ```python
   SPORT_KEY = "soccer_epl"
   OUTPUT_FILE = DATA_DIR / "raw_EPL.csv"
   # ... rest follows same structure as raw_NFL.py
   ```

2. **Add to config.py**
   ```python
   SPORT_CONFIGS = {
       "EPL": {
           "sport_key": "soccer_epl",
           "base_markets": ["h2h", "spreads", "totals"],
           "player_props": [],
           "enable_props": False,
       },
   }
   ```

3. **Add to runner**
   ```python
   # In run_all_sports.py
   SPORT_EXTRACTORS = {
       "EPL": "raw_EPL.py",
   }
   ```

4. **Add to merge**
   ```python
   # In merge_raw_odds.py
   SPORT_FILES = [
       "raw_EPL.csv",
   ]
   ```

## 🔍 Testing Individual Components

```bash
# Test single sport extraction
python raw_NFL.py

# Verify output
ls -lh data/raw_NFL.csv

# Test merge
python merge_raw_odds.py

# Test EV calculation
python calculate_ev.py
```

## 🆚 Comparison: Old vs New

| Feature | Old (pipeline_v2) | New (Sport-Specific) |
|---------|-------------------|----------------------|
| Structure | Single `extract_odds.py` | One file per sport |
| Customization | Limited | Full per-sport control |
| Normalization | None | Half-point alignment |
| Output | `raw_odds_pure.csv` | Individual + merged CSVs |
| Config | Hardcoded | Modular `config.py` |
| Player Props | All or nothing | Per-sport configuration |
| Debugging | Difficult | Easy (isolate by sport) |

## 💡 Best Practices

1. **Run sports individually first** to test API credits and data quality
2. **Check normalization** by inspecting `line` column in CSVs
3. **Verify sharp book coverage** in `all_ev_hits.csv` (should have 2+ sharp books)
4. **Adjust `EV_MIN_EDGE`** in config.py based on risk tolerance
5. **Monitor API credits** (check headers in console output)

## 🐛 Troubleshooting

### No events found
- Check time window settings (`EVENT_MIN_MINUTES`, `EVENT_MAX_HOURS`)
- Verify sport key is correct in config
- Check if games are scheduled in API

### No EV opportunities
- Lower `EV_MIN_EDGE` in config.py
- Check if sharp books have odds in `all_raw_odds.csv`
- Verify bookmaker keys match config (lowercase)

### Merge fails
- Ensure at least one `raw_*.csv` exists in `data/`
- Check CSV encoding (should be UTF-8)
- Verify headers match across sport files

## 📝 Environment Variables

Required in `.env`:
```bash
ODDS_API_KEY=your_api_key_here
```

Optional:
```bash
EVENT_MIN_MINUTES=5
EVENT_MAX_HOURS=48
REGIONS=au,us,eu
```

## 🚀 Next Steps

- [ ] Add more sports (soccer, tennis, cricket)
- [ ] Implement database storage for `all_ev_hits.csv`
- [ ] Add scheduling (cron jobs) for automated runs
- [ ] Create web dashboard for EV monitoring
- [ ] Add backtesting against historical odds

---

**Created:** December 27, 2025  
**Purpose:** Sport-specific odds extraction with half-point normalization  
**Status:** ✅ Ready for testing
