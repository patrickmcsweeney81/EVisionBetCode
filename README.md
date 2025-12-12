
# EV_ARB Bot – Sports Betting Expected Value Finder

---

## Deployment & Onboarding

This is the **backend-only** repo for the EV_ARB Bot (API, pipeline, and docs).

### 🚀 Deploy on Render





1. **Create a new Render web service**

  - Use this repo and the included `render.yaml` (auto-detects services)

2. **Set environment variables** in Render dashboard:

  - `ODDS_API_KEY` (required)
  - `DATABASE_URL` (optional, for DB features)
  - `ADMIN_PASSWORD_HASH` (for admin endpoints)

3. **No manual build steps needed** – Render uses `render.yaml` for all jobs and API


See the top of `render.yaml` for service descriptions.

---

## Local Development





1. `make dev-install` or `pip install -e ".[dev]"`

2. Add a `.env` file with your API key and config

3. Run the pipeline:

  - `python src/pipeline_v2/extract_odds.py`
  - `python src/pipeline_v2/calculate_opportunities.py`

4. Start the API locally:

  - `uvicorn backend_api:app --reload`

5. Run tests/lint/type-check:

  - `make test`, `make lint`, `make format`, `make type-check`


---

## Project Structure

- `src/pipeline_v2/` – Two-stage pipeline (extract, calculate)
- `backend_api.py` – FastAPI backend
- `data/` – Output files (gitignored)
- `render.yaml` – Render deployment config (web + cron jobs)
- `README.md` – This file
- `docs/` – Architecture, bugfix, and usage docs

---

**Current Version:** Pipeline V2 (Production)  
**Last Updated:** December 9, 2025

---


## Overview

EV_ARB Bot scans sports betting odds across multiple bookmakers and identifies **expected value (EV) opportunities**. Using The Odds API, it fetches real-time odds, calculates fair prices from sharp bookmakers, and detects profitable betting edges for Australian and global bookmakers.

**Key Features:**

---

## Quick Start


## Option 1: Full Pipeline (Recommended)

```bash
# Stage 1: Extract raw odds (costs ~194 API credits)
python src/pipeline_v2/extract_odds.py

# Stage 2: Calculate EV on extracted odds (no API calls)
python src/pipeline_v2/calculate_opportunities.py
```


**Output:** `data/ev_opportunities.csv` with all EV opportunities


## Option 2: Legacy System

```bash
# All-in-one (legacy, costs ~1,000+ API credits)
python ev_arb_bot.py
# OR
launcher.bat
```

---

## System Architecture

### Pipeline V2 (Current)

pipeline_v2/
├── extract_odds.py           Stage 1: Fetch and extract raw odds
├── calculate_opportunities.py Stage 2: Compute EV from raw data
├── ratings.py                Bookmaker ratings and weighting
└── README.md                 Detailed pipeline documentation
**File Structure:**
pipeline_v2/
├── extract_odds.py           Stage 1: Fetch and extract raw odds
├── calculate_opportunities.py Stage 2: Compute EV from raw data
├── ratings.py                Bookmaker ratings and weighting
└── README.md                 Detailed pipeline documentation
```text
```


**Data Flow:**
The Odds API
    ↓
[extract_odds.py] → raw_odds_pure.csv
    ↓
[calculate_opportunities.py] → ev_opportunities.csv


```text
The Odds API
  ↓
  [extract_odds.py] → raw_odds_pure.csv
  ↓
  [calculate_opportunities.py] → ev_opportunities.csv
```



**Current Results (as of Dec 9, 2025):**

- **1,209 raw odds rows** extracted
  - NBA: 834 rows
  - NFL: 306 rows
  - NHL: 69 rows (core markets only)
- **51 EV opportunities** identified
  - NBA: 14
  - NFL: 11
  - NHL: 26

---


## Configuration (.env)

All settings are controlled via the `.env` file:

```env
# API Configuration
ODDS_API_KEY=your_key_here                # Required
REGIONS=au,us                             # Fetch from AU and US bookmakers
MARKETS=h2h,spreads,totals                # Core markets (props auto-added per sport)

# Sports to analyze
SPORTS=basketball_nba,americanfootball_nfl,icehockey_nhl

# EV Threshold
EV_MIN_EDGE=0.01                          # Minimum 1% EV edge to report

# Sharp Bookmakers (for fair price calculation)
# Includes: Pinnacle, Draftkings, Fanduel, Betmgm, Betonline, 
#          Bovada, Lowvig, Mybookie, Betus, Betfair_AU, Betfair_EU

# Betfair Commission
BETFAIR_COMMISSION=0.06                   # 6% commission adjustment

# Kelly Betting
BANKROLL=1000
KELLY_FRACTION=0.25
```

---


---

## Key Concepts


### Fair Price Calculation

Fair odds are computed as the **median** of sharp bookmakers:

**Sharp Sources (12 total):**
- Pinnacle
- DraftKings
- FanDuel
- BetMGM
- BetOnline
- Bovada
- LowVig
- MyBookie
- Betus
- Betfair AU
- Betfair EU

**Adjustment:**
- Betfair odds are reduced by commission (default 6%)
- Requires minimum 2 sharp sources for fair price validity


### Expected Value (EV)

EV% = (fair_odds / market_odds - 1) × 100

```text
EV% = (fair_odds / market_odds - 1) × 100
```
- **Positive EV** = Profitable bet
- **EV >= 1%** = Reported opportunity
- **EV < 1%** = Filtered out


### Player Props Grouping

Player props are isolated per player using a 5-tuple key:
(sport, event_id, market, point, player_name)

```text
(sport, event_id, market, point, player_name)
```

**ev_opportunities.csv** - EV opportunities above threshold
- Columns: sport, event_id, market, player, selection, sharp_book_count, best_book, odds_decimal, fair_odds, ev_percent, stake, [bookmaker columns]
- Sorted by EV% (highest first)

### Internal
- **seen_hits.json** - Deduplication hash storage (legacy system)
- **api_usage.json** - API quota tracking
- **cache_events.json** - Event caching

```text
  - Used by calculate_opportunities.py

### Outputs
- **ev_opportunities.csv** - EV opportunities above threshold
  - Columns: sport, event_id, market, player, selection, sharp_book_count, best_book, odds_decimal, fair_odds, ev_percent, stake, [bookmaker columns]
  - Sorted by EV% (highest first)

### Internal
- **seen_hits.json** - Deduplication hash storage (legacy system)
- **api_usage.json** - API quota tracking
- **cache_events.json** - Event caching

---


---

## Sports & Markets

### Supported Sports

| Sport | Core Markets | Player Props | Notes |
|-------|-------------|--------------|-------|
| **NBA** | h2h, spreads, totals | ✅ 10+ markets | Points, rebounds, assists, etc. |
| **NFL** | h2h, spreads, totals | ✅ 15+ markets | Pass yards, TDs, receptions, etc. |
| **NHL** | h2h, spreads, totals | ❌ Not available | API limitation |

### Player Props Available

**NBA:**
- Points, Rebounds, Assists, 3-Pointers, Blocks, Steals, Turnovers
- Combo: PRA, Points+Assists, Points+Rebounds, Rebounds+Assists

**NFL:**
- Pass Yards, Pass TDs, Completions, Interceptions
- Rush Yards, Reception Yards, Receptions
- Anytime TD, First TD
- Tackles, Sacks, Defense

---


---

## File Cleanup (Dec 9, 2025)

The following temporary/debug files have been removed:
- ✅ `check_nhl_markets.py`
- ✅ `check_sports.py`
- ✅ `nba_outliers.py`
- ✅ `split_extreme_evs.py`
- ✅ `test_prop_api.py`
- ✅ `test_prop_response.py`

---


---

## Support & Troubleshooting

### No EV Opportunities Found
- Ensure `.env` has valid `ODDS_API_KEY`
- Check `EV_MIN_EDGE` threshold (default 1%)
- Verify at least 2 sharp bookmakers have odds for each market

### 422 Errors on Props
- Some bookmakers don't support certain prop markets
- Pipeline handles gracefully—affected events are skipped for that market

### API Quota Exceeded
- Check `data/api_usage.json` for remaining credits
- Wait before next run, or upgrade API tier
- Pipeline V2 uses ~194 credits per run vs ~1,000 for legacy

---


---

## Development Notes

### Adding New Sports
1. Update `SPORTS` in `.env`
2. Define prop markets in `extract_odds.py` (e.g., `NCAAF_PROPS`)
3. Update `get_props_for_sport()` function
4. Pipeline automatically handles the rest

### Modifying Fair Price Calculation
Edit `calculate_opportunities.py`:
- `SHARP_COLS` - List of sharp bookmakers
- `fair_from_sharps()` - Fair odds logic
- Commission adjustments in Betfair handling

---


---

## Contact & Support

- **Primary API:** The Odds API v4
- **Data:** Real-time odds from multiple bookmakers
- **Updates:** Check `/docs` folder for detailed guides


For questions, refer to:
- `pipeline_v2/README.md` - Pipeline-specific details
- `docs/TWO_STAGE_PIPELINE.md` - Architecture documentation
- `docs/RAW_ODDS_EXTRACTION.md` - Extraction specifics


---

## License

ISC

---


---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change. See the `/docs` folder for architecture and contribution guidelines.

---

**Frontend repo:** [EVisionBetSite](https://github.com/patrickmcsweeney81/EVisionBetSite)

**Maintainer:** Patrick McSweeney

## Author

Patrick McSweeney
