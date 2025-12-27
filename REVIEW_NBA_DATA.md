# NBA Data Review Guide (V3)

**Latest CSV:** `data/v3/extracts/basketball_nba_raw_20251228_002702.csv` (196 rows × 61 columns)

## Quick Stats
- **Rows**: 196 (each row = one market + bookmaker pairing)
- **Columns**: 61 (8 core + 53 bookmakers)
- **Markets**: h2h, spreads, totals, h2h_lay
- **Bookmakers**: All 53 mapped and verified

## Data Review Checklist

### 1. Core Columns (8)
- [ ] `event_id` - Unique game identifier
- [ ] `extracted_at` - When data was pulled (UTC)
- [ ] `commence_time` - Game start time (readable format)
- [ ] `league` - Always "NBA"
- [ ] `event_name` - "Team A at Team B" format
- [ ] `market_type` - h2h, spreads, totals, or h2h_lay
- [ ] `point` - Line value (8.5, -110, etc) or empty for h2h
- [ ] `selection` - Team/Over/Under

### 2. Bookmaker Columns (53)
Each bookmaker column should contain:
- Decimal odds (e.g., 1.95, 2.10)
- Empty if bookmaker doesn't carry this market
- No missing values (only empty strings)

**Bookmaker Groups:**
- **EU Sharp (6)**: pinnacle, betfair_ex_eu, betfair_ex_au, etc.
- **US Mainstream (15+)**: draftkings, fanduel, betmgm, etc.
- **AU-Specific (12+)**: sportsbet, pointsbet, etc.
- **Specialized (15+)**: asian, dafabet, etc.

### 3. Data Quality Checks

**Coverage Questions:**
- Are all 53 bookmakers present?
- Any missing odds where they should exist?
- Do spreads always have matched pairs (+9.5/-9.5)?
- Are h2h markets present for all games?

**Value Validation:**
- Are all odds between 1.01 and 10.00?
- Are point values reasonable for spreads (typically ±2.5 to ±15)?
- Are totals reasonable (typically 180–240 for NBA)?
- Any corrupted or non-numeric values?

**Market Logic:**
- For spreads: Are both +/- sides present?
- For totals: Are Over/Under pairs matched?
- For h2h: Both teams present per game?

### 4. Specific Things to Check
1. **Half Points**: Spreads/totals should have .5 values (normal for sports betting)
2. **Missing Bookmakers**: Note any bookmakers present in code but absent from CSV
3. **Market Coverage**: Which bookmakers carry which markets?
4. **Game Count**: How many unique games in the CSV?
5. **Duplicates**: Any duplicate rows that shouldn't exist?

## How to Review

**Option A: Excel/CSV Viewer**
1. Open the latest CSV in Excel or VS Code
2. Check columns A–H (core data)
3. Spot-check bookmaker columns
4. Sort/filter by market_type to see patterns

**Option B: Python Script** (recommended)
```python
import pandas as pd

df = pd.read_csv('data/v3/extracts/basketball_nba_raw_20251228_002702.csv')

# Basic stats
print(f"Shape: {df.shape}")
print(f"\nCore columns:\n{df[['event_id', 'event_name', 'market_type', 'selection']].head()}")

# Check for missing bookmakers
bookmakers = [col for col in df.columns if col not in [
    'event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
    'market_type', 'point', 'selection'
]]
print(f"\nBookmakers found: {len(bookmakers)}")
print(f"Bookmakers: {bookmakers}")

# Check for null values
print(f"\nNull values:\n{df.isnull().sum()[df.isnull().sum() > 0]}")

# Market breakdown
print(f"\nMarkets by type:")
print(df['market_type'].value_counts())

# Sample odds
print(f"\nSample odds (pinnacle column):")
print(df['pinnacle'].head(10))
```

## Next Steps

1. **Run extraction**: `python extract_nba_v3.py`
2. **Review the output** using checklist above
3. **Document findings**: Note any issues, missing bookmakers, or data quirks
4. **Report back** with data quality assessment
5. **Then move to next sport** (NFL, NHL, etc)

## Common Issues & What They Mean

| Issue | Cause | Fix |
|-------|-------|-----|
| Empty bookmaker column | Book doesn't carry all markets | Expected; keep as-is |
| Odd value 1.01 | Very low payout (rare) | Check if book-specific odds, not an error |
| Point = 0 | Pickem market or data error | Review event-by-event |
| Missing h2h | Book only shows spreads | Normal variation |
| Duplicate rows | Same market/book listed twice | Investigate and fix |

## File Locations
- Latest CSV: `data/v3/extracts/basketball_nba_raw_20251228_002702.csv`
- Extractor code: `extract_nba_v3.py`
- Previous runs: `data/v3/extracts/` (all timestamped)

---
**Next Phase**: Once NBA data is validated, we expand to NFL, NHL, MLB following the same single-sport review process.
