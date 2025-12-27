# EVisionBet V3 - STANDARDIZED SETUP
## December 28, 2025

---

## ✅ CURRENT STATE

**ONE STANDARD V3 EXTRACTOR:**
- File: `extract_nba_v3.py` (root of EVisionBetCode)
- Output: `data/v3/extracts/basketball_nba_raw_YYYYMMDD_HHMMSS.csv`
- Format: **196 rows × 61 columns** (8 core + 53 bookmakers)

**Core Columns (8):**
1. `event_id` - Unique event ID
2. `extracted_at` - ISO timestamp of extraction
3. `commence_time` - Event start time (formatted: "10:10pm 27/12/25")
4. `league` - League name ("NBA")
5. `event_name` - Event description ("Team A @ Team B")
6. `market_type` - Market type (h2h, spreads, totals, h2h_lay)
7. `point` - Line/spread value (empty for h2h)
8. `selection` - Outcome selection (team name or Over/Under)

**Bookmakers (53):**
All major regional books organized alphabetically:
- EU: betfair_ex_eu, pinnacle, unibet, williamhill, etc.
- US: draftkings, fanduel, betmgm, bovada, espnbet, etc.
- AU: sportsbet, pointsbetau, neds, tab, betr_au, etc.
- Specialized: betclic_fr, winamax_de, tipico_de, etc.

---

## 🚀 HOW TO USE

### Extract Fresh NBA Data
```bash
cd C:\EVisionBetCode
python extract_nba_v3.py
```

Creates: `data/v3/extracts/basketball_nba_raw_YYYYMMDD_HHMMSS.csv`

### View Latest Extraction
```bash
ls -la data/v3/extracts/
# Use the most recent .csv file
```

---

## 🗂️ V3 DIRECTORY STRUCTURE

```
EVisionBetCode/
├── extract_nba_v3.py              ← MAIN EXTRACTOR (run this!)
├── data/
│   └── v3/
│       └── extracts/
│           ├── basketball_nba_raw_20251228_002702.csv  ← Latest
│           ├── basketball_nba_raw_20251228_002557.csv
│           ├── basketball_nba_raw_20251227_065532.csv  ← Your reference
│           └── nba_raw.csv                             ← OLD (ignore)
└── src/
    └── v3/                        ← OLD V3 structure (ignore for now)
```

---

## ⚠️ CLEANUP ACTIONS NEEDED

### 1. Delete Old/Duplicate Code
```bash
# Old V3 modular structure (not using)
rm -r src/v3/

# Old pipeline  
rm pipeline_v3.py

# Old V2
rm src/pipeline_v2/
```

### 2. Keep Only ONE Extractor
- ✅ Use: `extract_nba_v3.py` (clean, simple, your standard)
- ❌ Delete: `pipeline_v3.py`, `pipeline_v2/*`, `src/v3/`

### 3. Data Consolidation
- Keep all CSVs in: `data/v3/extracts/`
- Always use LATEST CSV for analysis
- Old CSVs can be archived if needed

---

## 📋 CHECKLIST

- [ ] Run `python extract_nba_v3.py` once
- [ ] Verify output in `data/v3/extracts/`
- [ ] Check CSV has 196 rows × 61 columns
- [ ] Delete old code (src/v3/, pipeline_v3.py, etc.)
- [ ] Update backend API to read latest CSV from `data/v3/extracts/`
- [ ] Test in frontend

---

## 🔄 NEXT STEPS

1. **Fine-tune CSV** (if needed):
   - Add calculations? (implied probability, vig%, etc.)
   - Filter low-coverage lines?
   - Change bookmaker order?

2. **Connect to backend**:
   - Update `backend_api.py` to read from `data/v3/extracts/`
   - Add latest CSV detection logic

3. **Schedule extraction**:
   - Add cron job or scheduler for auto-refresh
   - Update every 2 hours? 4 hours?

---

## 💾 API KEY SETUP

Ensure `.env` file has:
```
ODDS_API_KEY=your_actual_key_here
```

Check if working:
```bash
python extract_nba_v3.py
# Should show: ✅ Found 9 events
```

---

**Everything is NOW standardized to ONE setup. No more confusion!**
