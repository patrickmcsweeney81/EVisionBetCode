# Configuration Guide

## Quick Edit Reference

### **Want to add/remove bookmakers?**
📍 Edit: `core/config.py`
- `SHARP_BOOKIES` - Sharp books for fair price calculation
- `AU_BOOKIES` - Australian target books for EV detection
- `ALL_BOOKIES_ORDERED` - Controls CSV column order

### **Want to change EV thresholds?**
📍 Edit: `core/config.py` or `.env`
- `EV_MIN_EDGE` - Minimum EV % (default: 0.015 = 1.5%)
- `MIN_PROB` - Minimum probability (default: 0.15 = 15%)
- `MIN_STAKE` - Minimum stake to log (default: $5)

### **Want to change bankroll/Kelly?**
📍 Edit: `core/config.py` or `.env`
- `BANKROLL` - Total bankroll (default: $1000)
- `KELLY_FRACTION` - Kelly fraction (default: 0.25 = 25%)

### **Want to change fair price weights?**
📍 Edit: `core/config.py`
- `WEIGHT_PINNACLE` - Pinnacle weight (default: 0.75 = 75%)
- `WEIGHT_OTHER_SHARPS` - Other sharps weight (default: 0.25 = 25%)

### **Want to change which sports to scan?**
📍 Edit: `.env`
- `SPORTS` - Comma-separated sport keys (e.g., `basketball_nba,soccer_epl`)
- `MARKETS` - Markets to analyze (e.g., `h2h,spreads,totals`)

### **Want to change API settings?**
📍 Edit: `.env` (keep secrets here!)
- `ODDS_API_KEY` - Your API key
- `REGIONS` - Regions to query (e.g., `au,us,eu`)

---

## Configuration Priority

**Values are loaded in this order** (later overrides earlier):

1. **`core/config.py`** - Default values for all settings
2. **`.env` file** - User overrides (optional)
3. **Environment variables** - System-level overrides (rare)

**Example:**
- `core/config.py` sets `EV_MIN_EDGE = 0.015` (1.5%)
- `.env` sets `EV_MIN_EDGE=0.03` (3%)
- **Bot uses 3%** (env override wins)

---

## Files Overview

### `core/config.py` - Main Configuration
✅ **Edit freely** - This is where you customize bot behavior
- Bookmaker lists
- Thresholds and filters
- Weights for fair prices
- File names

### `.env` - Secrets & Sport Selection
🔒 **Keep secrets here** (API keys, Telegram tokens)
🎯 **Sport selection** - Easy to change which sports to scan
- Never commit to Git!
- Override any config.py value here

### `ev_arb_bot_NEW.py` - Main Bot
⚠️ **Rarely needs editing** - Uses config from above files
- Only edit for new features or bug fixes

### `core/*.py` - Handler Modules
⚠️ **Advanced only** - Core logic for each market type
- `fair_prices.py` - Fair price calculation
- `h2h_handler.py` - Head-to-head markets
- `spreads_handler.py` - Spread markets
- `totals_handler.py` - Totals markets
- `logging.py` - CSV logging
- `utils.py` - Helper functions

---

## Common Tasks

### Add a new Australian bookmaker
1. Open `core/config.py`
2. Add to `AU_BOOKIES` list: `"newbook",`
3. Add to `ALL_BOOKIES_ORDERED` in desired position
4. Save and run - bot will automatically log it in CSV

### Remove a bookmaker from fair calculation
1. Open `core/config.py`
2. Remove from `SHARP_BOOKIES` list
3. Save and run

### Change minimum EV threshold temporarily
1. Open `.env`
2. Change `EV_MIN_EDGE=0.03` to desired value (e.g., `0.02` for 2%)
3. Save and run (no need to edit code)

### Scan different sports
1. Open `.env`
2. Edit `SPORTS=` line with comma-separated sport keys
3. Available sports: `basketball_nba`, `soccer_epl`, `icehockey_nhl`, etc.
4. Save and run

---

## Tips

- **Test changes on one sport first** - Set `SPORTS=basketball_nba` to test quickly
- **Check CSV output** - Verify new bookmakers appear in columns
- **Monitor API usage** - More sports = more API calls
- **Backup config** - Save a copy before major changes

---

## Need Help?

**Common issues:**
- Bookmaker not appearing? Check exact API key name (e.g., `pointsbetau` not `pointsbet`)
- No EV hits? Try lowering `EV_MIN_EDGE` temporarily to test
- CSV columns wrong? Check `ALL_BOOKIES_ORDERED` order in config.py
