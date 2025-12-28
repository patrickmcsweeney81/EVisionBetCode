# 🎯 SPREADS/TOTALS ALIGNMENT & EV IMPROVEMENTS BRAINSTORM
**Analysis Date:** December 28, 2025

---

## Current Data Structure Issue

**The Event:** New York Knicks @ Atlanta Hawks

**Current Spread Data (12 rows for one event):**
```
ATL Hawks    6.5    | FanDuel: 2.08
NYK Knicks  -6.5    | FanDuel: 1.69

ATL Hawks    7.5    | DraftKings: 1.80
NYK Knicks  -7.5    | DraftKings: 1.95

ATL Hawks    5.5    | [empty - no book offers]
NYK Knicks  -5.5    | [empty - no book offers]

ATL Hawks    8.0    | Pinnacle: 1.89
NYK Knicks  -8.0    | Pinnacle: 1.96

ATL Hawks    7.0    | [empty]
NYK Knicks  -7.0    | [empty]

ATL Hawks   11.5    | [empty]
NYK Knicks -11.5    | [empty]
```

**Problem:** 
- 12 rows for one spread market (6 point values × 2 sides)
- Many books don't offer all point values (sparse data)
- Need to consolidate for EV comparison

---

## Key Observations

### 1. **Point Value Distribution**
Each event has multiple point values offered by different books:
- **FanDuel:** -6.5/-6.5
- **DraftKings:** -7.5/-7.5  
- **Pinnacle:** -8.0/-8.0
- **No book offers:** -5.5, -7.0, -11.5 (outliers, probably API errors)

### 2. **Book Specialization**
```
Pinnacle    → Offers wider range (safer lines)
DraftKings  → Selective lines (favorites)
FanDuel     → Standard lines (-6.5, -7.5)
BetRivers   → [need to verify coverage]
```

### 3. **For Home Team (Knicks):**
```
Point    Pinnacle  DraftKings  FanDuel
-5.5     [empty]   [empty]     [empty]
-6.5     [empty]   [empty]     1.69
-7.0     [empty]   [empty]     [empty]
-7.5     [empty]   1.95        [empty]
-8.0     1.96      [empty]     [empty]
-11.5    [empty]   [empty]     [empty]
```

---

## 💡 Proposed Solution: "Line Clustering"

Instead of 12 separate rows, **group by point value and compare:**

### Before (Current):
```
6 rows × 2 sides = 12 rows per point spread
```

### After (Proposed):
```
Group spreads by consensus point value:
- Best market at -6.5: FanDuel (1.69 Knicks, 2.08 Hawks)
- Best market at -7.5: DraftKings (1.95 Knicks, 1.80 Hawks)
- Best market at -8.0: Pinnacle (1.96 Knicks, 1.89 Hawks)

Output 3 "main lines" instead of 12 rows
```

---

## 🚀 EV Improvement Strategy

### Phase 1: Line Consolidation
**Create function:** `consolidate_spread_lines(event_spreads)`

```python
def consolidate_spread_lines(spreads_df):
    """
    Input: All spreads for one event (12 rows with sparse data)
    
    Process:
    1. Group by point value
    2. Find "dominant" book for each point (most complete pairing)
    3. Track all books offering that point
    4. Return consolidated lines
    
    Output: ~3-4 "main" spreads instead of 12
    
    Example:
    {
        'point': -6.5,
        'dominant_book': 'FanDuel',
        'home_odds': 1.69,
        'away_odds': 2.08,
        'all_books_offering': ['FanDuel', 'BetMGM'],
    }
    """
```

### Phase 2: Fair Odds Alignment
**Problem:** Pinnacle offers -8.0, but FanDuel's sharpest line is -6.5

**Solution:** Create "synthetic fair line" at consensus point
```python
def calculate_consensus_fair_line(point_group):
    """
    For each point value:
    1. Collect all sharp book odds at that point
    2. Weight by sharpness (Pinnacle > BetRivers > others)
    3. Calculate fair odds at that specific point
    
    Example:
    Point -6.5:
      - FanDuel (1⭐): 1.69 (if at -6.5)
      - Pinnacle (4⭐): interpolate to -6.5
      - Fair odds: weighted average
    
    Point -7.5:
      - DraftKings (1⭐): 1.95
      - Pinnacle (4⭐): interpolate to -7.5
      - Fair odds: weighted average
    """
```

### Phase 3: Totals Alignment (Same Approach)
Current totals have similar issues:
- Over/Under @ 248.5 (FanDuel)
- Over/Under @ 249.5 (DraftKings)
- Over/Under @ 250.5 (sparse)
- Over/Under @ 248.0, 242.0, 245.0 (likely errors)

**Solution:** Cluster around consensus point (e.g., 248-250 range)

---

## 🎯 Implementation Roadmap

### Step 1: Data Validation
**Check all 12 events for:**
- How many spreads per event? (currently 12 rows each = all events have spreads)
- Point value range? (-5.5 to -11.5)
- Outlier points? (-11.5, -5.5 seem suspicious)
- Book coverage? (which books offer most lines)

### Step 2: Remove Outliers
**Filter out points that:**
- Only 1 book offers (likely errors)
- Outside -7.0 to -8.5 range (consensus range)
- Have zero valid odds (completely empty rows)

### Step 3: Create Consolidation Function
```python
def consolidate_market(event_data, market_type='spreads'):
    """
    Takes 12 spread rows → outputs 3-4 main lines
    
    Returns DataFrame with:
    - point (main consensus line, e.g., -6.5, -7.5, -8.0)
    - home_odds (fairest odds from dominant book)
    - away_odds
    - all_books
    - coverage_pct (% of books offering this point)
    """
```

### Step 4: Integrate with Fair Odds
- Use consolidated lines as input to fair odds calculation
- Handle point interpolation if needed
- Output clean "canonical spreads" per event

---

## 📊 Expected Improvements

**Before (Current CSV):**
```
286 rows total
- 24 h2h (clean, 2 rows per event)
- 124 spreads (sparse, 12 rows per event)
- 116 totals (sparse, 12 rows per event)
- 22 h2h_lay (outliers)
```

**After (Consolidated):**
```
~100 rows total
- 24 h2h (unchanged)
- 36 spreads (3 main lines × 12 events)
- 36 totals (3 main lines × 12 events)
- Eliminates outliers/errors
```

**EV Calculation Benefits:**
1. ✅ Cleaner data (no sparse NaNs)
2. ✅ Better fair odds calculation (all lines have 2+ sharp books)
3. ✅ Easier comparison (aligned point values)
4. ✅ Less noise (removed outlier points)

---

## 🔧 Code Architecture Proposal

**New files to create:**

```
src/
├── consolidation.py
│   ├── consolidate_spreads()
│   ├── consolidate_totals()
│   └── detect_outlier_points()
│
├── fair_odds.py
│   ├── calculate_fair_odds()
│   └── interpolate_line_odds()
│
└── ev_finder.py
    └── find_opportunities()
```

**Pipeline Flow:**
```
raw_csv
  ↓
consolidate spreads/totals
  ↓
calculate fair odds per line
  ↓
find EV opportunities
  ↓
output ev_hits.csv
```

---

## ✅ Immediate Action Items

- [ ] **Validate:** Check all 12 events for point distribution
- [ ] **Identify:** Which points are outliers (-11.5, -5.5)?
- [ ] **Benchmark:** What's the consensus point range? (-6.5 to -8.0?)
- [ ] **Code:** Write `consolidate_spreads()` function
- [ ] **Test:** Run on current CSV, verify output is cleaner
- [ ] **Integrate:** Feed consolidated lines to fair_odds.py

---

**Status:** 🚀 Ready to implement Phase 1 (consolidation)

Next Session: Build consolidation.py with outlier detection
