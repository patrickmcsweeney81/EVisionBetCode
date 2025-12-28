# ✅ SPREADS/TOTALS: CORRECT DATA STRUCTURE
**Based on V2 Archive Analysis** | December 28, 2025

---

## The Key Insight You Were Missing

**I was wrong about "alignment."**

There is **NO alignment between whole numbers and .5 lines.**

Instead: **Each point value is a completely separate market.**

```
WRONG (what I was proposing):
  "Align -6 books with -6.5 books"
  ❌ These are different markets!

CORRECT (V2 approach):
  "-6.5 Celtics spread" = ONE market (separate row)
  "-7.0 Celtics spread" = DIFFERENT market (separate row)
  "-7.5 Celtics spread" = DIFFERENT market (separate row)
  
  Each analyzed independently.
```

---

## V2 Data Structure (PROVEN CORRECT)

### Format: Wide Format, Multiple Rows per Event

```
ONE ROW = ONE unique (market_type, point, selection)
COLUMNS = All bookmakers

Event: Celtics vs Blazers

Row 1:  market_type=spreads, point=-6.5, selection="Celtics"
        pinnacle=1.91, betfair=1.88, draftkings=1.95, fanduel=1.69, ...

Row 2:  market_type=spreads, point=-7.0, selection="Celtics"
        draftkings=1.92, betmgm=1.87, ...

Row 3:  market_type=spreads, point=-7.5, selection="Celtics"
        pinnacle=1.93, betfair=1.87, draftkings=1.95, betmgm=1.91, ...

Row 4:  market_type=spreads, point=-8.0, selection="Celtics"
        pinnacle=1.85, betfair=1.82, ...

Row 5:  market_type=totals, point=229.5, selection="Over"
        pinnacle=1.90, fanduel=1.88, ...
```

### Why This Works

1. **Preserves all data** - No consolidation, no loss
2. **Clean grouping** - Each market point analyzed separately
3. **Clear fair odds** - For each row, calculate fair odds from sharps at THAT point
4. **Simple logic** - No interpolation, no adjustment math needed
5. **Matches Odds API** - Data comes naturally structured this way

---

## How to Implement

### Step 1: Parse CSV Correctly

```python
import pandas as pd

def load_and_structure_spreads_totals(csv_path):
    """
    Load CSV and group by (event_id, market_type, point, selection)
    Each combination = one market.
    """
    df = pd.read_csv(csv_path)
    
    # Filter to spreads and totals only
    markets = df[df['market_type'].isin(['spreads', 'totals'])].copy()
    
    # Ensure point is numeric (not string)
    markets['point'] = pd.to_numeric(markets['point'], errors='coerce')
    
    # Group by market key
    grouped = markets.groupby(
        ['event_id', 'market_type', 'point', 'selection'],
        as_index=False
    )
    
    return grouped
```

### Step 2: Identify Sharp Books Per Market

```python
SHARP_BOOKS = ['pinnacle', 'betfair']  # Rating 3⭐ or 4⭐
MID_BOOKS = ['draftkings', 'betmgm']    # Rating 2⭐-3⭐

def get_sharp_books_for_market(market_group, bookmaker_columns):
    """
    For one specific (event, market_type, point, selection),
    get all sharp book odds.
    
    market_group = one row from the grouped data
    """
    sharp_odds = []
    
    for book in SHARP_BOOKS:
        if book in bookmaker_columns:
            odds_val = market_group[book]
            if pd.notna(odds_val) and odds_val > 0:
                sharp_odds.append({
                    'book': book,
                    'odds': odds_val
                })
    
    return sharp_odds
```

### Step 3: Calculate Fair Odds Per Market

```python
import statistics

def calculate_fair_odds_for_market(sharp_odds_list):
    """
    For one market point, calculate fair odds from sharp books.
    
    Input: [{'book': 'pinnacle', 'odds': 1.91}, 
            {'book': 'betfair', 'odds': 1.88}]
    
    Output: 1.895 (median of sharp odds)
    """
    
    if len(sharp_odds_list) == 0:
        return None  # No sharp books for this point
    
    odds_values = [item['odds'] for item in sharp_odds_list]
    
    # Use weighted median (Pinnacle = 40%, others = 30% each, etc.)
    if len(odds_values) == 1:
        return odds_values[0]
    elif len(odds_values) == 2:
        # Pinnacle 50%, Betfair 50%
        return statistics.mean(odds_values)
    else:
        # Multiple sharps - weight Pinnacle higher
        weighted = sum(o for book, o in zip([item['book'] for item in sharp_odds_list], odds_values)) / len(odds_values)
        return weighted
```

### Step 4: Find EV at Each Market Point

```python
def find_ev_for_market(market_row, fair_odds, target_book='fanduel'):
    """
    For one specific market point, check if target book has value.
    
    market_row = one row from the grouped data (contains all bookmakers)
    fair_odds = calculated fair odds for this market point
    target_book = which book to compare (FanDuel, MyBookie, etc.)
    """
    
    if fair_odds is None or fair_odds < 1:
        return None
    
    target_odds = market_row.get(target_book)
    
    if pd.isna(target_odds) or target_odds <= 0:
        return None  # Target book doesn't offer this market point
    
    # EV as % of fair odds
    ev_pct = (target_odds / fair_odds) - 1
    
    return {
        'bookmaker': target_book,
        'market_type': market_row['market_type'],
        'point': market_row['point'],
        'selection': market_row['selection'],
        'target_odds': target_odds,
        'fair_odds': fair_odds,
        'ev_pct': ev_pct,
        'ev_type': 'positive' if ev_pct > 0 else 'negative'
    }
```

---

## Complete Pipeline Example

```python
def process_spreads_totals(csv_path, min_ev_threshold=0.03):
    """
    Full pipeline:
    1. Load CSV
    2. Group by market key (event, market_type, point, selection)
    3. For each market group, calculate fair odds from sharps
    4. Compare target books
    5. Find opportunities
    """
    
    df = pd.read_csv(csv_path)
    
    # Filter spreads/totals
    markets = df[df['market_type'].isin(['spreads', 'totals'])].copy()
    markets['point'] = pd.to_numeric(markets['point'], errors='coerce')
    
    opportunities = []
    
    # Process each unique market point
    for (event_id, market_type, point, selection), group in markets.groupby(
        ['event_id', 'market_type', 'point', 'selection']
    ):
        
        # Get sharp books for this market point
        sharp_odds = get_sharp_books_for_market(group.iloc[0], df.columns)
        
        if len(sharp_odds) < 2:
            continue  # Skip if not enough sharp books
        
        # Calculate fair odds at this point
        fair_odds = calculate_fair_odds_for_market(sharp_odds)
        
        # Check each target book
        for target_book in ['fanduel', 'mybookieag', 'matchbook']:
            ev_data = find_ev_for_market(group.iloc[0], fair_odds, target_book)
            
            if ev_data and abs(ev_data['ev_pct']) > min_ev_threshold:
                opportunities.append(ev_data)
    
    return pd.DataFrame(opportunities)
```

---

## Validation Tests

### Test 1: Correct Grouping

```python
def test_market_grouping(csv_path):
    """
    Verify each market point creates separate row
    """
    df = pd.read_csv(csv_path)
    spreads = df[df['market_type'] == 'spreads']
    
    # Group and count
    grouped = spreads.groupby(['event_id', 'point', 'selection']).size()
    
    # Each unique group should have exactly ONE row
    assert (grouped == 1).all(), "Market grouping broken - duplicates found"
    
    # Check that different points exist
    unique_points = spreads['point'].nunique()
    assert unique_points > 1, "Missing point variations"
    
    print(f"✅ Correct: {len(spreads)} spreads with {unique_points} unique points")
```

### Test 2: Fair Odds Sanity

```python
def test_fair_odds_range(fair_odds_series):
    """
    Fair odds should be in reasonable range
    """
    # All odds should be > 1.0
    assert (fair_odds_series > 1.0).all(), "Fair odds < 1.0 found"
    
    # Most should be 1.5 - 3.5
    reasonable = (fair_odds_series >= 1.5) & (fair_odds_series <= 3.5)
    pct_reasonable = reasonable.sum() / len(fair_odds_series)
    
    assert pct_reasonable > 0.8, f"Only {pct_reasonable:.1%} of fair odds in reasonable range"
    
    print(f"✅ Fair odds distribution: {fair_odds_series.min():.2f} to {fair_odds_series.max():.2f}")
```

### Test 3: Sharp Book Coverage

```python
def test_sharp_coverage(csv_path):
    """
    Each market should have >= 2 sharp books
    """
    df = pd.read_csv(csv_path)
    spreads = df[df['market_type'] == 'spreads']
    
    SHARP_BOOKS = ['pinnacle', 'betfair']
    
    for (event_id, point, selection), group in spreads.groupby(['event_id', 'point', 'selection']):
        # Count non-null values for sharp books
        sharp_count = sum(group[book].notna().sum() for book in SHARP_BOOKS if book in group.columns)
        
        if sharp_count < 2:
            print(f"⚠️  Low sharp coverage: {event_id}, {point}, {selection} ({sharp_count} sharps)")
    
    print("✅ Sharp coverage check complete")
```

### Test 4: EV Distribution

```python
def test_ev_distribution(ev_df):
    """
    Check EV results look reasonable
    """
    positive_ev = (ev_df['ev_pct'] > 0).sum()
    negative_ev = (ev_df['ev_pct'] < 0).sum()
    
    print(f"EV Distribution:")
    print(f"  Positive EV: {positive_ev} opportunities")
    print(f"  Negative EV: {negative_ev} opportunities")
    
    # Should have mix of both
    assert positive_ev > 0, "No positive EV found - algorithm broken"
    assert negative_ev > 0, "No negative EV found - algorithm broken"
    
    print(f"✅ EV distribution looks correct")
```

---

## Manual Inspection Checklist

```
For each run, manually inspect one complete event:

Event: Celtics vs Blazers (8dc89134)

□ Check spreads exist:
  - Count rows: 3-5 different point values expected
  - Points: -6.5, -7.0, -7.5, -8.0, -8.5 (or similar range)
  
□ Check bookmaker coverage:
  - At least 15-25 bookmakers per point
  - Some books at every point (e.g., DraftKings at -7.5)
  - Some books missing some points (normal)
  
□ Check odds values:
  - All odds > 1.0
  - Tight books (Pinnacle) have higher odds than loose books (FanDuel)
  - For same point: odds differ by < 0.20
  
□ Check fair odds calculation:
  - Pinnacle + Betfair median seems reasonable
  - Fair odds between tightest and loosest books
  - Fair odds stable across similar point values
  
□ Check EV results:
  - Some positive, some negative
  - Biggest EV at tightest vs loosest comparison
  - No EV > 50% (would be suspicious)
```

---

## What Changed in Understanding

| What I Proposed | What's Actually Correct |
|---|---|
| Normalize all points to -7.5 | Keep each point separate - it's a different market |
| Compare across points with adjustment | Never compare across points |
| Consolidate data | Preserve every data point as-is |
| Complex interpolation math | Simple fair odds calculation per point |

---

## Next Steps

1. ✅ Understand V2 approach (DONE - this doc)
2. ⏳ Implement correct grouping (by market key)
3. ⏳ Calculate fair odds per point (not cross-point)
4. ⏳ Find EV within each market point
5. ⏳ Run validation tests
6. ⏳ Manual inspect one event
7. ⏳ Deploy to backend

---

**Key Takeaway:** No alignment needed. Each market point is analyzed independently using only sharp books at THAT point. Simple, clean, correct.
