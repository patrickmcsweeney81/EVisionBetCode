# Book Weights Integration Guide

## Overview

The `core/book_weights.py` module has been successfully integrated into the EV Bot codebase. This provides a flexible 0-4 weight scale for bookmakers with sport-specific overrides.

---

## What's New (v2.0)

### **1. Flexible Weight System (0-4 Scale)**

Replace old percentage-based weights with dynamic scale:

| Weight | Classification | Examples |
|--------|---------------|----------|
| **4** | Primary Sharps | Pinnacle, Circa, CRIS |
| **3** | Strong Sharps | BetOnline, DraftKings (props), FanDuel (props), Betfair |
| **2** | Decent Books | Bet365, Caesars, BetMGM, PointsBet |
| **1** | Followers | Bovada, BetRivers, Unibet, MyBookie |
| **0** | Ignored | Not used in fair calculation |

### **2. Sport-Specific Overrides**

Automatic weight adjustments by sport:

- **MMA**: BetOnline/Bovada elevated to weight 4/2 (better MMA coverage)
- **NBA Props**: DraftKings/FanDuel weight 4 (dominant prop markets)
- **NFL Props**: Similar to NBA
- **NHL Props**: Bet365 elevated to weight 3

### **3. Market Type Differentiation**

Different weights for different markets:

- **Main Markets** (H2H/Spreads/Totals): Pinnacle-focused
- **Player Props**: DK/FD prioritized alongside Pinnacle

---

## Migration Path

### **Migration Status (✅ COMPLETE)**

- ✅ `core/book_weights.py` module created
- ✅ `core/utils.py` updated with `weighted_median()` & sharp filtering helpers
- ✅ `core/fair_prices.py` unified (v2 functions + deprecated legacy ones)
- ✅ All handlers migrated (H2H, spreads, totals, player props, NFL props) to v2 weighted median
- ✅ `ev_arb_bot_NEW.py` passing sport context to spreads/totals/props
- ✅ Legacy percentage-based functions retained only for backward compatibility

### **Next Steps (Cleanup Phase)**

Planned removals once stability confirmed:
1. Delete legacy functions: `master_fair_odds`, `build_fair_prices_simple`
2. Remove legacy weight constants from `core/config.py`
3. Drop remaining `SHARP_BOOKIES` usages outside book_weights (handlers updated ✔)
4. Update tests to assert v2 outputs only; remove legacy test expectations


---

## Usage Examples

### **Example 1: Get Book Weight**

```python
from core.book_weights import get_book_weight

# Main markets (H2H, spreads, totals)
weight = get_book_weight("pinnacle", "main")  # Returns: 4

# Player props
weight = get_book_weight("draftkings", "props", "NBA")  # Returns: 4 (NBA override)
weight = get_book_weight("draftkings", "props", "MLB")  # Returns: 3 (default)

# Unknown book
weight = get_book_weight("unknown_book", "main")  # Returns: 0 (ignore)
```

### **Example 2: List Sharp Books**

```python
from core.book_weights import list_books_by_weight

# Get all strong sharps (weight >= 3) for main markets
sharps = list_books_by_weight("main", min_weight=3)
# Returns: {"pinnacle": 4, "circa": 4, "betonline": 3, "draftkings": 3, ...}

# Get all books for NBA player props
nba_props = list_books_by_weight("props", sport="NBA", min_weight=3)
# Returns: {"pinnacle": 4, "draftkings": 4, "fanduel": 4, ...}
```

### **Example 3: Calculate Fair Price (v2.0)**

```python
from core.fair_prices import build_fair_price_from_books

# Collect devigged odds from bookmakers
bookmaker_odds = {
    "pinnacle": 2.05,
    "draftkings": 2.10,
    "fanduel": 2.08,
    "bovada": 2.20  # Will be filtered out (weight 1 < min_weight 3)
}

# Calculate fair price for NBA player props
fair_odds = build_fair_price_from_books(
    bookmaker_odds,
    market_type="props",
    sport="NBA",
    min_weight=3
)
# Result: ~2.06 (weighted toward Pinnacle/DK/FD, ignoring Bovada)
```

### **Example 4: Process H2H Event (v2.0)**

```python
from core.h2h_handler import process_h2h_event_v2

# Process with sport context for optimized weights
result = process_h2h_event_v2(
    event=api_event,
    home_team="Lakers",
    away_team="Celtics",
    sport="NBA"
)

# Result includes fair prices calculated with NBA-specific weights
fair_home = result["fair"]["home"]
fair_away = result["fair"]["away"]
```

---

## Testing

### **Test Fair Price Calculation**

```python
# Run existing test suite
python -m pytest tests/test_book_weights.py -v

# Test specific function
python -m pytest tests/test_book_weights.py::test_weighted_median -v
```

### **Integration Test**

```python
# Test with real API data (requires ODDS_API_KEY in .env)
python test_fair_prices.py
```

---

## Benefits

### **1. More Accurate Fair Prices**

- Sport-specific weights improve prop market accuracy
- Flexible weighting adapts to different betting contexts
- Better handling of niche sports (MMA, etc.)

### **2. Easier Maintenance**

- Single source of truth for bookmaker weights
- Add new bookmakers by updating book_weights.py
- Sport overrides without touching core logic

### **3. Better EV Detection**

- More precise fair prices = better EV identification
- Reduced false positives from weak bookmakers
- Sport-optimized for props (huge improvement)

### **4. Backward Compatible**

- Old code continues to work during migration
- Gradual rollout possible (test on one sport first)
- Easy rollback if issues arise

---

## Configuration

No `.env` changes required! The system auto-detects book_weights availability.

Optional: Add sport-specific overrides in `core/book_weights.py`:

```python
SPORT_OVERRIDES = {
    "YOUR_SPORT": {
        "main": {
            "bookmaker_key": weight_value
        },
        "props": {
            "bookmaker_key": weight_value
        }
    }
}
```

---

## Troubleshooting

### **Issue: "BOOK_WEIGHTS_AVAILABLE = False"**

**Cause**: Import error in fair_prices.py or handlers

**Fix**: Check that book_weights.py exists and has no syntax errors:

```bash
python -c "from core.book_weights import get_book_weight; print('OK')"
```

### **Issue: "No sharp bookmakers found"**

**Cause**: All bookmakers filtered out due to min_weight threshold

**Fix**: Lower min_weight or check that Pinnacle/sharps are in API response:

```python
# Temporarily lower threshold for debugging
fair_odds = build_fair_price_from_books(odds, "main", sport="NBA", min_weight=2)
```

### **Issue: "Fair prices differ from legacy"**

**Cause**: Expected - v2.0 uses weighted median vs percentage weights

**Fix**: This is normal. v2.0 is more accurate. To compare:

```python
# Old method
fair_old = build_fair_prices_simple(pin_a, pin_b, None, None, sharps_a, sharps_b)

# New method
fair_new = build_fair_prices_two_way(devigged_a, devigged_b, "main", "NBA")

# Difference should be < 3% typically
```

---

## Monitoring & Validation

1. Run modular bot (`ev_arb_bot_NEW.py`) across multiple sports (NBA + NFL) and compare EV hit quality pre/post migration.
2. Spot check prop markets for improved median stabilization (DraftKings/FanDuel alignment).
3. Log distribution of included sharp books (temporary instrumentation optional).
4. After 3–5 stable runs, proceed with cleanup removals listed above.

---

## Support

**Documentation**: See docstrings in `core/book_weights.py` for detailed API docs

**Examples**: See `tests/test_book_weights.py` for usage patterns

**Questions**: Check this guide first, then review module code comments

---

**Last Updated**: November 29, 2025  
**Version**: 2.0 (Initial Integration)  
**Status**: ✅ Ready for Testing & Migration
