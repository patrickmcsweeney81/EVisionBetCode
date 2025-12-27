# ✅ CURRENT STATE & CLEANUP - ONE FOLDER ONLY

**Date:** December 28, 2025  
**Status:** STANDARDIZED TO ONE V3 SETUP  
**Reference CSV:** `data/v3/extracts/basketball_nba_raw_20251227_065532.csv`

---

## 🎯 THE SINGLE SOURCE OF TRUTH

### ACTIVE FILES (Use These)
```
EVisionBetCode/
├── extract_nba_v3.py              ← ONLY extractor (run this)
├── backend_api.py                 ← API (not connected yet)
├── bookmaker_ratings.py           ← Ratings system (locked)
├── data/v3/extracts/              ← Output CSVs (only folder for data)
│   └── basketball_nba_raw_20251227_065532.csv  ← YOUR REFERENCE
├── .env                           ← Config (API key)
└── [other config files]
```

### DOCUMENTATION (All Current & Valid)
```
✅ V3_STANDARDIZED_SETUP.md   ← Full setup guide (READ THIS FIRST)
✅ NEW_COMPUTER_SETUP.md       ← Status & next steps
✅ README.md                   ← Quick reference
✅ PATS_FILE.md                ← Personal guide
✅ VSCODE_SETUP.md             ← Development tools
```

### ARCHIVE FOLDER (Historical - Don't Run)
```
archive/
├── pipeline_v2/               ← OLD two-stage pipeline
├── pipeline_v3.py             ← OLD monolithic extractor
├── v3/                        ← OLD modular v3 structure
└── [other old code]
```

---

## ✅ WHAT'S ALREADY DONE

1. **Bookmaker Ratings (LOCKED)**
   - 54 books in 5 tiers (4⭐→0⭐→3⭐→2⭐→1⭐)
   - File: `bookmaker_ratings.py`
   - Columns ordered by tier (NEVER CHANGES)

2. **Extract Logic (STANDARDIZED)**
   - File: `extract_nba_v3.py`
   - Output: 62 columns (8 core + 54 bookmakers)
   - Format: Decimal odds, clean CSV
   - Spreads/totals: Only .5 point lines (no whole numbers)
   - Last run: 72 rows (9 games consolidated)

3. **Reference Data**
   - File: `data/v3/extracts/basketball_nba_raw_20251227_065532.csv`
   - Use this to validate new runs
   - Same structure = good

---

## 🚫 WHAT NOT TO DO

| ❌ Don't | ✅ Do Instead |
|---------|-------------|
| Run `pipeline_v2.py` | Run `extract_nba_v3.py` |
| Use code in `src/v3/` | Use `extract_nba_v3.py` |
| Look in `archive/pipeline_v3.py` | Read `V3_STANDARDIZED_SETUP.md` |
| Create new v3 folders | Keep everything in `EVisionBetCode/` |
| Modify `bookmaker_ratings.py` tiers | Only update if business needs change |
| Save CSVs to different folders | Always save to `data/v3/extracts/` |

---

## 🔄 CURRENT WORKFLOW

1. **Run extraction:**
   ```bash
   python extract_nba_v3.py
   ```

2. **Check output:**
   - File created in: `data/v3/extracts/`
   - Format: `basketball_nba_raw_YYYYMMDD_HHMMSS.csv`
   - Columns: 62 (8 core + 54 books)
   - Check against: `basketball_nba_raw_20251227_065532.csv`

3. **Verify:**
   - All 54 bookmakers present
   - Spreads/totals in .5 format only
   - No duplicate rows per market

---

## 📋 IF CONFUSED - READ IN ORDER

1. **Start:** This file (CURRENT_STATE_CLEANUP.md)
2. **Setup:** V3_STANDARDIZED_SETUP.md
3. **Quick Ref:** README.md
4. **Personal:** PATS_FILE.md

**That's it. Nothing else needed.**

---

## ⚠️ KEY POINTS

- **ONE extractor:** `extract_nba_v3.py`
- **ONE data folder:** `data/v3/extracts/`
- **ONE reference:** `basketball_nba_raw_20251227_065532.csv`
- **ONE config:** `bookmaker_ratings.py`
- **No confusion:** All old code in archive

---

## 🎯 NEXT STEPS (After Cleanup)

1. ✅ Run `extract_nba_v3.py` → verify output matches reference
2. ⏳ Connect `backend_api.py` to read latest CSV
3. ⏳ Add NFL extractor (same structure, different sport)
4. ⏳ Schedule auto-refresh (cron or scheduler)

---

**Status:** READY TO USE  
**Last Updated:** December 28, 2025  
**Committed:** Yes (with all V3 files)
