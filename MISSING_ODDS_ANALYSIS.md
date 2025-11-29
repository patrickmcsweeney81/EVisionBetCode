# Missing Bookmaker Odds Analysis

## Summary
Analyzed 284 rows in `all_odds_analysis.csv` to identify why bookmaker columns have missing values.

## Root Cause: Point Value Fragmentation

### The Issue
Bookmakers offer **different spread and total point values** for the same event. The logging code correctly only populates bookmaker columns when they offer the **exact same point value** as the row being logged.

### Example
For "New York Knicks @ Orlando Magic":
- **pointsbetau** offers: spreads_2.5 (1.870/1.950)
- **sportsbet** offers: spreads_1.5 (1.900/1.900)  
- **pinnacle** offers: spreads_3.0 (unknown odds)

When logging pointsbetau's spreads_2.5 row, the code **correctly** leaves pinnacle and sportsbet columns empty because they don't offer the 2.5 spread.

## Coverage Analysis

### h2h Markets (100% coverage)
✅ **All bookmakers have odds** for h2h markets because there are no point variations.
- 144 rows, all bookmakers consistently present
- Pinnacle: 144/144 (100%)
- Betfair: 144/144 (100%)
- All AU books: 144/144 (100%)

### Spreads Markets (Fragmented)
⚠️ **Multiple spread lines per event** causes sparse bookmaker columns.
- 82 rows across 13 unique spread lines (spreads_1.5, spreads_2.5, spreads_8.5, spreads_9.5, etc.)
- Bookmakers rarely offer the same spread line
- Examples:
  - spreads_2.5: Only pointsbetau offers this line
  - spreads_1.5: Only sportsbet, tab, playup, dabble_au
  - spreads_9.5: Pinnacle + sportsbet + tab (100% coverage within that line)

### Totals Markets (Fragmented)
⚠️ **Multiple total lines per event** causes sparse bookmaker columns.
- 58 rows across 11 unique total lines (totals_223.5, totals_230.5, totals_244.5, etc.)
- Similar issue to spreads
- Examples:
  - totals_230.5: Pinnacle (75%), sportsbet (75%), tabtouch (100%)
  - totals_244.5: Only sportsbet offers this line (100% within that line)

## Impact on Fair Price Calculation

### Problem
When a bookmaker offers a unique spread/total line that **no sharp bookmakers** offer, the fair price calculation **fails** (returns empty string).

### Evidence from CSV
Row 5-6 (spreads_2.5):
```
bookmaker: pointsbetau
Book: 1.870 / 1.950
Fair: (empty)
EV%: (empty)
Prob: (empty)
```

This happens because:
1. pointsbetau offers spreads_2.5
2. Pinnacle offers spreads_3.0 (different line)
3. No other sharp books offer spreads_2.5
4. Fair calculation requires sharp bookmaker odds → **fails**

### Working Example
Row 7-8 (totals_230.5):
```
bookmaker: pointsbetau  
Book: 1.900 / 1.900
Fair: 1.930 / 1.960
EV%: -1.55% / -3.06%
```

This works because:
1. pointsbetau offers totals_230.5
2. Pinnacle also offers totals_230.5 (same line!)
3. Fair calculation succeeds with Pinnacle's 1.930/1.960 odds

## Is This a Bug?

**No - this is correct behavior.** You cannot compare:
- spreads_2.5 odds (one team favored by 2.5 points)
- spreads_3.0 odds (one team favored by 3.0 points)

These are **fundamentally different betting propositions** with different probabilities and risk profiles.

## Implications

### Data Completeness
- **h2h markets**: ✅ 100% complete, all bookmakers comparable
- **spreads/totals**: ⚠️ Fragmented by point value, many rows incomparable across bookmakers

### Fair Price Calculation
- **Works**: When sharp bookmakers offer the same point value
- **Fails**: When only non-sharp bookmakers offer a unique point value
- **Impact**: ~27% of spreads/totals rows lack fair prices (see rows with empty Fair column)

### EV Detection
- **Works**: h2h markets (100% coverage)
- **Partial**: spreads/totals (only when sharp books offer matching lines)
- **Limitation**: Cannot detect EV on unique spread/total lines without sharp reference

## Bookmaker Coverage by Type

### Sharp Books (for Fair Calculation)
- **Pinnacle**: 208/284 (73.2%) - primary sharp reference
- **Betfair**: 144/284 (50.7%) - secondary sharp reference

### AU Bookmakers (for EV Detection)  
- **sportsbet**: 244/284 (85.9%)
- **pointsbetau**: 244/284 (85.9%)
- **tabtouch**: 228/284 (80.3%)
- **tab**: 214/284 (75.4%)
- **playup**: 214/284 (75.4%)
- **dabble_au**: 204/284 (71.8%)
- **unibet**: 184/284 (64.8%)
- **neds**: 144/284 (50.7%)
- **ladbrokes_au**: 144/284 (50.7%)
- **boombet**: 144/284 (50.7%)
- **betright**: 144/284 (50.7%)
- **betr_au**: 144/284 (50.7%)
- **bet365_au**: 0/284 (0.0%) - not in API

## Recommendations

### Option 1: Accept Current Behavior (Recommended)
✅ **Pros**:
- Mathematically correct - only compares like-for-like
- No false EV signals from mismatched lines
- h2h markets work perfectly (100% coverage)

⚠️ **Cons**:
- Cannot detect EV on unique spread/total lines
- Sparse CSV for spreads/totals (looks incomplete)

### Option 2: Line Normalization (Complex)
Convert all spreads/totals to a common baseline using mathematical adjustments. For example:
- Convert spreads_2.5 → spreads_3.0 using probability models
- Convert totals_230.5 → totals_231.5 using mathematical relationships

⚠️ **Risks**:
- Requires sophisticated sports betting mathematics
- Introduces estimation error
- May create false EV signals
- Computationally expensive

### Option 3: Separate CSVs by Market Type
Create three separate CSVs:
- `all_odds_h2h.csv` (dense, 100% coverage)
- `all_odds_spreads.csv` (sparse, by line)
- `all_odds_totals.csv` (sparse, by line)

✅ **Pros**:
- Clear separation of market types
- h2h CSV would be dense and complete
- Easier to filter and analyze

⚠️ **Cons**:
- More files to manage
- Filtering script would need updates

## Conclusion

The "missing" bookmaker odds are **not a bug** - they represent bookmakers offering different spread/total lines. The current behavior is mathematically correct and prevents false EV signals from comparing incompatible betting propositions.

**Recommendation**: Keep current behavior, focus EV detection on **h2h markets** (100% coverage) where all bookmakers are comparable. Spreads/totals EV detection will only work when sharp bookmakers offer matching lines.
