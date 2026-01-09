## Fair Odds Calculation Issues - Debug Report

### Summary of Issues Found

1. **Missing Pair IDs for Spreads** ✗
   - Spreads are showing `pair_id = NaN`
   - Should have pair_id assigned during filtering
   - Result: Spreads NOT using de-vigging (False) when they should

2. **Extremely High Fair Odds** ✗
   - player_assists: max 36.00 (reasonable)
   - player_triple_double: max 101.00 (INVALID - should be ~20-30 max)
   - Root cause: Single-outcome props using simple weighted average of unreliable data
   - Problem: Alternate lines (11.5, 9.5, etc.) have very few books, inflating odds

3. **DeVig Coverage Issues** ✗
   - Spreads: Only 416 of 606 rows use de-vigging (68.5%)
   - Reason: pair_id is NaN for spreads, preventing opposite row lookup

### Technical Breakdown

#### Issue 1: Missing Pair IDs for Spreads
```
Current State:
  Row 12810: Boston @ -10.5 | pair_id = NaN | uses_devig = False
  Row 12811: Toronto @ +10.5 | pair_id = NaN | uses_devig = False

Expected State:
  Row 12810: Boston @ -10.5 | pair_id = 1234 | uses_devig = True
  Row 12811: Toronto @ +10.5 | pair_id = 1234 | uses_devig = True
```

**Why this matters:**
- Without pair_id, code falls back to legacy logic in `get_opposite_selection()`
- Legacy logic can't find opposite because spreads use negative point (-10.5 vs +10.5)
- De-vigging is skipped, uses simple weighted average instead

**Where the bug is:**
- File: `filter_nba_v3.py` - pair_id assignment section
- Spreads should get pair_id in the same way as player_props
- Check if spreads are excluded from pair_id assignment

#### Issue 2: Very High Fair Odds (Calculation Problem)
```
Example Problem:
  Row 6675: player_triple_double (Yes)
  Market: Atlanta Hawks @ Denver Nuggets
  Fair Odds: 101.00 (INVALID!)
  Uses DeVig: False (single-outcome, no opposite)
  
  Problem: Only FanDuel has this odds = 26.00
  Calculation: 1.0 / (implied_prob from 26.00) ≈ weighted average
  With only 1 book: Fair = 26.00
  But CSV shows 101.00 - suggests extreme outlier or rounding error
```

**Why this happens:**
- Single-outcome props (player_triple_double, player_first_basket) have no opposite selection
- Weighted average of 1-2 books gives unreliable fair odds
- Extreme lines (11.5, 9.5 assists) have only 2-4 books with odds
- Missing books inflates implied probabilities

**Example from data:**
```
player_assists @ 9.5 (Over):
  - draftkings: 11.20 (prob: 8.93%)
  - fanduel:    10.00 (prob: 10.00%)
  - dabble_au:  7.50  (prob: 13.33%)
  - pointsbetau: 11.00 (prob: 9.09%)
  
  Weighted average prob = ~10.3% → Fair odds = 9.71 ✓ REASONABLE
  
player_triple_double (Yes):
  - fanduel: 26.00 (prob: 3.85%)
  Only 1 book! → Fair odds = 26.00, but CSV shows 101.00 ✗ ERROR
```

### Root Causes

#### Why spreads aren't paired:
1. Filter stage assigns pair_id using composite key: (event_id, market_type, point, player_name)
2. Spreads have different point values: -10.5 vs +10.5
3. Composite key groups them as SAME group (same event, same market_type, same point)
4. But filter pairing logic may have special case that skips spreads

**Need to check:** Lines in `filter_nba_v3.py` where pair_id is assigned for different market types

#### Why single-outcome props have inflated odds:
1. Code path for single-outcome markets: Falls through to simple weighted average
2. Not enough books for reliable fair odds (2-4 books for extreme lines)
3. Formula: `fair_decimal = 1.0 / weighted_prob` is correct, but weighted_prob is unreliable
4. MAD outlier detection is disabled for single-outcome markets (only active in 2-way path)

### Fixes Needed

#### Fix 1: Verify Spreads Get Pair IDs
- Check `filter_nba_v3.py` lines ~280-320
- Ensure spreads composite key groups opposite signs correctly
- Test: Run filter and check for NaN pair_id in spreads

#### Fix 2: Limit Fair Odds for Single-Outcome Markets
- Don't use markets with <5 books for fair odds calculation
- Set fair_odds = NaN if insufficient data
- Or: Use stricter MAD threshold for single-outcome props

#### Fix 3: Cap Fair Odds Maximum
- Single-outcome props should rarely exceed 50.0
- Add validation: if fair_odds > 50 and less than 5 books → cap to NaN
- Better: Require minimum 8 books for extreme lines (>10.0 fair odds)

#### Fix 4: Disable De-Vigging for Unreliable Markets
- player_triple_double (20 total rows) → too few samples
- player_first_basket (100 total rows) → too few samples
- player_first_team_basket (96 total rows) → too few samples
- Mark these as non-2way markets in TWO_WAY_MARKETS dict

### Validation Tests

Run these after fixes:

```python
# Test 1: Spreads have pair_ids
spreads = df[df['market_type'] == 'spreads']
assert spreads['pair_id'].notna().sum() == len(spreads), "Spreads missing pair_ids!"

# Test 2: Spreads using de-vigging
assert (spreads['uses_devig'] == True).sum() > len(spreads) * 0.9, "Spreads not using de-vigging!"

# Test 3: No Fair Odds > 50 for high-volume markets
high_volume = df[df['market_type'].isin(['player_points', 'player_rebounds', 'player_assists'])]
assert (high_volume['Fair odds'] <= 50).sum() > len(high_volume) * 0.95, "Found unreliable Fair Odds!"

# Test 4: Player triple double fair odds reasonable
triple = df[df['market_type'] == 'player_triple_double']
assert triple['Fair odds'].max() <= 50, f"Triple double max: {triple['Fair odds'].max()}"
```

### Next Steps

1. **Immediate (High Priority):**
   - Fix spreads pair_id assignment in filter_nba_v3.py
   - Run filter + EV calculation
   - Verify spreads now have pair_ids and use de-vigging

2. **Follow-up (Medium Priority):**
   - Add minimum book count requirement for fair odds
   - Cap fair odds for single-outcome markets
   - Re-run EV calculation

3. **Validation (Before Use):**
   - Run test suite to verify fixes
   - Compare new vs old Fair odds
   - Spot-check 10-15 rows manually

