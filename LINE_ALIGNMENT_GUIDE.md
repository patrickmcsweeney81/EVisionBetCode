# Line & Spread Alignment Strategy

**Problem:** Different bookmakers offer different lines for the same market
- Book A: Total Over 48.5 
- Book B: Total Over 48.0
- Book C: Total Over 49.0

**Question:** How do we align these for fair odds calculation & EV detection?

---

## 🎯 Three Alignment Strategies

### Strategy 1: **Exact Line Match (Strictest)**

**What:** Only group markets with IDENTICAL lines  
**Pros:**
- ✅ Most accurate (comparing apples to apples)
- ✅ No rounding errors
- ✅ Easy to implement

**Cons:**
- ❌ Fewer bookmakers per market (lose coverage)
- ❌ Higher API costs (need more granular queries)

**Example:**
```
Total Over 48.5:  [Pinnacle, DraftKings, FanDuel]
Total Over 48.0:  [BetMGM, Betrivers]
Total Over 49.0:  [Sportsbet]
```

**Best For:** High-precision analysis, professional arbitrage

---

### Strategy 2: **Rounding to Half-Point (Balanced) ⭐ RECOMMENDED**

**What:** Round all lines to nearest 0.5, then group  
**Rounding Rules:**
- 48.25 → 48.5 (round up)
- 48.0 → 48.0 (stays)
- 48.75 → 49.0 (round up)

**Pros:**
- ✅ Good balance (slight tolerance for minor variations)
- ✅ Maintains coverage (more books per group)
- ✅ Industry standard in sports betting
- ✅ Reasonable for EV calculation

**Cons:**
- ⚠️ Slight line inconsistency (±0.25 difference)

**Example:**
```
48.0 - 48.49:  [Book A: 48.25, Book B: 48.0]  → 48.0 group
48.5 - 48.99:  [Book C: 48.5, Book D: 48.75] → 48.5 group
49.0 - 49.49:  [Book E: 49.0]                 → 49.0 group
```

**Best For:** Balanced EV detection (YOUR CASE)

---

### Strategy 3: **Tolerance Band (Looser)**

**What:** Accept lines within ±0.5 of the sharpest line  
**Pros:**
- ✅ Maximum bookmaker coverage
- ✅ Useful for less liquid markets

**Cons:**
- ❌ Can skew fair odds (mixing 48.0 with 49.0 is bad)

**Example:**
```
Sharpest line: 48.5
Accept range: 48.0 - 49.0  ← Groups everything together
```

**Best For:** Soft markets where coverage matters more than precision

---

## 📊 Implementation: Half-Point Rounding (RECOMMENDED)

### 1. **Add to base_extractor.py:**

```python
def normalize_line(line: str | float) -> str:
    """
    Normalize spread/total lines to nearest half-point.
    
    Handles:
    - String inputs ("48.25") → float → normalize
    - Float inputs (48.25) → normalize
    - Empty/missing lines → return as-is
    
    Rules:
    - 48.0 → 48.0
    - 48.25 → 48.5 (round up)
    - 48.5 → 48.5
    - 48.75 → 49.0 (round up)
    """
    if not line or line == "":
        return ""
    
    try:
        line_float = float(line)
        
        # Multiply by 2, round, divide by 2
        # 48.25 * 2 = 96.5 → round(96.5) = 96 or 97
        # Better: use Decimal for precision
        from decimal import Decimal, ROUND_HALF_UP
        
        d = Decimal(str(line_float))
        normalized = (d * 2).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 2
        
        return str(normalized)
    except (ValueError, TypeError):
        return str(line)
```

### 2. **Modify grouping key in calculate_opportunities.py:**

```python
def group_rows_wide(rows: List[Dict]) -> Dict[Tuple, List[Dict]]:
    """
    Group by: (sport, event_id, market, NORMALIZED_POINT, player_name)
    
    Lines are normalized to nearest 0.5 before grouping.
    """
    from src.v3.base_extractor import normalize_line
    
    grouped = {}
    for row in rows:
        market = row.get("market", "")
        selection = row.get("selection", "")
        point = row.get("point", "")
        
        # NORMALIZE THE LINE
        point_normalized = normalize_line(point)
        
        player_name = _player_key(selection) if market.startswith("player_") else ""

        key = (
            row.get("sport", ""),
            row.get("event_id", ""),
            market,
            point_normalized,  # ← Use normalized
            player_name,
        )
        grouped.setdefault(key, []).append(row)
    
    return grouped
```

### 3. **Track Original vs Normalized (for debugging):**

```python
def add_line_variance_metric(opportunity: Dict):
    """
    Track how much lines varied in this market.
    
    Useful for understanding data quality & alignment effectiveness.
    """
    bookmaker_lines = [
        float(bm.get("point", 0)) 
        for bm in opportunity.get("bookmakers", [])
        if bm.get("point")
    ]
    
    if bookmaker_lines:
        variance = max(bookmaker_lines) - min(bookmaker_lines)
        opportunity["line_variance"] = variance
        opportunity["alignment_quality"] = (
            "tight" if variance <= 0.5 else
            "moderate" if variance <= 1.0 else
            "loose"
        )
```

---

## 🧪 Testing Your Alignment

### Create test case:

```python
def test_line_alignment():
    """Verify lines group correctly"""
    test_rows = [
        {"event_id": "e1", "market": "totals", "point": "48.0", "bookmaker": "A"},
        {"event_id": "e1", "market": "totals", "point": "48.25", "bookmaker": "B"},
        {"event_id": "e1", "market": "totals", "point": "48.5", "bookmaker": "C"},
        {"event_id": "e1", "market": "totals", "point": "49.0", "bookmaker": "D"},
    ]
    
    grouped = group_rows_wide(test_rows)
    
    # Should have 2 groups: 48.5 and 49.0
    assert len(grouped) == 2
    
    # Check 48.5 group has A, B, C
    group_48_5 = [g for g in grouped if "48.5" in str(g)][0]
    assert len(grouped[group_48_5]) == 3
    
    # Check 49.0 group has D
    group_49_0 = [g for g in grouped if "49.0" in str(g)][0]
    assert len(grouped[group_49_0]) == 1
```

---

## 📊 Impact on Your NBA Data

### Before Alignment:
```
Total Over 216.5:  [Pinnacle]
Total Over 217.0:  [DraftKings, FanDuel]
Total Over 217.5:  [BetMGM, Betrivers, Sportsbet]

Problem: These are separate markets!
Fair odds can't use Pinnacle's 216.5 with others' 217.5
```

### After Half-Point Alignment:
```
Total Over 217.0:  [Pinnacle: 216.5 → normalized]
                   [DraftKings: 217.0]
                   [FanDuel: 217.0]
Total Over 217.5:  [BetMGM: 217.5]
                   [Betrivers: 217.5]
                   [Sportsbet: 217.5]

Now we can calculate fair odds per normalized line!
```

---

## 🎯 Recommended for Your Pipeline

### Phase 1: Implement Half-Point Normalization (NOW)
```python
# In base_extractor.py
def normalize_line(line: str | float) -> str:
    # Code from above
    
# In calculate_opportunities.py  
point_normalized = normalize_line(point)
```

### Phase 2: Add Line Variance Tracking (LATER)
- Track how much lines vary
- Monitor data quality
- Flag suspicious groupings

### Phase 3: Optional - Add Tolerance Config (FUTURE)
```python
ALIGNMENT_STRATEGY = "half_point"  # or "exact" or "tolerance_band"
TOLERANCE_BAND = 0.5  # ±0.5 from sharpest

# Switch strategies per sport if needed
```

---

## 📝 Current Your NBA CSV

When you ran NBA extraction:
- **Did you notice line variations?**
- Check the CSV and look for same market with different `point` values

Example to check:
```python
import pandas as pd

df = pd.read_csv("basketball_nba_raw_20251226_100233.csv")

# Group by market, check point variation
for market in df['market'].unique():
    market_df = df[df['market'] == market]
    points = market_df['point'].unique()
    if len(points) > 1:
        print(f"{market}: {points}")  # Shows variation
```

---

## ✅ My Recommendation for You

**Use Strategy 2: Half-Point Rounding**

**Why:**
1. **Balances precision + coverage** - You get enough books per market
2. **Industry standard** - Sports bettors expect this
3. **Simple to implement** - Few lines of code
4. **Fair odds work well** - ±0.25 tolerance is acceptable
5. **Your data will benefit** - More books per group = better EV detection

**Implementation:**
1. Add `normalize_line()` to `base_extractor.py`
2. Use normalized point in grouping key
3. Test with your NBA data
4. Track line variance for quality metrics

---

## 🚀 Next Steps

**Want me to:**
1. Implement half-point rounding in your code?
2. Add test cases to verify alignment?
3. Analyze your NBA CSV to show actual line variations?
4. Add line variance metrics to output?

Which would help most? Let me know! 🎯

