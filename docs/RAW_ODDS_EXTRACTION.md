## RAW ODDS EXTRACTION - COMPLETE

### Structure
- **File**: `data/raw_odds_pure.csv`
- **Rows**: 760 (one row per market/selection)
- **Columns**: 61 total

### Column Order
1. **Base Columns** (9): timestamp, sport, event_id, away_team, home_team, commence_time, market, point, selection
2. **Sharp Books** (13): Pinnacle, Betfair_EU, Betfair_AU, Draftkings, Fanduel, Betmgm, Betonline, Bovada, Marathonbet, Matchbook, Lowvig, Mybookie, Betus
3. **AU Books** (13): Sportsbet, Bet365, Pointsbet, Betright, Tab, Dabble, Unibet, Ladbrokes, Playup, Tabtouch, Betr, Neds, Boombet
4. **US Books** (7): Caesars, Betrivers, Sugarhouse, Superbook, Twinspires, Wynnbet, Williamhill
5. **Unknown** (19): Various regional bookmakers

### Data Format
- **Odds Format**: Decimal (e.g., 1.900, 2.050)
- **Markets**: h2h (moneyline), spreads, totals
- **Regions**: AU, US, US2, EU
- **Sports**: NBA (16 events), NFL (29 events)

### Key Features
✓ Pure raw data - NO calculations
✓ One row per market/selection
✓ All bookmaker odds as columns
✓ Sharp books first (for fair price calculation)
✓ AU books prominently positioned
✓ Dynamic column handling (unknown bookmakers added as discovered)

### Next Steps
1. Run `calculate_ev.py` to add fair odds, EV%, prob, stakes
2. Filter for high-EV opportunities (configurable threshold)
3. Merge with additional data sources (other APIs, etc.)
4. Keep legacy `raw_odds.csv` for comparison

### Cost Efficiency
- **API Calls**: 2 sports × 3 markets × 4 regions = 24 credits per run
- **Data Points**: 760 odds rows per run
- **Remaining Credits**: 81,002 (plenty for development)
