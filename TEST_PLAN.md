# Testing Strategy - Pipeline V2 & Core Handlers

**Objective:** Validate both `pipeline_v2/` (extraction + calculation) and `core/` handlers work correctly with the cleaned-up codebase.

---

## Phase 1: Pipeline V2 Validation ⚙️

### Stage 1: Extract Raw Odds
**File:** `pipeline_v2/extract_odds.py`  
**Purpose:** Fetch odds from The Odds API and write to CSV (wide format)

```bash
cd C:\EVisionBetCode
python pipeline_v2/extract_odds.py
```

**Expected Output:**
- `data/raw_odds_pure.csv` created
- ~3-5 minutes runtime (depends on API)
- **Check these metrics:**
  - Rows created (should be 100+ for NBA + NBL)
  - Column count (should be 25+: event details + bookmaker odds)
  - Bookmaker coverage (Pinnacle, DraftKings, FanDuel should be present)

**CSV Structure Check:**
```
sport, event_id, commence_time, market, point, selection, 
Pinnacle, Draftkings, Fanduel, Betmgm, ..., Sportsbet, Tab, Pointsbet, ...
```

**Quick Inspection:**
```powershell
# Check row count
(Import-Csv data/raw_odds_pure.csv | Measure-Object).Count

# Check columns
(Import-Csv data/raw_odds_pure.csv | Select-Object -First 1).PSObject.Properties.Name

# Sample data
Import-Csv data/raw_odds_pure.csv | Select-Object -First 3
```

---

### Stage 2: Calculate EV Opportunities
**File:** `pipeline_v2/calculate_opportunities.py`  
**Purpose:** Read raw CSV, calculate fair odds, output EV opportunities

```bash
python pipeline_v2/calculate_opportunities.py
```

**Expected Output:**
- `data/ev_opportunities.csv` created
- Much faster than Stage 1 (uses local CSV, no API calls)
- **Check these metrics:**
  - Rows created (should be 5-50 opportunities depending on market)
  - Fair odds calculations (should be between min and max bookmaker odds)
  - EV% calculations (should all be >= 1% per config)

**CSV Structure Check:**
```
sport, event_id, market, player, selection, 
sharp_book_count, best_book, odds_decimal, fair_odds, ev_percent, stake,
Pinnacle, Draftkings, Fanduel, ...
```

**Quick Analysis:**
```powershell
# Check results
$ev = Import-Csv data/ev_opportunities.csv
$ev | Measure-Object  # Count
$ev | Select-Object sport, ev_percent, stake | Head -10  # Sample
$ev | Group-Object sport | Select-Object Name, Count  # By sport
```

---

## Phase 2: Data Validation ✅

### CSV Quality Checks

**1. No Empty Fair Odds:**
```powershell
$csv = Import-Csv data/ev_opportunities.csv
$csv | Where-Object { [string]::IsNullOrWhiteSpace($_.fair_odds) } | Measure-Object
# Should return 0 (no empty fair odds)
```

**2. Fair Odds Within Bookmaker Range:**
```powershell
$csv = Import-Csv data/ev_opportunities.csv | Select-Object -First 5
# Visually inspect: fair_odds should be between min/max of bookmaker columns
```

**3. EV% is Positive:**
```powershell
$csv = Import-Csv data/ev_opportunities.csv
$csv | Where-Object { [double]$_.ev_percent -lt 0.01 } | Measure-Object
# Should return 0 (all EV >= 1%)
```

**4. Sharp Book Count >= 2:**
```powershell
$csv = Import-Csv data/ev_opportunities.csv
$csv | Where-Object { [int]$_.sharp_book_count -lt 2 } | Measure-Object
# Should return 0 (all have 2+ sharp sources)
```

---

## Phase 3: Core Handlers Testing 🎯

**Only needed IF you plan to use legacy ev_arb_bot.py or custom handlers**

### Import Validation

```bash
# Test all imports work
python -c "from core.h2h import extract_h2h_odds_for_book; print('h2h: OK')"
python -c "from core.spreads import extract_spread_odds; print('spreads: OK')"
python -c "from core.totals import extract_totals_odds; print('totals: OK')"
python -c "from core.player_props import extract_player_prop_odds; print('player_props: OK')"
python -c "from core.nfl_props import extract_nfl_prop_odds; print('nfl_props: OK')"
python -c "from core.fair_prices import build_fair_prices_two_way; print('fair_prices: OK')"
```

### Function Tests

```bash
# Run unit tests (if using pytest)
pytest tests/ -v
```

Expected output:
```
test_book_weights.py::test_get_weight ... PASSED
test_master_fair.py::test_master_fair_odds_pinnacle_and_sharps ... PASSED
```

---

## Phase 4: Comparison & Analysis 📊

### Key Metrics to Compare

| Metric | Expected Range | What It Means |
|--------|---|---|
| **Total Rows (raw)** | 100-500 | API coverage - more is better |
| **Total Opportunities** | 5-100 | Market efficiency - fewer means sharper markets |
| **Avg EV%** | 2-5% | Edge quality - higher is rarer but better |
| **Highest EV%** | 5-20% | Best opportunities |
| **Avg Sharp Books/Opp** | 3-6 | Data reliability |
| **Best Bookmakers** | Tab, Sportsbet, Pointsbet | AU books showing edges |

### Sample Analysis Script

```python
import pandas as pd

# Load results
raw = pd.read_csv('data/raw_odds_pure.csv')
ev = pd.read_csv('data/ev_opportunities.csv')

print(f"Raw odds extracted: {len(raw)} rows")
print(f"Opportunities found: {len(ev)} rows")
print(f"\nOpportunities by sport:")
print(ev['sport'].value_counts())
print(f"\nEV statistics:")
print(ev['ev_percent'].describe())
print(f"\nTop 10 opportunities:")
print(ev.nlargest(10, 'ev_percent')[['sport', 'market', 'selection', 'ev_percent', 'best_book']])
```

---

## Phase 5: Troubleshooting 🔧

### If Stage 1 (extract_odds.py) fails:

```
Error: API_KEY missing
→ Check .env has valid ODDS_API_KEY

Error: 422 Unsupported Market
→ Some bookmakers don't support props for certain sports - normal

Error: No data returned
→ Check SPORTS/REGIONS in .env
→ Try running at different time (games might not be available)
```

### If Stage 2 (calculate_opportunities.py) fails:

```
Error: No such file 'raw_odds_pure.csv'
→ Run Stage 1 first: python pipeline_v2/extract_odds.py

Error: Fair odds calculation fails
→ Check raw CSV has Pinnacle/DraftKings data
→ Review book_weights.py for weight configuration

Error: ImportError from fair_prices
→ Should be fixed - verify core/fair_prices.py exists
```

### If imports fail:

```
Error: Cannot import from fair_prices
→ Verify core/fair_prices.py exists and has correct content

Error: Cannot import from book_weights
→ Check book_weights.py is in core/ folder
```

---

## Recommendation: Full Test Run ✅

**Suggested sequence:**

1. **Run Stage 1** (5-10 min)
   ```bash
   python pipeline_v2/extract_odds.py
   ```

2. **Inspect raw_odds_pure.csv**
   ```powershell
   (Import-Csv data/raw_odds_pure.csv | Measure-Object).Count
   ```

3. **Run Stage 2** (1 min)
   ```bash
   python pipeline_v2/calculate_opportunities.py
   ```

4. **Analyze results**
   ```powershell
   $ev = Import-Csv data/ev_opportunities.csv
   $ev | Measure-Object
   $ev | Group-Object sport
   ```

5. **Validate quality** (run checks above)

6. **Report findings** (share counts, top opportunities, any errors)

---

## Expected Success Criteria ✨

✅ Stage 1 completes without errors  
✅ raw_odds_pure.csv created with 100+ rows  
✅ Stage 2 completes without errors  
✅ ev_opportunities.csv created  
✅ All EV% values >= 1%  
✅ All fair_odds between bookmaker min/max  
✅ All sharp_book_count >= 2  
✅ No import errors when testing handlers  

**If all checks pass:** System is ready for production use!
