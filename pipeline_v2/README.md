# Pipeline V2 - Two-Stage Odds Extraction & EV Calculator

## Overview

This is a **complete rewrite** of the odds extraction system with a clean two-stage architecture:

1. **Stage 1:** `extract_odds.py` - Pure data extraction (no calculations)
2. **Stage 2:** `calculate_opportunities.py` - EV calculations from raw CSV

**Key difference from legacy `ev_arb_bot.py`:**
- Separates data fetching from calculations
- Enables recalculation without API costs
- Supports multi-source data merging
- Pivoted CSV format (one row per market, all bookmakers as columns)

---

## Quick Start

### 1. Extract Raw Odds

```bash
python pipeline_v2/extract_odds.py
```

**Output:** `data/raw_odds_pure.csv`

**What it does:**
- Fetches NBA & NFL odds from Odds API v4
- Core markets: h2h, spreads, totals (all events)
- Player props: 14 NBA props + 19 NFL props (time-filtered: 5min-48hrs)
- Regions: AU + US + EU (EU added to include Pinnacle)
- 2-way market filter (Over/Under pairs only)

**Cost:** ~190 credits per run (7 NBA + 13 NFL events typical)

### 2. Calculate EV

```bash
python pipeline_v2/calculate_opportunities.py
```

---

## File Structure

```
pipeline_v2/
├── extract_odds.py            Main extraction script
├── calculate_opportunities.py  EV calculator
├── ratings.py                 Bookmaker ratings & weights
└── README.md                  This file
```

---

## Configuration

Edit `.env` in project root:

```bash
ODDS_API_KEY=your_key_here
SPORTS=basketball_nba,americanfootball_nfl
REGIONS=au,us,eu             # EU added to ensure Pinnacle odds
ODDS_FORMAT=decimal
```

**Time Window (in `raw_odds_pure.py`):**
```python
EVENT_MIN_MINUTES = 5   # Don't fetch events <5 min from now
EVENT_MAX_HOURS = 48    # Don't fetch events >48 hrs out
```

---

## Data Format

### CSV Structure

**Columns:**
- `timestamp` - UTC extraction time
- `sport` - basketball_nba or americanfootball_nfl
- `event_id` - Unique event identifier
- `away_team` - Away team name
- `home_team` - Home team name
- `commence_time` - Event start time (UTC)
- `market` - Market type (h2h, spreads, player_points, etc)
- `point` - Handicap/line value (if applicable)
- `selection` - Team name or player name (e.g., "Jalen Brunson Over 25.5")
- `Pinnacle`, `Betfair_AU`, `Draftkings`, ... - Bookmaker odds (decimal format)

**Example Row:**
```csv
timestamp,sport,event_id,away_team,home_team,commence_time,market,point,selection,Pinnacle,Draftkings,Fanduel,...
2025-12-07T04:00:00+00:00,basketball_nba,abc123,Magic,Knicks,2025-12-07T17:10:00Z,player_points,25.5,Jalen Brunson Over 25.5,1.90,1.87,1.91,...
```

---

## Cost Optimizations Implemented

| Optimization | Savings | Status |
|--------------|---------|--------|
| AU + US + EU regions (adds Pinnacle) | Costs higher than au,us | ➡️ Required for Pinnacle |
| 2-way market filter (Over/Under pairs) | **-30%** | ✅ Done |
| Time window filter (5min-48hrs) | **-20%** | ✅ Done |
| **Total** | **~80%** | **✅** |

**Before optimizations:** ~1,036 credits per run (7,213 rows)  
**After optimizations:** ~194 credits per run (10,833 rows)

**Result:** 80% cost reduction with 50% MORE data!

---

## Player Props Coverage

### NBA Props (14 markets)
- Single: points, rebounds, assists, threes, blocks, steals, turnovers
- Combos: PRA, PA, PR, RA, blocks_steals
- Special: double_double, first_basket

### NFL Props (19 markets)
- Passing: yards, TDs, completions, attempts, interceptions
- Rushing: yards, attempts
- Receiving: receptions, yards
- Combos: pass_rush_yds, rush_reception_yds
- TDs: anytime_td, 1st_td
- Defense: tackles_assists, sacks, defensive_interceptions
- Kicking: kicking_points

---

## Bookmakers Included

**Sharp Books (for fair odds):**
- Pinnacle, Betfair_AU, Betfair_EU, Draftkings, Fanduel, Betmgm

**AU Books:**
- Sportsbet, Tab, Neds, Pointsbet, Betright, Dabble, Unibet, Ladbrokes, Playup, Tabtouch, Betr, Boombet

**US Books:**
- Caesars, Betrivers, Williamhill, Ballybet, Betparx, Espnbet, Fanatics, Fliff, Hardrockbet

**Total:** ~24 bookmakers (AU + US + EU regions; Pinnacle via EU)

---

## Debugging Tools

### Check Raw Data
```bash
python pipeline_v2/sample_raw.py
```

### Test API Connection
```bash
python pipeline_v2/test_api_simple.py
```

### Inspect Prop Structure
```bash
python pipeline_v2/debug_props.py
```

---

## Known Issues

1. **calculate_ev.py not tested** - Skeleton exists but needs debugging
2. **NBA props may be sparse** - AU books often don't post NBA props until closer to game time
3. **File permission errors** - Close CSV in Excel before re-running extraction
4. **API rate limits** - 500 requests per month on free tier (we use ~194 per run = ~2 runs/day)

---

## Next Steps (TODO)

- [ ] Test and debug `calculate_ev.py`
- [ ] Implement historical archival (save each run with timestamp)
- [ ] Add multi-source merging (combine Odds API + other sources)
- [ ] Investigate Draftkings/Fanduel direct APIs for cost savings
- [ ] Add automated scheduling (cron/Task Scheduler)

---

## Comparison: Legacy vs Pipeline V2

| Feature | Legacy (`ev_arb_bot.py`) | Pipeline V2 |
|---------|--------------------------|-------------|
| Architecture | Single-pass, coupled | Two-stage, decoupled |
| Data format | Calculation-heavy | Raw odds only |
| Recalculation | Requires API call | Use cached CSV |
| Cost per run | ~1,036 credits | ~194 credits |
| Regions | 4 (au,us,us2,eu) | 3 (au,us,eu) |
| Props filter | None | 2-way markets only |
| Code size | 1,300 lines | 609 + 330 lines |
| Status | ✅ Working | ⚠️ Stage 1 working, Stage 2 untested |

---

## Support

For issues or questions, see:
- `docs/TWO_STAGE_PIPELINE.md` - Architecture details
- `docs/RAW_ODDS_EXTRACTION.md` - Extraction summary
- Legacy system: `ev_arb_bot.py` (still intact and functional)
