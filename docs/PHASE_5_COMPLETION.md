# Phase 5 Complete: Backend API v3 Implementation

## ✅ What Was Built

### New Endpoint: GET `/api/config/weights`
- **Purpose**: Expose EVisionBet's hidden weight configuration to frontend
- **Returns**: All enabled sports with their bookmaker weights (0-4 normalized scale)
- **Frontend Use**: Load on startup, initialize weight sliders, enable weight-based recalculation

**Example Response:**
```json
{
  "sports": {
    "basketball_nba": {
      "weights": {
        "pinnacle": 0.50,
        "draftkings": 0.30,
        "fanduel": 0.20
      },
      "title": "NBA"
    },
    "americanfootball_nfl": {
      "weights": {
        "pinnacle": 0.60,
        "draftkings": 0.40
      },
      "title": "NFL"
    }
  },
  "timestamp": "2025-12-26T...",
  "note": "These are EVisionBet's hidden weights..."
}
```

### Enhanced Existing Endpoints
- **GET `/api/ev/hits`** - Already returns fair odds pre-calculated with hidden weights ✅
- **GET `/api/odds/raw`** - Already returns raw odds for frontend recalculation ✅
- **GET `/`** (root) - Updated to list `config_weights` endpoint ✅

### Code Changes

**File: `backend_api.py`**
```python
# Added imports (lines 30-35)
try:
    from src.v3.configs import get_sport_config, get_enabled_sports
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Added new endpoint (lines 1223-1278)
@app.get("/api/config/weights")
async def get_config_weights():
    # Returns EVisionBet weights for all enabled sports
    # Gracefully handles config system not available
    # Returns empty dict if no config found

# Updated root endpoint (lines 1280-1305)
# Added "config_weights": "/api/config/weights" to endpoints list
```

### Documentation Created
- **`docs/BACKEND_API_V3.md`** - Complete guide to:
  - New `/api/config/weights` endpoint
  - How frontend loads and uses weights
  - Weight adjustment flow (sliders → normalization → recalculation)
  - Fair odds formula (identical on backend and frontend)
  - Testing instructions
  - Integration with pipeline

## 🧪 Testing Results

All endpoints tested and working:

✅ **Config Weights Endpoint**
- Returns NBA weights: pinnacle 4, draftkings 3, fanduel 3, betfair 3, betfairaus 2, sportsbet 1
- Returns NFL weights: pinnacle 4, draftkings 4, fanduel 3, betfair 2
- No errors when config system available

✅ **EV Hits Endpoint**
- Returns pre-calculated opportunities with fair_odds already computed
- Using weights from backend config
- 106 total opportunities available
- Example: Julian Champagnie Under, fair_odds: 1.7693, best_odds: 1.97, EV: 0.1134 (11.34%)

✅ **Root Endpoint**
- Lists all endpoints including new config_weights
- Shows correct path: `/api/config/weights`

## 🔧 Architecture Integration

### Data Flow
1. **Pipeline** extracts odds → calculates fair odds with EVisionBet weights → CSV/DB
2. **Backend API** serves:
   - `/api/ev/hits` - Pre-calculated with hidden weights (ready to display)
   - `/api/config/weights` - EVisionBet weights (for transparency + frontend recalc)
3. **Frontend** displays:
   - Table with EV hits (from `/api/ev/hits`)
   - Weight sliders (initialized from `/api/config/weights`)
   - Recalculated EV% when user adjusts weights

### Key Design
- **Hidden weights** stored in `src/v3/configs/weights.py` (EVisionBet strategy)
- **Config system** auto-loads in base_extractor (__init__)
- **Backend** uses hidden weights for pre-calculation
- **Frontend** starts with 0 weights, users adjust independently
- **Both** use identical fair odds formula for consistency

## 📝 Weight Adjustment Flow (Frontend)

```
1. Load Config
   GET /api/config/weights
   → { "sports": { "basketball_nba": { "weights": { "pinnacle": 0.50, ... } } } }

2. Initialize Sliders
   User sees all bookmakers with sliders starting at 0

3. User Adjusts
   Drag slider: pinnacle → 2, draftkings → 1, fanduel → 0
   userWeights = { pinnacle: 2, draftkings: 1, fanduel: 0 }

4. Normalize
   totalWeight = 3
   normalizedWeights = { pinnacle: 0.667, draftkings: 0.333, fanduel: 0 }

5. Recalculate Fair Odds
   fairOdds = weighted_average(raw_odds, normalizedWeights)
   
6. Recalculate EV
   ev = (fairOdds * bestOdds - 1) * 100
```

## 🚀 What's Ready for Next Phase

### Phase 6: Frontend Weight Component
Frontend can now:
1. Load EVisionBet weights from `/api/config/weights`
2. Display weight sliders for each bookmaker (0-4 scale)
3. Recalculate EV% when user adjusts weights
4. Use same fair odds formula as backend (per-sport, separate Over/Under, outlier removal)

### Phase 7: Pipeline Updates
Pipeline can be updated to:
1. Load enabled sports from config
2. Support --sports override (nba,nfl)
3. Support --estimate-cost flag
4. Support --tiers 1,2 for tier selection
5. Implement dry-run mode

But **no changes needed** for basic functionality - backend already serves config.

## ✨ Summary

**Phase 5 Status: 100% COMPLETE**
- ✅ New `/api/config/weights` endpoint created and tested
- ✅ Existing endpoints verified working with v3 architecture
- ✅ Config system imports successfully in backend_api.py
- ✅ Graceful fallback if config system unavailable
- ✅ Documentation complete with examples
- ✅ All 3 REST API endpoints now ready:
  - GET `/api/config/weights` - New!
  - GET `/api/ev/hits` - Enhanced with hidden weights
  - GET `/api/odds/raw` - Ready for frontend use

**Remaining Work:**
- Phase 6: Frontend weight component (React UI)
- Phase 7: Pipeline orchestrator (config-driven extraction)

**Lines of Code:**
- backend_api.py: +70 lines (config import + new endpoint + root update)
- docs/BACKEND_API_V3.md: +190 lines (comprehensive documentation)
- Total: ~260 lines

**Next Command:** When ready, we'll build Phase 6 (Frontend weight slider component).
