# Point Normalization Implementation

**Date:** December 27, 2025  
**Version:** v3.0.0  
**Status:** ✅ Complete

---

## Overview

Implemented half-point normalization for all betting lines (spreads, totals, player props) to ensure consistent market grouping regardless of how different bookmakers present their lines.

## Problem Statement

Different bookmakers may present the same market with slightly different point values:
- Bookmaker A: Over 225.3 points
- Bookmaker B: Over 225.5 points  
- Bookmaker C: Over 225.7 points

Without normalization, these would be treated as three separate markets, preventing proper odds comparison and fair odds calculation.

## Solution

All point values are now normalized to the nearest 0.5 increment using the `_normalize_point()` method:

```python
225.0 -> "225.0"
225.3 -> "225.5"  # Rounds to nearest 0.5
225.5 -> "225.5"
225.7 -> "225.5"  # Rounds to nearest 0.5
225.75 -> "226.0" # Midpoint rounds up
226.0 -> "226.0"
```

### Rounding Logic

- Uses `floor(value * 2 + 0.5) / 2` to avoid Python's banker's rounding
- Midpoint values (e.g., 225.75) round up
- Works correctly with negative values (for spreads)
- Handles None and empty string inputs gracefully

## Implementation

### 1. Base Extractor (`src/v3/base_extractor.py`)

Added `_normalize_point(point)` method that:
- Accepts float, int, string, or None
- Returns normalized value as string with one decimal place
- Returns empty string for invalid inputs

### 2. NBA Extractor (`src/v3/extractors/nba_extractor.py`)

Updated to normalize points before market grouping:
```python
point_raw = outcome.get("point")
point = self._normalize_point(point_raw)
market_key = (event_id, market_type, point, selection)
```

### 3. NFL Extractor (`src/v3/extractors/nfl_extractor.py`)

Applied normalization to spreads and totals:
```python
point_normalized = self._normalize_point(outcome.get("point", ""))
market_dict = {
    ...
    "point": point_normalized,
    ...
}
```

## Benefits

1. **Consistent Grouping**: Markets with nearly identical lines are grouped together
2. **Better Fair Odds**: More bookmakers contribute to fair odds calculation
3. **Cleaner CSV Output**: All points display as X.0 or X.5
4. **Market Standardization**: Industry-standard half-point increments

## Testing

Comprehensive test suite with 18 test cases covering:
- ✅ Standard rounding (225.3 → 225.5)
- ✅ Midpoint rounding (225.75 → 226.0)
- ✅ Integer inputs (226 → 226.0)
- ✅ Negative values for spreads (-3.3 → -3.5)
- ✅ Edge cases (None, empty string, zero)
- ✅ String inputs ("225.5" → "225.5")

All tests pass.

## Impact on Market Grouping

**Before normalization:**
```
Market 1: Over 225.3 (Pinnacle: 1.90)
Market 2: Over 225.5 (DraftKings: 1.87, FanDuel: 1.88)
Market 3: Over 225.7 (Sportsbet: 2.10)
```

**After normalization:**
```
Market 1: Over 225.5 (Pinnacle: 1.90, DraftKings: 1.87, FanDuel: 1.88, Sportsbet: 2.10)
```

Now all four bookmakers are grouped together for fair odds calculation and EV detection.

## CSV Output Format

The `point` column in CSV outputs now consistently shows:
- Spreads: `-7.5`, `-7.0`, `-6.5`, etc.
- Totals: `225.0`, `225.5`, `226.0`, etc.
- Player props: `25.0`, `25.5`, `26.0`, etc.

## Future Considerations

- Consider sport-specific normalization rules if needed (e.g., soccer totals might use 0.25 increments)
- Monitor API data to ensure bookmakers don't introduce fractional points beyond 0.5
- Could extend to normalize odds values if needed in future

---

## Files Modified

1. `src/v3/base_extractor.py` - Added `_normalize_point()` method
2. `src/v3/extractors/nba_extractor.py` - Applied normalization to all markets
3. `src/v3/extractors/nfl_extractor.py` - Applied normalization to spreads and totals

## Related Documentation

- [EVisionBet v3 Architecture](src/v3/README.md)
- [Base Extractor Class](src/v3/base_extractor.py)
- [NBA Extractor](src/v3/extractors/nba_extractor.py)
- [NFL Extractor](src/v3/extractors/nfl_extractor.py)
