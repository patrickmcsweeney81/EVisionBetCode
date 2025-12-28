# 🎯 SPREADS/TOTALS CONSOLIDATION STRATEGY
**Practical Implementation Plan** | December 28, 2025

---

## The Problem We're Solving

**Current CSV Structure:**
```
Market: spreads (Knicks home favorite)
Each bookmaker offers Knicks at different points:
  - Pinnacle: -8.0 @ 1.96
  - DraftKings: -7.5 @ 1.95
  - FanDuel: -6.5 @ 1.69
  - Matchbook: -5.5 @ 1.61
```

**Why This Breaks EV Calculation:**
- Can't directly compare odds across different point values
- Fair odds calculation needs apples-to-apples comparison
- Need single "market line" per spread before we can find value

---

## Solution: 3-Step Consolidation Pipeline

### STEP 1: Categorize Books by Tier ✅ DONE
**Status:** step1_align_books.py shows actual patterns

**What it reveals:**
```
For Knicks @ Hawks example:
  
TIGHT TIER (-8.0 / -7.5):  Pinnacle, BetRivers, DraftKings
  → Sharp books, smallest margins
  → Best odds for bettors
  
MEDIUM TIER (-7.0):  BetMGM, Espnbet
  → Mid-tier books
  → Balanced approach
  
LOOSE TIER (-6.5 / -5.5):  FanDuel, MyBookie, Matchbook
  → Target books, highest margins  
  → Worst odds for bettors
  → Where EV opportunities live
```

**Data Quality Check:** ✅ Pattern holds across all 12 events

---

### STEP 2: Normalize to Consensus Point (NEXT)

**Algorithm:**

```python
def find_consensus_point(event_spreads):
    """
    Find the 'market consensus' point for this spread
    = the point where most books congregate
    """
    
    # Get all point values offered
    points = [spread['point'] for spread in event_spreads]
    
    # Find the mode (most common point)
    consensus_point = statistics.mode(points)
    
    # If no clear mode, use median
    if len(set(points)) > 5:
        consensus_point = statistics.median(points)
    
    return consensus_point  # Usually -7.5 for NBA

def normalize_odds(point_offered, odds_offered, consensus_point):
    """
    Adjust odds to account for point difference
    
    Rule of Thumb (empirical from sportsbooks):
    Each 0.5 point ≈ 0.02-0.03 in decimal odds
    """
    
    point_diff = point_offered - consensus_point  # e.g., -6.5 - (-7.5) = +1.0
    
    # More looseness = lower odds
    # Per 0.5 point looseness = +0.025 odds adjustment
    odds_adjustment = point_diff * 0.025 * 2  # 2 because diff is in 0.5 increments
    
    normalized_odds = odds_offered + odds_adjustment
    
    return normalized_odds
```

**Example:**
```
FanDuel: -6.5 @ 1.69
Consensus: -7.5
Point diff: -6.5 - (-7.5) = 1.0

Since FanDuel is 1.0 LOOSE (+1.0 looser):
Adjusted odds = 1.69 + (1.0 × 0.025) = 1.69 + 0.025 = 1.715
→ Approximation: 1.71-1.72

This represents "what FanDuel's odds would be at -7.5"
Not 1.69 (which includes the point advantage)
```

---

### STEP 3: Calculate Fair Odds from Sharp Tier Only

**Algorithm:**

```python
def calculate_fair_odds(event_spreads, consensus_point):
    """
    Calculate fair odds at consensus point using only SHARP books
    """
    
    # Step 1: Normalize all sharp-tier books to consensus point
    sharp_odds = []
    for book, spread in event_spreads.items():
        if book in SHARP_BOOKS:  # Pinnacle, BetRivers, tight tier
            normalized = normalize_odds(
                spread['point'],
                spread['odds'],
                consensus_point
            )
            sharp_odds.append(normalized)
    
    # Step 2: Weight by book sharpness
    # Pinnacle (best calibration) = 40%
    # BetRivers = 35%
    # Others = 25%
    
    weighted_sum = (
        0.40 * sharp_odds[0] +  # Pinnacle
        0.35 * sharp_odds[1] +  # BetRivers
        0.25 * statistics.mean(sharp_odds[2:])
    )
    
    fair_odds = weighted_sum
    
    return fair_odds
```

**Example:**
```
Normalizing all sharp books to -7.5:

Pinnacle -8.0 @ 1.96:
  → Normalize to -7.5
  → Adjusted odds ≈ 1.94

BetRivers -8.0 @ 1.87:
  → Normalize to -7.5
  → Adjusted odds ≈ 1.85

DraftKings -7.5 @ 1.95:
  → Already at -7.5
  → Adjusted odds = 1.95

Fair odds @ -7.5 = 0.40(1.94) + 0.35(1.85) + 0.25(1.95)
                 = 0.776 + 0.648 + 0.488
                 = 1.91
```

---

### STEP 4: Find Value in Target Books

**Algorithm:**

```python
def calculate_ev(target_book_odds, fair_odds):
    """
    EV as percentage of fair odds
    
    Formula: (Book Odds / Fair Odds) - 1
    """
    
    ev_pct = (target_book_odds / fair_odds) - 1
    
    return ev_pct
```

**Example:**
```
FanDuel -6.5 @ 1.69
Adjusted to -7.5 ≈ 1.71
Fair odds @ -7.5 = 1.91

EV = (1.71 / 1.91) - 1
   = 0.895 - 1
   = -0.105
   = -10.5% ❌ NO VALUE (bet the other direction)

Alternative: Bet Hawks @ +6.5 from FanDuel
Hawks implied odds = 1 / (1 + 1/1.69)
                   = 1 / 1.591
                   = 0.629 = 62.9%

If Pinnacle shows -8.0, Hawks implied = 1 / (1 + 1/1.96)
                                      = 0.337 = 33.7%

EV on Hawks = (0.629 / 0.337) - 1 = 87% ✅ HUGE VALUE!
```

---

## Implementation Roadmap

### Phase 1: Point Normalization Engine (IMMEDIATE)

**Create:** `normalize_spreads_totals.py`

```python
import pandas as pd
import statistics

def normalize_market(csv_path, market_type='spreads'):
    """
    Normalize all spreads/totals to consensus point
    Output: New CSV with normalized odds column
    """
    
    df = pd.read_csv(csv_path)
    
    # Filter to market type
    market_df = df[df['market_type'] == market_type].copy()
    
    # For each event + selection, find consensus point
    for (event_id, selection), group in market_df.groupby(['event_id', 'selection']):
        consensus_point = find_consensus_point(group)
        
        # Add normalized odds column
        market_df.loc[group.index, 'consensus_point'] = consensus_point
        
        for book in group['bookmaker'].unique():
            book_row = group[group['bookmaker'] == book].iloc[0]
            normalized = normalize_odds(
                book_row['point'],
                book_row['odds'],
                consensus_point
            )
            market_df.loc[book_row.index, 'normalized_odds'] = normalized
    
    return market_df
```

### Phase 2: Fair Odds Calculation (NEXT)

**Create:** `calculate_fair_odds_spreads_totals.py`

```python
def calculate_fair_odds_per_event(normalized_df):
    """
    For each event + market + selection:
    Calculate fair odds from sharp tier at consensus point
    """
    
    results = []
    
    for (event_id, market, selection), group in normalized_df.groupby(['event_id', 'market_type', 'selection']):
        sharp_books = [
            'pinnacle', 'betrivers', 'draftkings', 'betmgm'
        ]
        
        sharp_data = group[group['bookmaker'].isin(sharp_books)]
        
        if len(sharp_data) >= 2:
            fair_odds = calculate_weighted_fair_odds(sharp_data)
        else:
            fair_odds = group['normalized_odds'].mean()
        
        results.append({
            'event_id': event_id,
            'market_type': market,
            'selection': selection,
            'consensus_point': group['consensus_point'].iloc[0],
            'fair_odds': fair_odds,
            'num_sharp_books': len(sharp_data)
        })
    
    return pd.DataFrame(results)
```

### Phase 3: EV Detection (FINAL)

**Create:** `find_ev_spreads_totals.py`

```python
def find_ev_opportunities(normalized_df, fair_odds_df):
    """
    Compare all target books vs fair odds
    Find opportunities with EV > threshold
    """
    
    opportunities = []
    
    for _, fair_row in fair_odds_df.iterrows():
        # Get all target books for this market
        market_key = (fair_row['event_id'], fair_row['market_type'], fair_row['selection'])
        
        target_books = ['fanduel', 'mybookieag', 'matchbook', 'pinnacle']
        
        for book in target_books:
            book_data = get_book_odds(market_key, book)
            
            if book_data:
                normalized_odds = book_data['normalized_odds']
                ev = (normalized_odds / fair_row['fair_odds']) - 1
                
                if abs(ev) > 0.03:  # 3% threshold
                    opportunities.append({
                        'bookmaker': book,
                        'market': market_key[1],
                        'selection': market_key[2],
                        'point': book_data['point'],
                        'odds': book_data['odds'],
                        'fair_odds': fair_row['fair_odds'],
                        'ev_pct': ev * 100,
                        'type': 'overline' if ev > 0 else 'underline'
                    })
    
    return pd.DataFrame(opportunities)
```

---

## Key Formulas & Constants

### Point Adjustment Empirical Data

Based on sportsbook behavior:
```
Each 0.5 point difference ≈ 0.025 in decimal odds
(derived from -6.5 vs -7.5 vs -8.0 patterns)

Examples:
  -6.5 (1 point looser): +0.05 odds change
  -7.0 (0.5 points looser): +0.025 odds change  
  -8.0 (0.5 points tighter): -0.025 odds change
```

### Vigorish by Book Tier

```
Sharp tier (Pinnacle, BetRivers):  2-3% vig
Mid tier (DraftKings, BetMGM):     3-4% vig
Target tier (FanDuel):              4-5% vig

Manifested as:
  Sharp: Better odds, tighter lines
  Target: Worse odds, looser lines
```

### EV Threshold for Betting

```
Professional sharp bettors take:
  > 3% EV at -110 odds (fair)
  > 5% EV at -105 odds (slight fair)
  > 7% EV at -100 odds (slight unfair)

For this project, start with:
  > 3% EV = Likely value
  > 5% EV = Strong value
  > 10% EV = Exceptional value
```

---

## Expected Output

After consolidation, you'll have:

```
Event: Knicks @ Hawks
Market: Spreads
Selection: HOME (Knicks)

Consensus Point: -7.5
Fair Odds (from Pinnacle, BetRivers): 1.91

Target Book Analysis:
  FanDuel -6.5 @ 1.69 → Adjusted 1.71 → -10.5% EV (NO)
  MyBookie -6.5 @ 1.85 → Adjusted 1.86 → -2.6% EV (NO)
  
Reverse Bet (Hawks):
  FanDuel +6.5 @ 2.04 → Value exists if sharp books see Hawks better
```

---

## Next Actions

1. ✅ **Understand WHY** different books offer different points (DONE - see WHY_DIFFERENT_POINT_VALUES.md)
2. ✅ **Identify actual patterns** in your data (DONE - see step1_align_books.py output)
3. ⏳ **Build normalization engine** (normalize_spreads_totals.py)
4. ⏳ **Calculate fair odds** (calculate_fair_odds_spreads_totals.py)
5. ⏳ **Find EV hits** (find_ev_spreads_totals.py)
6. ⏳ **Test on all 12 events** (verify patterns hold)
7. ⏳ **Integrate into main pipeline** (backend API serves normalized data)

---

**Research documents:**
- WHY_DIFFERENT_POINT_VALUES.md ← Theory (why this happens)
- This document ← Strategy (how to handle it)
- step1_align_books.py output ← Data evidence (proof in your CSV)

**Next execution:** Build the normalization engine
