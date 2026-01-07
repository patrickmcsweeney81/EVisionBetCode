# Team Column Implementation - Summary

**Status:** ✅ Complete and Committed (Commit: 7fcd12e)  
**Date:** January 7, 2026

## What Was Added

A dedicated **`team`** column to capture team identifiers for team_totals markets, separate from the existing `player_name` column used for player props.

## Changes Made

### 1. **extract_nba_v3.py** (Lines 301-315)
**Before:**
- Used `player_name` column for both player props AND team_totals

**After:**
- Added dedicated `team` variable separate from `player_name`
- For market types starting with `team_`: Populates `team` field from API `description` field
- For market types starting with `player_`: Populates `player_name` field from API `description` field
- Updated column ordering: `core_cols` now includes `"team"` after `"player_name"`

### 2. **filter_nba_v3.py** (Line 128)
**Before:**
```python
df = df.drop_duplicates(subset=['event_name', 'market_type', 'selection', 'point', 'player_name'], keep='first')
```

**After:**
```python
df = df.drop_duplicates(subset=['event_name', 'market_type', 'selection', 'point', 'player_name', 'team'], keep='first')
```

**Effect:** Deduplication now preserves different teams' totals as unique bets (e.g., "Dallas Over" vs "Sacramento Over")

### 3. **calculate_nba_ev_full.py** (Line 501)
**Before:**
```python
core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
             'market_type', 'point', 'selection', 'player_name']
```

**After:**
```python
core_cols = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 
             'market_type', 'point', 'selection', 'player_name', 'team']
```

**Effect:** Final EV CSV includes the `team` column for team_totals visibility

## Data Structure

### Example: team_totals Row in CSV

**Before (Confusing):**
```
event_name: "Dallas Mavericks @ Sacramento Kings"
market_type: "team_totals"
selection: "Over"
point: "223.5"
player_name: ""  ← Empty, no team identifier
```

**After (Clear):**
```
event_name: "Dallas Mavericks @ Sacramento Kings"
market_type: "team_totals"
selection: "Over"
point: "223.5"
player_name: ""  ← Empty (reserved for player props)
team: "Dallas Mavericks"  ← ✅ Now clearly shows WHICH team's total
```

## CSV Column Order

New order (all three CSVs - raw, filtered, EV):
```
1. event_id
2. extracted_at
3. commence_time
4. league
5. event_name
6. market_type
7. point
8. selection
9. player_name      ← For player props (e.g., "Anthony Davis")
10. team            ← For team props (e.g., "Dallas Mavericks")  [NEW]
11-40. Bookmaker odds columns
```

## Pipeline Test Results

Full pipeline ran successfully with new column:
- ✅ Extract: 22,630 rows (includes team column)
- ✅ Filter: 7,547 rows (dedup preserves team distinctions)
- ✅ EV: 7,547 rows (team column in output)

**Team Totals Data:**
- team_totals market: 258 rows in filtered data
- All have `team` field populated from API `description`

## API Data Source

The Odds API provides team names in the `description` field for team_totals markets (same pattern as player props use `description` for player names).

Example API response structure for team_totals outcome:
```json
{
    "name": "Over",
    "description": "Dallas Mavericks",  ← Team name from API
    "point": 223.5,
    "price": 1.91
}
```

## Next Steps

✅ **Done:**
- Dedicated `team` column extracted from API
- Column preserved through filtering
- Column included in final EV output
- Changes committed and pushed to GitHub

📋 **Optional Future Enhancements:**
- Display team in frontend tables alongside selection
- Use team+selection+point for better market grouping
- Enhanced filtering/sorting by team

---

**Commit:** `7fcd12e`  
**Files Modified:** 3 (extract_nba_v3.py, filter_nba_v3.py, calculate_nba_ev_full.py)  
**Lines Changed:** 12 insertions, 10 deletions
