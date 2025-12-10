# Render Path Resolution Fix - December 11, 2025

## Problem
The Render cron job for `calculate_opportunities.py` was failing with:
```
[!] /opt/render/project/src/data/raw_odds_pure.csv not found
❌ Your cronjob failed because of an error: Exited with status 1
```

**Root Cause:** The scripts used relative paths that depended on the script location. When Render cron jobs run with a different working directory than expected, the path resolution failed.

---

## Solution Implemented

### 1. Added Robust Path Resolution (`extract_odds.py` and `calculate_opportunities.py`)

Created a `get_data_dir()` function that tries multiple location strategies:
- Option 1: Relative to script location (default, works locally)
- Option 2: Current working directory (works for Render cron jobs)
- Option 3: Parent of /src subdirectory (handles Render's file structure)
- Default fallback: Creates directory in script location

**Before:**
```python
RAW_CSV = Path(__file__).parent.parent / "data" / "raw_odds_pure.csv"
```

**After:**
```python
def get_data_dir():
    """Find data directory - supports local and Render deployments"""
    # Try multiple locations...
    return data_path

DATA_DIR = get_data_dir()
RAW_CSV = DATA_DIR / "raw_odds_pure.csv"
```

### 2. Automatic Directory Creation

Both scripts now:
- Create the `/data` directory if it doesn't exist
- Use `mkdir(parents=True, exist_ok=True)` for safety

```python
DATA_DIR.mkdir(parents=True, exist_ok=True)
```

### 3. Enhanced Debug Output

Added detailed logging to both scripts showing:
- Script location
- Working directory
- Data directory path
- Whether files/directories exist
- Directory contents (if missing)

Example output:
```
[DEBUG] Script location: C:\EVisionBetCode\pipeline_v2\calculate_opportunities.py
[DEBUG] Working directory: C:\EVisionBetCode
[DEBUG] Data directory: C:\EVisionBetCode\data
[DEBUG] Data dir exists: True
[DEBUG] Raw CSV exists: True
```

### 4. Better Error Messages

When CSV is not found, now shows:
```
[!] /path/to/raw_odds_pure.csv not found
[!] Looking in: /path/to/data
[!] Data directory exists: True/False
[!] Contents of /path/to/data:
    - file1.csv
    - file2.csv
```

---

## Files Modified

### `pipeline_v2/extract_odds.py`
- Added `get_data_dir()` function (lines 27-67)
- Updated data directory initialization
- Added debug output to `main()` (lines 661-669)

### `pipeline_v2/calculate_opportunities.py`
- Added `get_data_dir()` function (lines 60-81)
- Updated .env loading with explicit path
- Added debug output to `main()` (lines 619-627)
- Enhanced `read_raw_odds()` error messages (lines 191-220)

---

## Testing

### Local Testing (✅ Passed)
```bash
cd C:\EVisionBetCode
python pipeline_v2/calculate_opportunities.py
```

**Result:**
```
[OK] Read 972 rows from C:\EVisionBetCode\data\raw_odds_pure.csv
[OK] Found 17 EV opportunities
[OK] Wrote 17 opportunities to C:\EVisionBetCode\data\ev_opportunities.csv
[DONE] Complete
```

---

## Render Deployment Next Steps

1. **Update Render cron job settings** (if needed):
   - Root Directory: `.` (dot)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python pipeline_v2/calculate_opportunities.py`

2. **Trigger a manual run** in Render to test:
   - Check logs for `[DEBUG]` output to verify path resolution
   - Should see `[OK] Read XXX rows...` if successful
   - Check database to confirm data was written

3. **Monitor first execution** to ensure:
   - No path errors
   - CSV files are being read/written correctly
   - Database connection works

---

## Backward Compatibility

✅ All changes are backward compatible:
- Local development still works with relative paths
- Fallback logic ensures compatibility with different deployment scenarios
- No breaking changes to function signatures or APIs

---

## Expected Render Behavior

When `calculate_opportunities.py` runs on Render:

1. **Debug output** shows actual paths being used
2. **Path resolution** tries multiple strategies in order
3. **Directory creation** ensures `/data` exists even if missing
4. **Error messages** clearly show what's wrong if file is still not found

---

## Success Indicators

✅ Script runs without path errors  
✅ CSV files are read from correct location  
✅ Output CSV is written successfully  
✅ Database inserts complete without errors  
✅ Debug output shows correct paths  

---

## Related Documentation

- `RENDER_DEPLOYMENT.md` - Cron job setup instructions
- `DEPLOYMENT_CHECKLIST.md` - Deployment progress tracking
- `.github/copilot-instructions.md` - System architecture reference
