# EVisionBet v3 - Build Completion Report

**Date:** December 26, 2025  
**Status:** ✅ CORE ARCHITECTURE COMPLETE  
**Next:** Backend API + Frontend integration

---

## 📊 What Was Built

### Phase 1: Configuration Layer (6 Files)
✅ **COMPLETE** - All configurations now modular and per-sport customizable

```
src/v3/configs/
├── __init__.py              ← Exports all configs
├── sports.py                ← Master sports config (6 sports defined)
├── bookmakers.py            ← Bookmaker ratings (0-4 stars)
├── weights.py               ← EVisionBet hidden weights per sport
├── fair_odds.py             ← Fair odds strategy per sport
├── regions.py               ← Region configs per sport
└── api_tiers.py             ← API tier strategy per sport
```

**What It Does:**
- All sports (NBA, NFL, NHL, Soccer, Tennis, Cricket) defined in one config
- Easy enable/disable per sport via `"enabled": True/False`
- Per-sport customization: regions, API tiers, weights, fair odds logic
- Users never see EVisionBet weights (hidden in backend only)

---

### Phase 2: Base Extractor Updates (1 File)
✅ **COMPLETE** - Now supports tier-based extraction + region awareness

**Changes Made:**
```python
# Before: All base_extractor
# Now: Tier-aware with config loading

# Added methods:
def _fetch_tier_2_props()      # Player props (if enabled)
def _fetch_tier_3_advanced()   # Advanced markets (if enabled)

# Added config awareness:
self.sport_config = get_sport_config(self.SPORT_KEY)
self.api_tiers_config = get_api_config_for_sport(self.SPORT_KEY)
self.region_config = get_regions_for_sport(self.SPORT_KEY)
self.fair_odds_config = get_fair_odds_config(self.SPORT_KEY)

# Auto-load from config:
self.REGIONS = self.region_config["extract_from"]
self.TIME_WINDOW_HOURS = self.region_config["time_window_hours"]
```

**Result:** Base extractor loads sport-specific config automatically

---

### Phase 3: Per-Sport Fair Odds Classes (2 Files)
✅ **COMPLETE** - Custom fair odds logic per sport

```
src/v3/processors/
├── fair_odds_nba.py    ← NBA: 5% outlier, min 2 sharps, Pinnacle 50% weight
└── fair_odds_nfl.py    ← NFL: 3% outlier, min 1 sharp, Pinnacle 60% weight
```

**Key Features:**
- Separate weight totals for Over/Under (FIX from v2)
- Custom outlier removal per sport
- Sport-specific sharp book requirements
- EV calculation using fair odds
- Arbitrage detection

**Example (NBA):**
```python
# Aggressive for sparse props
OUTLIER_THRESHOLD = 0.05
MIN_SHARP_COUNT = 2
WEIGHT_PROFILE = {
    "pinnacle": 0.50,
    "draftkings": 0.30,
    "fanduel": 0.20,
}
```

**Example (NFL):**
```python
# Conservative for weekly events
OUTLIER_THRESHOLD = 0.03
MIN_SHARP_COUNT = 1
WEIGHT_PROFILE = {
    "pinnacle": 0.60,
    "draftkings": 0.40,
}
```

---

### Phase 4: Sport Extractor Updates (2 Files)
✅ **COMPLETE** - NBA & NFL now config-aware + tier-ready

**Changes Made:**
- Import config system
- Update docstrings to reference config
- Simplify hardcoded regions/props (loaded from config now)
- Add tier method calls in fetch_odds()

**Result:** Extractors are now minimal, config-driven, pluggable

---

## 🎯 Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                    CONFIG LAYER                         │
│  (sports.py, bookmakers.py, weights.py, etc.)           │
│  ✓ All sports defined (6+ defined)                     │
│  ✓ All bookmakers rated 0-4 stars                      │
│  ✓ EVisionBet hidden weights                           │
│  ✓ Fair odds strategy per sport                        │
│  ✓ Regions customizable per sport                      │
│  ✓ API tiers customizable per sport                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│               BASE EXTRACTOR LAYER                      │
│  base_extractor.py - Common logic                      │
│  ✓ Loads config automatically                          │
│  ✓ Supports 3 API tiers (base, props, advanced)       │
│  ✓ Tier-aware fetch methods                            │
│  ✓ Region-aware extraction                             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           SPORT-SPECIFIC EXTRACTORS                     │
│  nba_extractor.py, nfl_extractor.py                    │
│  ✓ Inherits config-aware base                          │
│  ✓ Tier 2 props (customizable)                         │
│  ✓ Tier 3 advanced (customizable)                      │
│  ✓ Per-sport fair odds class                           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│         PER-SPORT FAIR ODDS CLASSES                    │
│  fair_odds_nba.py, fair_odds_nfl.py, etc.             │
│  ✓ Custom outlier removal                              │
│  ✓ Custom sharp count requirements                     │
│  ✓ Custom weight profiles                              │
│  ✓ Separate Over/Under weight totals (KEY FIX)        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│               OUTPUT CSV FILES                          │
│  data/v3/merged/all_raw_odds.csv (all sports)          │
│  data/v3/merged/all_ev_hits.csv (with EV%)             │
│  (Plus derived: outliers.csv, arbs.csv, etc)           │
└─────────────────────────────────────────────────────────┘
```

---

## 💾 Configuration Examples

### Enable/Disable Sports
```python
# src/v3/configs/sports.py
SPORTS_CONFIG = {
    "basketball_nba": {
        "enabled": True,    # ← Production
        ...
    },
    "americanfootball_nfl": {
        "enabled": True,    # ← Production
        ...
    },
    "ice_hockey_nhl": {
        "enabled": False,   # ← Testing/disabled
        ...
    },
}
```

### Add a New Sport
```python
# In sports.py, add:
"cricket_ipl": {
    "enabled": False,  # Start disabled
    "title": "IPL",
    "api_tiers": {...},
    "evisionbet_weights": {...},
}

# In regions.py, add:
"cricket_ipl": {
    "extract_from": ["au", "us", "eu"],
    "time_window_hours": 48,
    ...
}

# In api_tiers.py, add:
"cricket_ipl": {
    "tier_1_base_markets": True,
    "tier_2_player_props": False,
    ...
}

# In fair_odds.py, add:
"cricket_ipl": {
    "outlier_threshold": 0.05,
    "min_sharp_count": 1,
    ...
}
```

### Adjust Fair Odds Per Sport
```python
# In fair_odds.py, modify threshold:
"basketball_nba": {
    "outlier_threshold": 0.05,  # More aggressive
    ...
}

"americanfootball_nfl": {
    "outlier_threshold": 0.03,  # More conservative
    ...
}
```

### Adjust Hidden Weights
```python
# In sports.py, change EVisionBet weights:
"basketball_nba": {
    "evisionbet_weights": {
        "pinnacle": 4,        # ← Weight 4/4
        "draftkings": 3,      # ← Weight 3/4
        "fanduel": 3,         # ← Weight 3/4
        "sportsbet": 1,       # ← Weight 1/4
    },
}
```

---

## 🚀 What's Next (NOT Built Yet)

### Phase 5: Backend API (Pending)
```python
# backend_api.py - New endpoints needed:

GET /api/admin/odds/raw
  → Returns all raw odds from all_raw_odds.csv
  → Admin page uses this

GET /api/ev/hits
  → Returns EV opportunities from all_ev_hits.csv
  → Pre-calculated with EVisionBet weights

GET /api/config/weights
  → Returns EVisionBet weight config
  → Frontend uses for recalculation

GET /api/config/bookmakers
  → Returns all bookmakers for weight sliders
```

### Phase 6: Frontend Component (Pending)
```javascript
// EVHitsCard.js - New features needed:

1. Weight sliders (0-4 per bookmaker)
2. User-adjusted weight storage (localStorage)
3. EV recalculation on weight change
4. Display fair odds + EV%
```

### Phase 7: Pipeline Updates (Pending)
```python
# pipeline_v3.py improvements needed:

1. Load enabled sports from config
2. Command-line override: --sports nba,nfl
3. Cost estimation: --estimate-cost
4. Dry-run mode: --dry-run
5. Tier control: --tiers 1,2
```

---

## ✨ Key Features Implemented

| Feature | Status | Where |
|---------|--------|-------|
| Config-driven sports setup | ✅ | configs/sports.py |
| Per-sport regions | ✅ | configs/regions.py |
| Per-sport API tiers | ✅ | configs/api_tiers.py |
| Per-sport fair odds | ✅ | fair_odds_nba.py, fair_odds_nfl.py |
| Hidden EVisionBet weights | ✅ | configs/weights.py + sports.py |
| 0-4 weight system | ✅ | configs/bookmakers.py |
| Tier-aware extraction | ✅ | base_extractor.py |
| Region-aware extraction | ✅ | base_extractor.py + configs |
| Modular config files | ✅ | configs/ folder |
| Easy sport enable/disable | ✅ | configs/sports.py |
| Fix: Separate Over/Under weights | ✅ | fair_odds_nba.py, fair_odds_nfl.py |
| Frontend weight sliders | ⏳ | Next phase |
| Backend API endpoints | ⏳ | Next phase |
| Pipeline orchestration | ⏳ | Next phase |

---

## 📁 Files Created/Updated

**Created (11 files):**
1. ✅ `src/v3/configs/__init__.py` (95 lines)
2. ✅ `src/v3/configs/sports.py` (120 lines)
3. ✅ `src/v3/configs/bookmakers.py` (95 lines)
4. ✅ `src/v3/configs/weights.py` (30 lines)
5. ✅ `src/v3/configs/fair_odds.py` (55 lines)
6. ✅ `src/v3/configs/regions.py` (60 lines)
7. ✅ `src/v3/configs/api_tiers.py` (75 lines)
8. ✅ `src/v3/processors/fair_odds_nba.py` (135 lines)
9. ✅ `src/v3/processors/fair_odds_nfl.py` (135 lines)

**Updated (2 files):**
1. ✅ `src/v3/base_extractor.py` (added tier methods + config loading)
2. ✅ `src/v3/extractors/nba_extractor.py` (updated to use config)
3. ✅ `src/v3/extractors/nfl_extractor.py` (updated to use config)

**Total: 850+ lines of new/modified code**

---

## 🔍 How to Test

### 1. Check Config Loading
```python
from src.v3.configs import (
    get_sport_config,
    get_enabled_sports,
    get_api_config_for_sport,
)

# Get enabled sports
enabled = get_enabled_sports()
print(enabled)  # Should show NBA, NFL

# Get specific sport config
nba = get_sport_config("basketball_nba")
print(nba["evisionbet_weights"])  # Should show hidden weights
```

### 2. Check Fair Odds Per Sport
```python
from src.v3.processors.fair_odds_nba import NBAFairOdds
from src.v3.processors.fair_odds_nfl import NFLFairOdds

nba_calc = NBAFairOdds()
nfl_calc = NFLFairOdds()

print(nba_calc.OUTLIER_THRESHOLD)  # Should be 0.05
print(nfl_calc.OUTLIER_THRESHOLD)  # Should be 0.03
```

### 3. Check Extractors Load Config
```python
from src.v3.extractors.nba_extractor import NBAExtractor

nba = NBAExtractor()
print(nba.REGIONS)  # Should load from config
print(nba.TIME_WINDOW_HOURS)  # Should load from config
```

---

## 🎯 Summary

✅ **Configuration Layer:** Complete, modular, extensible  
✅ **Base Extractor:** Config-aware, tier-ready  
✅ **Fair Odds Classes:** Per-sport with custom logic  
✅ **Sport Extractors:** Updated to use new system  
❌ **Backend API:** Pending (easy integration)  
❌ **Frontend:** Pending (weight sliders)  
❌ **Pipeline:** Pending (orchestration updates)  

**Ready to proceed to Phase 5: Backend API**

When you're ready, I can build:
1. Backend API endpoints (/api/ev/hits, /api/config/weights)
2. Frontend weight slider component
3. Pipeline orchestrator with tier control

Just say when! 🚀
