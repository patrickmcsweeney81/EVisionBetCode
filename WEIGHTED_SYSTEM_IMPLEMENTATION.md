# Fair Odds Calculation: Weighted System Implementation
## Summary of Changes (January 6, 2026)

---

## What Changed

**Previous Method:**
- Sharp books only (4⭐ + 3⭐) = 10 books
- Median with 20% trim
- Soft books excluded entirely

**New Method:**
- ALL books (4⭐ + 3⭐ + 2⭐ + 1⭐) = 20 books
- Weighted average by sharpness
- 20% trim ONLY on soft books (2⭐ + 1⭐)
- Sharp books never trimmed

---

## Weights

```
4⭐ Sharp (Pinnacle, Betfair EU, Matchbook, DraftKings, FanDuel, LowVig):
    Weight = 1.5
    6 books

3⭐ Sharp (BetOnlineAG, BetMGM, BetRivers, Fanatics):
    Weight = 1.0
    4 books

2⭐ Soft (HardRockBet, WilliamHill US, Bovada, ESPNBet):
    Weight = 0.75
    4 books (with 20% trim)

1⭐ Soft (Coolbet, Fliff):
    Weight = 0.5
    2 books (with 20% trim)

Total: 20 books
```

---

## Example: Bam Adebayo Rebounds Under 9.5

### All Books De-vigged

```
DraftKings (4⭐):      54.38%  weight 1.5
FanDuel (4⭐):         53.72%  weight 1.5
BetOnlineAG (3⭐):     53.97%  weight 1.0
WilliamHill (2⭐):     52.94%  weight 0.75  (survives trim)
Fliff (1⭐):           52.85%  weight 0.5   (survives trim)
HardRockBet (2⭐):     49.05%  weight 0.75  (trimmed - outlier)
ESPNBet (2⭐):         53.05%  weight 0.75  (trimmed - outlier)
```

### Calculation

```
Soft books trim: Remove HardRockBet (49.05%) and ESPNBet (53.05%)
                 Keep: WilliamHill (52.94%), Fliff (52.85%)

Weighted sum:
  DraftKings:    54.38% × 1.5  = 81.57
  FanDuel:       53.72% × 1.5  = 80.59
  BetOnlineAG:   53.97% × 1.0  = 53.97
  WilliamHill:   52.94% × 0.75 = 39.71
  Fliff:         52.85% × 0.5  = 26.42
  ──────────────────────────────────────
  Total:                        = 282.25 / 5.25 = 53.76% probability

Fair Odds: 1 / 0.5376 = 1.86 (rounded)
```

### EV Impact

```
AU Odds: 1.92 (DabbleAU)

OLD SYSTEM (1.85 fair):  EV = (1.92 × 0.5405) - 1 = 3.78%
NEW SYSTEM (1.86 fair):  EV = (1.92 × 0.5376) - 1 = 3.22%  ✓ CSV Match
```

The new system gives **3.22% EV** (slightly lower than old 3.78%, but more robust consensus).

---

## Key Differences

| Aspect | Old System | New System |
|--------|-----------|-----------|
| **Books Used** | 10 (sharp only) | 20 (all) |
| **Weighting** | Equal (all 1.0) | By rating (1.5, 1.0, 0.75, 0.5) |
| **Trimming** | 20% of ALL books | 20% of SOFT books only |
| **Sharp Book Trim** | Yes, loses data | No, always included |
| **Soft Book Impact** | Excluded | Reduced via weight + trim |
| **Consensus** | Minimal (median only) | More robust (weighted) |
| **Data Utilization** | Limited | Comprehensive |

---

## Results Summary

### Overall Statistics
```
Total Lines: 1,102
Mean EV: -5.30%
Median EV: -4.43%
Positive EV Lines: 28 (2.5%)
```

### Top 3 Opportunities
```
1. DAL @ SAC Totals Over 225.5:     Fair 3.25 → AU 3.50 → EV +7.56%
2. DAL @ SAC Totals Over 211.5:     Fair 3.12 → AU 3.30 → EV +5.67%
3. DAL @ SAC Totals Over 223.5:     Fair 3.42 → AU 3.60 → EV +5.41%
```

---

## Why This Is Better

1. **More Data = Better Consensus**
   - 20 books instead of 10
   - Multiple perspectives weighted by quality

2. **Smart Trimming**
   - Soft books trimmed (reduce outliers like HardRockBet's 49%)
   - Sharp books never trimmed (they're reliable)
   - Prevents data loss

3. **Transparent Weighting**
   - 4⭐ books trust 50% more than 3⭐
   - 2⭐ books reduced to 1/3 weight of sharps
   - Clear, defensible methodology

4. **Balanced Risk**
   - Still favors sharp book consensus
   - But incorporates broader market view
   - More resilient to edge cases

---

## Technical Implementation

```python
# De-vig all books
devig_probs = {book: devig(odds) for book in ALL_BOOKS}

# Separate by rating
sharp_probs = extract(devig_probs, SHARP_BOOKS)     # Never trim
soft_probs = extract(devig_probs, SOFT_BOOKS)       # Trim 20%

# Trim soft books
trimmed_soft = apply_20pct_trim(soft_probs)

# Combine
all_probs = {**sharp_probs, **trimmed_soft}

# Weighted average
weights = [BOOK_WEIGHTS[book] for book in all_probs]
fair_prob = np.average(probs, weights=weights)
fair_odds = 1 / fair_prob
```

---

## Validation

✅ **Code Updated**: `calculate_nba_ev_full.py`
✅ **Data Generated**: `basketball_nba_ev_full.csv`
✅ **Test Examples**:
   - Bam Adebayo: 3.22% EV ✓
   - Cooper Flagg: 0.47% EV (minimal but positive)
   - Top opportunities: 5-7% range

---

## Files Changed

- `calculate_nba_ev_full.py` - Updated function with weighted logic
- `data/v3/extracts/basketball_nba_ev_full.csv` - New output
- Analysis scripts created:
  - `bam_weighted_comparison.py` - Detailed walkthrough
  - `compare_weighted_results.py` - Top opportunities summary

---

**Status**: ✅ Implemented and validated  
**Date**: January 6, 2026  
**System**: Weighted consensus with smart trimming on soft books only

