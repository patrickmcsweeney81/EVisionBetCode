# EV Bot AI Agent Instructions

**Project:** EV_ARB Bot – Sports Betting Expected Value Finder  
**Status:** Production-ready (Pipeline V2)  
**Last Updated:** December 10, 2025

---

## Project Overview

This project identifies **expected value (EV) opportunities** in sports betting by analyzing odds from multiple bookmakers using The Odds API. The system calculates fair prices from sharp bookmakers and detects profitable edges for Australian and international bookmakers.

**Core Focus:** EV-only analysis (arbitrage removed)  
**Current Version:** Pipeline V2 (two-stage extraction + calculation)

---

## Core Architecture

### Two-Stage Pipeline

**Stage 1: Raw Odds Extraction** (`pipeline_v2/raw_odds_pure.py`)
- Fetches odds from The Odds API v4
- Supports: NBA, NFL, NHL
- Markets: h2h, spreads, totals, player props (NBA/NFL only)
- Output: `data/raw_odds_pure.csv` (wide format, one row per market/selection)
- Cost: ~194 API credits per run

**Stage 2: EV Calculation** (`pipeline_v2/calculate_ev.py`)
- Reads raw odds from CSV
- Calculates fair prices from 12 sharp bookmakers
- Detects EV opportunities (>= 1% edge)
- Output: `data/ev_opportunities.csv`
- Cost: Zero API calls

### Data Files

**Inputs:**
- `raw_odds_pure.csv` - All odds across all sports/markets/bookmakers

**Outputs:**
- `ev_opportunities.csv` - EV opportunities above 1% threshold

**Internal:**
- `seen_hits.json` - Deduplication storage
- `api_usage.json` - API quota tracking
- `cache_events.json` - Event caching

---

## Key Concepts

### 1. Fair Price Calculation

Fair odds represent the "true" market price without bookmaker margins.

**Bookmaker Ratings System (52 total books):**
- **4-star (4 books):** Pinnacle, Betfair_EU, Draftkings, Fanduel - 35% weight (8.75% each)
- **3-star (7 books):** Betfair_AU, Betfair_UK, Betmgm, Betrivers, Betsson, Marathonbet, Lowvig - 40% weight (5.71% each)
- **2-star (4 books):** Nordicbet, Mybookie, Betonline, Betus - 15% weight (3.75% each)
- **1-star (37 books):** Target bookmakers (Sportsbet, Pointsbet, etc.) - 10% weight (used for EV detection, not fair odds)

**Calculation Method:**
1. Devig each sharp bookmaker's two-way odds (Over/Under)
2. Remove outliers (5% tolerance from median)
3. Calculate **weighted average** using bookmaker ratings
4. Use **separate weight totals** for Over and Under sides (critical - see BUGFIX_FAIR_ODDS_DEC10_2025.md)
5. Requires minimum 10% weight coverage for validity

**Sport-Specific Weight Profiles:**
- NBA/NFL/Soccer: Standard (35/40/15/10)
- NHL: Pinnacle-heavy (50/30/10/10)
- Cricket/Tennis: Betfair-dominated (65-75/15-25/5/5)

### 2. Player Props Grouping (Critical)

Player props are isolated per player using 5-tuple key:
```python
(sport, event_id, market, point, player_name)
```

**Why:** Multiple players in same market were previously grouped together, preventing individual player EV calculation. **Fixed Dec 2025:** Each player now has isolated fair odds calculation.

### 3. Expected Value (EV)

```
EV% = (fair_odds / market_odds - 1) × 100
```

**Thresholds:**
- **EV >= 1%** = Reported opportunity
- **EV < 1%** = Filtered out

**Current Results (Dec 10, 2025):**
- 3,238 raw rows extracted (NBA only)
- 1 EV opportunity identified (conservative detection with accurate fair odds)
- Fair odds calculation fixed: weighted average now uses separate totals for Over/Under sides

---

## Configuration

All settings in `.env`:

```bash
# API
ODDS_API_KEY=your_key                     # Required
REGIONS=au,us                             # AU + US bookmakers only
MARKETS=h2h,spreads,totals                # Core markets

# Sports
SPORTS=basketball_nba,americanfootball_nfl,icehockey_nhl

# EV Thresholds
EV_MIN_EDGE=0.01                          # Minimum 1% edge

# Betfair Commission
BETFAIR_COMMISSION=0.06

# Kelly Betting
BANKROLL=1000
KELLY_FRACTION=0.25
```

---

## Development Patterns

1. **Error Handling**:
   - Graceful 422 errors on unsupported prop markets (skipped)
   - Soft fallback for missing bookmaker odds (market excluded)
   - Missing 2+ sharps → market excluded from EV analysis

2. **Data Management**:
   - Deduplication via SHA1 hashes of event details
   - CSV logging with UTC timestamps on all rows
   - Automatic directory/file creation on first run
   - Event caching to reduce API calls

3. **Code Organization**:
   - Pipeline V2 separated into two focused modules
   - Functions grouped by purpose with clear headers
   - Configuration helpers at module top level
   - Core logic separated into discrete mathematical functions

---

## Integration Points

1. **External APIs**:
   - The Odds API v4 (primary data source)
   - Endpoint: `https://api.the-odds-api.com/v4/sports/{sport}/odds`
   - Format: Decimal odds
   - Regions: au, us

2. **File System**:
   - Uses `pathlib` for cross-platform path handling
   - Data directory auto-created in same location as script
   - CSV format with UTF-8 encoding

---

## Common Tasks

### Running Full Pipeline

```bash
# 1. Extract raw odds
python pipeline_v2/raw_odds_pure.py

# 2. Calculate EV (no API calls)
python pipeline_v2/calculate_ev.py

# Output: data/ev_opportunities.csv
```

### Adding a New Sport

1. Add to `SPORTS` in `.env`
2. Define props in `raw_odds_pure.py`
3. Update `get_props_for_sport()` function
4. Run pipeline → automatic

### Modifying Fair Price Logic

File: `pipeline_v2/bookmaker_ratings.py`
- `BOOKMAKER_RATINGS` - Dict of all 52 bookmakers with 1-4 star ratings
- `SPORT_WEIGHT_PROFILES` - Sport-specific weight distributions
- `load_weight_config(sport)` - Get weights for specific sport
- `get_sharp_books_only()` - Returns 3⭐+4⭐ books for fair odds

File: `pipeline_v2/calculate_ev.py`
- `fair_from_sharps()` - Weighted fair odds calculation with outlier removal
- `EV_MIN_EDGE` - Threshold (default 1%)

---

## Sports & Markets Status

| Sport | Core Markets | Player Props | Status |
|-------|-------------|--------------|--------|
| NBA | h2h, spreads, totals | ✅ 10+ markets | Full support |
| NFL | h2h, spreads, totals | ✅ 15+ markets | Full support |
| NHL | h2h, spreads, totals | ❌ Not available | Core only |

---

## Recent Changes (December 2025)

✅ **Bookmaker Ratings System (Dec 10):** Implemented 1-4 star rating system (52 books total) with weighted fair odds calculation. Sport-specific weight profiles for 8 sports.

✅ **Fair Odds Bug Fixed (Dec 10):** CRITICAL - Fixed weighted average calculation that was using single weight total for both Over/Under sides. Fair odds now accurate (~1.93 instead of 1.19). See docs/BUGFIX_FAIR_ODDS_DEC10_2025.md.

✅ **Outlier Detection (Dec 10):** Added 5% tolerance filter to remove stale/aberrant odds before weighting.

✅ **Player Props Grouping Fixed:** Critical bug where multiple players were grouped together is now fixed. Each player evaluated independently.

✅ **Bookmaker Expansion (Dec 10):** 52 bookmakers supported (from 15). Configurable BOOKMAKER_ORDER environment variable.

✅ **sharp_book_count Column:** Added to output showing number of sharp sources per opportunity.

✅ **NHL Support:** Added NHL core markets. Player props not available per API.

---

## When Modifying Code

### Preservation Rules
1. **Deduplication:** Maintain seen_hits.json logic
2. **Per-player isolation:** Keep 5-tuple grouping key in calculate_ev.py
3. **Separate weight totals:** CRITICAL - Over and Under sides must have independent weight totals after outlier filtering
4. **Sharp list:** Expand carefully; validate fair price logic
5. **Error handling:** Graceful degradation for missing sharps/props
6. **API efficiency:** Cache events; minimize redundant calls

### Testing Requirements
- Run with 3+ sports / 100+ rows to validate grouping
- Verify sharp_book_count accuracy
- Check EV% calculations against manual spot checks
- Validate CSV headers and column order

---

## Documentation

- **README.md** - Overview and quick start
- **pipeline_v2/README.md** - Detailed pipeline architecture
- **.env** - Configuration reference