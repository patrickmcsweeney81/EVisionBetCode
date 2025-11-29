# EV Bot AI Agent Instructions

This project is an expected value (EV) finder that analyzes odds from various bookmakers using The Odds API. Arbitrage functionality has been removed; focus is EV-only.

## Core Architecture

- **Main Components**:
   - `ev_arb_bot.py`: Core engine that processes odds data and identifies EV opportunities (h2h, spreads, totals)
   - `data/`: Directory containing state persistence files
      - `seen_hits.json`: Deduplication storage for previously identified opportunities
      - `hits_log.csv`: CSV log of detected EV hits (legacy combined format retained)
      - `hits_ev.csv`: EV-only CSV with custom bookmaker columns

## Key Concepts

1. **Fair Price Calculation**
   - Uses multiple "sharp" bookmakers (Pinnacle, Betfair) to establish fair market prices
   - Betfair odds are adjusted for commission (default 6%)
   - Final fair price is median of available sharp bookmaker prices

2. **Opportunity Detection**
   - EV (Expected Value) threshold: configurable via `EV_MIN_EDGE` (default 3%)
   - Supports markets: h2h, spreads, totals (configure via `MARKETS`)
   - Targets primarily Australian bookmakers with configurable list

## Configuration

- Environment variables in `.env` control core behavior (excerpt):
   ```
   ODDS_API_KEY=           # Required: API key for odds data
   REGIONS=au,us          # Target regions for odds
   MARKETS=h2h,spreads,totals  # Market types to analyze (EV-only)
   SPORTS=upcoming        # Sports to scan ("upcoming" or specific list)
   EV_MIN_EDGE=0.03       # Minimum EV edge threshold
   BETFAIR_COMMISSION=0.06 # Betfair commission adjustment
   FAIR_WEIGHT_PINNACLE=0.5
   FAIR_WEIGHT_BETFAIR=0.3
   FAIR_WEIGHT_SHARPS=0.2
   TELEGRAM_ENABLED=1
   BANKROLL=1000
   KELLY_FRACTION=0.25
   ```

## Development Patterns

1. **Error Handling**:
   - Graceful fallbacks for missing configurations (see `load_env()`)
   - Soft failure for missing optional dependencies (e.g., python-dotenv)

2. **Data Management**:
   - Deduplication via SHA1 hashes of event details
   - CSV logging with UTC timestamps for all EV hits
   - Automatic directory/file creation on first run

3. **Code Organization**:
   - Functions grouped by purpose with clear section headers
   - Configuration helpers at top level
   - Core logic separated into discrete mathematical and API functions

## Integration Points

1. **External APIs**:
   - The Odds API v4 (primary data source)
   - Telegram (optional) for EV hit and summary notifications

2. **File System**:
   - Uses `pathlib` for cross-platform path handling
   - Data directory auto-created in same location as script

## Common Tasks

1. **Running the Bot**:
   - Configure `.env` with required API keys and desired markets
   - Execute `launcher.bat` or run `python ev_arb_bot.py` directly
   - Output logged to `data/hits_log.csv` and `data/hits_ev.csv`

2. **Adding New Bookmakers**:
   - Update `AU_BOOKIES` or `SHARP_BOOKIES` lists in the script
   - Ensure bookmaker IDs match The Odds API naming convention

When modifying this codebase, preserve error handling patterns and ensure any new features maintain deduplication logic to prevent duplicate EV notifications. Arbitrage code paths have been removed; reintroducing them would require reinstating fair odds pairing and stake splitting logic.