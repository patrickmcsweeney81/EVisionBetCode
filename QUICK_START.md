# EV_ARB Bot - Quick Start Guide

**Updated:** December 9, 2025  
**Status:** Production-ready

---

## Two Systems Available

### 🟢 **Pipeline V2** (Recommended - Current)
**Location:** `pipeline_v2/`  
**Status:** ✅ Production-ready  
**Cost:** ~194 API credits per run  
**Use:** Extract raw odds, calculate EV separately

**Quick Start:**
```bash
# Stage 1: Extract raw odds (costs ~194 credits)
python pipeline_v2/extract_odds.py

# Stage 2: Calculate EV (no API calls, instant)
python pipeline_v2/calculate_opportunities.py

# Output: data/ev_opportunities.csv
```

**Features:**
- ✅ 80% cost reduction vs legacy
- ✅ Recalculate EV without API calls
- ✅ Clean data separation
- ✅ Player prop isolation (per-player grouping)
- ✅ 12 sharp bookmakers
- ✅ NHL support (core markets)

---

### 🔴 **Legacy System** (Still Available)
**File:** `ev_arb_bot.py`  
**Status:** ✅ Working, tested  
**Cost:** ~1,000+ API credits per run  
**Use:** All-in-one bot with all legacy features

**Quick Start:**
```bash
python ev_arb_bot.py
# OR
launcher.bat
```

---

## Current Status (Dec 9, 2025)

### Latest Run Results
- **Raw odds extracted:** 1,209 rows
  - NBA: 834 rows
  - NFL: 306 rows
  - NHL: 69 rows (core markets only)
- **EV opportunities found:** 51
  - NBA: 14
  - NFL: 11
  - **NHL: 26** ← New!

### Recent Updates
✅ Player props bug fixed (per-player grouping)  
✅ Pinnacle added to sharp bookmakers  
✅ NHL core markets integrated  
✅ sharp_book_count column added  
✅ Temporary debug files cleaned up  

---

## Directory Structure

```
EVisionBetCode/
│
├── pipeline_v2/               🆕 NEW: Two-stage system
│   ├── extract_odds.py            Stage 1: Extract raw odds
│   ├── calculate_opportunities.py Stage 2: Calculate EV
│   ├── ratings.py                 Bookmaker ratings
│   └── README.md                  Full documentation
│
├── ev_arb_bot.py              Legacy: All-in-one bot
├── launcher.bat               Legacy: Quick launcher
│
├── data/                      💾 Shared data files
│   ├── raw_odds_pure.csv          Raw odds from extract_odds.py
│   ├── ev_opportunities.csv       EV hits (Pipeline V2)
│   ├── seen_hits.json             Deduplication (Legacy)
│   └── api_usage.json             API quota tracking
│
├── docs/                      📄 Documentation
│   ├── README.md                  Main documentation
│   ├── TWO_STAGE_PIPELINE.md      Architecture
│   └── RAW_ODDS_EXTRACTION.md     Extraction details
│
└── .env                       ⚙️  Configuration
```

---

## Configuration

Create/update `.env`:

```bash
# Required
ODDS_API_KEY=your_api_key_here

# Sports to analyze
SPORTS=basketball_nba,americanfootball_nfl,icehockey_nhl

# Regions
REGIONS=au,us

# EV threshold (default 1%)
EV_MIN_EDGE=0.01

# Betfair commission
BETFAIR_COMMISSION=0.06

# Kelly betting
BANKROLL=1000
KELLY_FRACTION=0.25
```

---

## How It Works

### Stage 1: Raw Odds Extraction
1. Fetches odds from The Odds API v4
2. Extracts h2h, spreads, totals for all sports
3. Extracts player props (NBA/NFL only)
4. Expands to wide CSV format (one row per market/selection)
5. Output: `raw_odds_pure.csv` with 25+ bookmaker columns (wide format)

### Stage 2: EV Calculation
1. Reads `raw_odds_pure.csv` from stage 1
2. Groups by market/line/player (5-tuple key)
3. Calculates fair odds from 12 sharp bookmakers
4. Computes EV% for each outcome
5. Filters for EV >= 1%
6. Output: `ev_opportunities.csv` (51 opportunities found)

---

## Sports & Markets

| Sport | h2h | Spreads | Totals | Player Props |
|-------|-----|---------|--------|--------------|
| **NBA** | ✅ | ✅ | ✅ | ✅ 10+ markets |
| **NFL** | ✅ | ✅ | ✅ | ✅ 15+ markets |
| **NHL** | ✅ | ✅ | ✅ | ❌ Not available |

---

## Output Files

### ev_opportunities.csv

**Columns:**
- `timestamp` - When opportunity was detected
- `sport` - NBA, NFL, or NHL
- `event_id` - Unique event identifier
- `away_team`, `home_team` - Teams
- `commence_time` - Event start time
- `market` - h2h, spreads, totals, or player prop market
- `player` - Player name (if player prop)
- `line` - Spread/total line
- `selection` - Side (e.g., "Over", "Sacramento Kings")
- `sharp_book_count` - Number of sharp books with odds (2-12)
- `best_book` - Which bookmaker offers best price
- `odds_decimal` - Best available odds
- `fair_odds` - Calculated fair price from sharps
- `ev_percent` - Expected value percentage (sorted highest first)
- `implied_prob` - Implied probability of outcome
- `stake` - Recommended Kelly stake
- `[25+ bookmaker columns]` - Odds from each bookmaker

**Example Row (NBA):**
```
Donte DiVincenzo Under 3.5 assists @ Dabble 2.1
- Fair Odds: 2.0215 (median of DK, FD, BetOnline)
- Sharp Count: 3
- EV%: +3.88%
- Best Book: Dabble 2.1 (vs fair 2.0215)
```

---

## Troubleshooting

### "No EV opportunities found"
1. Check `.env` has valid `ODDS_API_KEY`
2. Verify `EV_MIN_EDGE` (default 1%)
3. Run with verbose output to see details
4. Check `raw_odds_pure.csv` was created with data from extract_odds.py

### "422 Error on props"
- Some bookmakers don't support certain prop markets
- Pipeline skips affected markets gracefully
- Check `raw_odds_pure.csv` output from extract_odds.py for affected sports

### "Not enough sharp books"
- Market excluded if <2 sharp sources available
- This is by design (confidence filtering)
- Add more bookmakers to REGIONS if needed

---

## Which System Should I Use?

| Situation | Recommendation |
|-----------|----------------|
| **Save API credits** | ✅ Pipeline V2 (80% cheaper) |
| **Production EV finding** | ✅ Pipeline V2 |
| **Recalculate without API** | ✅ Pipeline V2 |
| **Raw odds data needed** | ✅ Pipeline V2 |
| **Legacy features** | 🔴 Legacy `ev_arb_bot.py` |
| **Proven stability** | ✅ Pipeline V2 (tested, production) |

---

## Next Steps

1. **Configure `.env`** with your Odds API key
2. **Run Stage 1:** `python src/pipeline_v2/extract_odds.py`
3. **Run Stage 2:** `python src/pipeline_v2/calculate_opportunities.py`
4. **Review:** `data/ev_opportunities.csv`
5. **Place bets** on opportunities with positive EV!

---

## Documentation

- **README.md** - Full project overview
- **pipeline_v2/README.md** - Pipeline V2 detailed docs
- **docs/TWO_STAGE_PIPELINE.md** - Architecture details
- **.github/copilot-instructions.md** - AI agent instructions
- `launcher.bat` - Quick start
- `.env` - Configuration

### Pipeline V2
- `src/pipeline_v2/extract_odds.py` - Raw extraction (609 lines)
- `src/pipeline_v2/calculate_opportunities.py` - EV calculator (395 lines)
- `src/pipeline_v2/README.md` - Full docs

### Documentation
- `docs/TWO_STAGE_PIPELINE.md` - Architecture
- `docs/SETUP_GUIDE.md` - Setup instructions
- `docs/PRODUCT_PLAN.md` - Product roadmap

---

## Configuration

Both systems use `.env` in root directory:

```bash
ODDS_API_KEY=your_key_here
SPORTS=basketball_nba,americanfootball_nfl
REGIONS=au,us                # Pipeline V2: AU+US only
ODDS_FORMAT=decimal
BANKROLL=1000
KELLY_FRACTION=0.25
```

---

## Support

- **Legacy issues:** Check existing `data/hits_log.csv` and Telegram logs
- **Pipeline V2 issues:** See `pipeline_v2/README.md`
- **Documentation:** All MD files in `docs/`

---

## Recent Changes (Dec 2025)

✅ Created `pipeline_v2/` folder - new two-stage system  
✅ Moved all documentation to `docs/`  
✅ Legacy system preserved and intact  
✅ Added cost optimizations (80% reduction)  
✅ Fixed 2-way market filter for player props  
✅ Updated paths for new directory structure
