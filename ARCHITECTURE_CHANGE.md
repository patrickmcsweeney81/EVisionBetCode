# EV Bot Architecture Change - hits_ev.csv Removed

## What Changed

The bot no longer generates `hits_ev.csv` directly. Instead, it only creates `all_odds_analysis.csv` with ALL opportunities, and you use `filter_ev_hits.py` to generate hits.

## Why This Change

**Before (❌ Old Way):**
- Bot had duplicate EV calculation logic scattered everywhere
- hits_ev.csv had buggy probability calculations (based on book odds instead of fair odds)
- Had to maintain two separate code paths
- Couldn't test different thresholds without re-running bot

**After (✅ New Way):**
- Bot only logs raw data + fair prices to all_odds_analysis.csv (single source of truth)
- filter_ev_hits.py does all filtering with correct probability logic
- No duplicate code = no bugs
- Can test different EV thresholds instantly without API calls
- Cleaner separation: collect vs filter

## New Workflow

### 1. Run Bot (Collect Data)
```bash
python ev_arb_bot_NEW.py
```
**Output:** `data/all_odds_analysis.csv` with ALL opportunities

### 2. Filter for EV Hits
```bash
# Default: 3% EV, 40% prob
python filter_ev_hits.py

# Aggressive: 2% EV, 35% prob
python filter_ev_hits.py --ev-min 0.02 --prob-min 0.35

# Quality filter: require 3+ sharp books
python filter_ev_hits.py --min-sharps 3

# Custom output
python filter_ev_hits.py --ev-min 0.04 --prob-min 0.45 --output data/hits_conservative.csv
```
**Output:** `data/hits_ev_filtered.csv` with filtered hits

### 3. Analyze Data
```bash
# View CSV directly
cat data/all_odds_analysis.csv | head -20

# Or use Excel/LibreOffice to open all_odds_analysis.csv
```

## Files

| File | Purpose | When Created |
|------|---------|--------------|
| `all_odds_analysis.csv` | ALL opportunities with Fair/EV%/Prob/NumSharps | Every bot run |
| `hits_ev_filtered.csv` | Filtered EV hits meeting your thresholds | When you run filter script |
| `seen_hits.json` | Deduplication tracking | Every bot run |

## Benefits

✅ **No more duplicate logic** - Single probability calculation in raw_odds_logger.py  
✅ **Faster testing** - Filter offline without API calls  
✅ **Correct probabilities** - Based on fair odds, not book odds  
✅ **Flexible filtering** - Test different EV/prob thresholds instantly  
✅ **Easier debugging** - All data in one place  

## Console Output Still Shows EV

The bot still prints EV opportunities to console during scan:
```
[EV] sportsbet         Josh Giddey          U 1.5 1.800 (fair=1.711, edge=5.2%, stake=$15)
```

This is just for monitoring - the real analysis happens with filter_ev_hits.py.

## Migration Note

If you have scripts that read `hits_ev.csv`, update them to:
1. Use `filter_ev_hits.py` to generate filtered CSV first
2. Read from `hits_ev_filtered.csv` instead
3. Or read directly from `all_odds_analysis.csv` and apply your own filters
