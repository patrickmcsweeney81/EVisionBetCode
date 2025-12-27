# EVisionBet v3 - Detailed Architecture Proposal & Review

**Date:** December 25, 2025  
**Purpose:** Full transparency review before implementation  
**Status:** Awaiting your approval on each section

---

## 📋 TABLE OF CONTENTS

1. Current State Analysis
2. Proposed Changes (Per-Sport Customization)
3. Odds API Strategy Review
4. Data Flow Diagram (Raw → Frontend)
5. File-by-File Review
6. Frontend Impact Analysis
7. Storage Efficiency Analysis
8. Approval Checklist

---

## 🔍 PART 1: Current State Analysis

### What Currently Exists

**Files:**
```
src/v3/
├── config.py                 ← Single config for all sports
├── base_extractor.py         ← Generic extraction logic
├── extractors/
│   ├── nba_extractor.py      ← Inherits from base
│   └── nfl_extractor.py      ← Inherits from base
└── processors/
    └── fair_odds_v2.py       ← Single generic logic
```

**Current Approach:**
- ✅ One config file for all sports (simple)
- ✅ Base class reuse (DRY)
- ❌ Fair odds same for all sports (not optimal)
- ❌ Regions same per sport class (limited flexibility)
- ❌ API strategy same (might waste calls)

**Current Data Flow:**
```
Odds API
    ↓
[Base Markets Only: h2h, spreads, totals]
    ↓
nba_raw.csv / nfl_raw.csv
    ↓
all_raw_odds.csv (merged)
    ↓
backend_api.py
    ↓
Frontend (React table)
```

---

## 💡 PART 2: Proposed Changes (With Your Input)

### 2.1 Fair Odds Per-Sport Customization

**Proposal:**

Create sport-specific fair odds classes:

```
src/v3/processors/
├── fair_odds_base.py         ← Abstract base
├── fair_odds_nba.py          ← NBA-specific logic
├── fair_odds_nfl.py          ← NFL-specific logic
├── fair_odds_soccer.py       ← Soccer-specific logic
└── fair_odds_tennis.py       ← Tennis-specific logic
```

**Why Different Per Sport?**

| Sport | Challenge | Custom Approach |
|-------|-----------|-----------------|
| NBA | Lots of props, sparse AU books | Weight sharps heavily, ignore AU outliers for props |
| NFL | Fewer books, weekly events | Use all available books, interpolate gaps |
| Soccer | European focus, Pinnacle dominates | Pinnacle-only for some markets |
| Tennis | H2H only, very sharp consensus | Use tight median approach |
| Cricket | Limited props, AU-focused | AU book clustering detection |

**Example: NBA vs NFL**

NBA Fair Odds:
```python
class NBAFairOdds(FairOddsBase):
    def calculate(self, market_data):
        # Remove 5% outliers aggressively (sparse props)
        # Weight sharps: Pinnacle 50%, DK 30%, FD 20%
        # Require minimum 2 sharps
        # Special handling for player props
```

NFL Fair Odds:
```python
class NFLFairOdds(FairOddsBase):
    def calculate(self, market_data):
        # Remove only extreme outliers (2-3%)
        # Weight sharps: Pinnacle 40%, DK 30%, FD 30%
        # Allow single sharp if coverage good
        # Interpolate missing markets
```

**Questions for you:**
- ✅ Do you want this level of customization per sport?
- ❓ Should we have default + override per sport?
- ❓ How many sports do you want customized initially? (Start with 2-3?)

---

### 2.2 Regions Per-Sport Customization

**Current:**
```python
SPORTS_CONFIG = {
    "basketball_nba": {"regions": ["au", "us", "eu"]},
}
```

**Proposed:**
```python
SPORTS_CONFIG = {
    "basketball_nba": {
        "regions": {
            "extraction": ["au", "us", "eu"],     # What to fetch from API
            "sharp_priority": ["us", "eu", "au"], # Preferred order for fair odds
            "exclude_from_fair": ["au"],          # Never use AU for prop fair odds
            "time_windows": {                      # Region-specific timing
                "au": 48,  # 48h window
                "us": 48,
                "eu": 72,
            }
        }
    }
}
```

**Why More Control?**
- AU books are 1-star (not sharp) for most props
- Different time zones = different event schedules per region
- Some leagues are region-specific (EPL = EU focus)
- Avoid fetching expensive EU data for AU-only sports

**Proposed Region Strategy:**

| Sport | Extraction | Sharp Source | Exclude from Fair |
|-------|------------|--------------|-------------------|
| NBA | au,us,eu | us,eu | au |
| NFL | au,us | us | au,eu |
| EPL | au,us,eu | eu,us | (none) |
| Big Bash | au | au | (none) |
| IPL | au,us,eu | eu,us | (none) |

**Questions for you:**
- ✅ Does this breakdown make sense?
- ❓ Any sports you want different strategy?
- ❓ Should we optimize by time of day? (fetch AU at night, EU during day?)

---

### 2.3 Odds API Strategy Review

**Current Implementation:**
```python
# Extract base markets only
markets = ["h2h", "spreads", "totals"]
# Per-event player props (expensive!)
```

**Analysis:**

**Current Cost per Sport:**
```
NBA:
  - Base markets (all events): ~45 credits
  - Player props (per-event): ~40+ credits
  Total: ~85 credits per run

NFL:
  - Base markets: ~30 credits
  - Player props (per-event): ~20+ credits
  Total: ~50 credits per run
```

**Problem:**
- ❌ Fetching player props per-event is expensive
- ❌ Missing 3-way markets (draws in soccer)
- ❌ Some books only have 1-way markets (need to handle)
- ❌ Not capturing all available markets for future analytics

**Proposed New Strategy:**

**Tier 1: Base Markets (Always Fetch)**
```python
markets = ["h2h", "spreads", "totals"]
# Cost: ~30-50 credits total
# Benefit: Core betting markets for EV detection
```

**Tier 2: Player Props (Selective)**
```python
# NBA: Fetch 5 major props per sport
props = ["player_points", "player_rebounds", "player_assists"]
# Cost: ~20 credits
# Benefit: High-volume player prop markets

# NFL: Fetch only if sufficient sharps available
props = ["player_pass_yds", "player_rush_yds"]
# Cost: ~15 credits

# Soccer: Skip (props minimal)
props = []
# Cost: $0
```

**Tier 3: Advanced Markets (For Analytics - Optional)**
```python
# 3-way markets (with draw): soccer, cricket, some h2h
# 1-way markets: captures all available
# Over/Under partials: handle 1.5, 2.5, 3.5 goals separately
# Cost: ~30-50 additional credits (opt-in per sport)

# Stored in separate CSV for future analysis
# Not used for immediate EV detection
# Used for: "What markets are available?" analytics
```

**New CSV Structure:**

```
data/v3/extracts/
├── nba_base_markets.csv      ← h2h, spreads, totals
├── nba_player_props.csv      ← player_points, assists, etc
├── nba_advanced.csv          ← Future: custom markets
├── nfl_base_markets.csv
├── nfl_player_props.csv
└── nfl_advanced.csv
```

**Cost Comparison:**

| Scenario | Current Cost | New Cost | Savings |
|----------|--------------|----------|---------|
| NBA only | 85 | 50 | 41% |
| NFL only | 50 | 35 | 30% |
| Both (2 sports) | 135 | 85 | 37% |
| 6 sports | 400 | 250 | 38% |
| 12 sports | 800 | 500 | 38% |

**Proposed Code Structure:**

```python
class BaseExtractor:
    def fetch_odds(self):
        # Tier 1: Always
        base = self._fetch_base_markets()
        
        # Tier 2: If enabled
        if self.FETCH_PLAYER_PROPS:
            props = self._fetch_player_props()
        
        # Tier 3: If enabled
        if self.FETCH_ADVANCED:
            advanced = self._fetch_advanced_markets()
        
        return self._merge_markets(base, props, advanced)
```

**Per-Sport Configuration:**

```python
SPORTS_CONFIG = {
    "basketball_nba": {
        "tiers": {
            "base_markets": True,       # Always
            "player_props": True,       # 5 major props
            "advanced_markets": False,  # Not needed now
        },
        "player_props_to_fetch": [
            "player_points",
            "player_rebounds",
            "player_assists",
        ]
    },
    "soccer_epl": {
        "tiers": {
            "base_markets": True,
            "player_props": False,      # Props sparse
            "advanced_markets": True,   # Track 3-way markets for analytics
        },
    }
}
```

**Questions for you:**
- ✅ Does tiered approach make sense?
- ✅ Should we fetch advanced markets now for future analytics?
- ❓ Which sports should skip player props entirely?
- ❓ How do you want to handle 3-way markets (draw, etc.)?

---

## 📊 PART 3: Data Flow Diagram (Detailed)

**Current Flow:**

```
┌─────────────────┐
│  The Odds API   │
└────────┬────────┘
         │ [45-85 credits per sport]
         ▼
┌──────────────────────────────────┐
│ [Base + Props extracted]          │
│ One CSV per sport                 │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ all_raw_odds.csv                 │
│ (1000+ rows, 17 columns)         │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ backend_api.py                    │
│ /api/odds/raw → JSON             │
│ /api/ev/hits → JSON              │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ React Frontend                    │
│ RawOddsTable.js                  │
│ EVHits.js                        │
│ Dashboard.js                     │
└──────────────────────────────────┘
```

**Proposed Flow (With Tiering):**

```
┌──────────────────┐
│ The Odds API     │
└────────┬─────────┘
         │ [Tier 1: Base Markets]
         ├─→ [Tier 2: Player Props] (if enabled)
         └─→ [Tier 3: Advanced] (if enabled)
         
         ▼ [~50-250 credits per sport]
         
┌────────────────────────────────────────┐
│ Per-Sport Extraction                   │
├────────────────────────────────────────┤
│ nba_base_markets.csv                   │
│ nba_player_props.csv                   │
│ nfl_base_markets.csv                   │
│ nfl_advanced.csv                       │
└────────┬───────────────────────────────┘
         │
         ▼ [Merge & Process]
         
┌────────────────────────────────────────┐
│ data/v3/merged/                        │
├────────────────────────────────────────┤
│ all_raw_odds.csv                       │
│ (Base + props combined, ready for EV)  │
│                                        │
│ all_advanced.csv (optional)            │
│ (3-way markets, analytics only)        │
└────────┬───────────────────────────────┘
         │
         ▼ [Fair Odds Calculation]
         
┌────────────────────────────────────────┐
│ Fair Odds (Sport-Specific)             │
├────────────────────────────────────────┤
│ NBA: Custom NBA fair odds logic        │
│ NFL: Custom NFL fair odds logic        │
│ Soccer: Custom Soccer fair odds logic  │
└────────┬───────────────────────────────┘
         │
         ▼ [EV Detection]
         
┌────────────────────────────────────────┐
│ all_ev_hits.csv                        │
│ (Opportunities with EV %)              │
└────────┬───────────────────────────────┘
         │
         ▼ [Backend API]
         
┌────────────────────────────────────────┐
│ backend_api.py                         │
├────────────────────────────────────────┤
│ GET /api/odds/raw                      │
│ GET /api/ev/hits                       │
│ GET /api/analytics/coverage            │
│ GET /api/advanced/all-markets          │
└────────┬───────────────────────────────┘
         │
         ▼ [Frontend - Existing + New]
         
┌────────────────────────────────────────┐
│ React Frontend                         │
├────────────────────────────────────────┤
│ Pages:                                 │
│  - RawOddsTable.js (existing)          │
│  - EVHits.js (existing)                │
│  - Dashboard.js (existing)             │
│                                        │
│ New Pages (Optional):                  │
│  - CoverageAnalytics.js                │
│  - AllMarkets.js                       │
│  - SharpConsensus.js                   │
└────────────────────────────────────────┘
```

**Key Differences:**
- ✅ More granular extraction (per-tier)
- ✅ Sport-specific fair odds applied
- ✅ Advanced data available for future analytics
- ✅ Backend APIs expand over time

**Questions for you:**
- ✅ Does this flow make sense?
- ❓ Should we store advanced markets separately or in main CSV?
- ❓ Should API split base/props or serve combined?

---

## 🐍 PART 4: File-by-File Review

### File 1: `src/v3/config.py`

**Current Status:**
```python
# 350 lines
# Everything in one place
SPORTS_CONFIG = { "basketball_nba": {...} }
BOOKMAKER_RATINGS = { "pinnacle": {...} }
SPORT_WEIGHT_PROFILES = { "basketball_nba": {...} }
EV_CONFIG = { "min_ev_percent": 2.0 }
```

**Proposed Changes:**

**Option A: Expand Single File**
- Add `fair_odds_config` per sport
- Add `region_config` per sport
- Add `api_tiers_config` per sport
- Result: ~800 lines (getting large)

**Option B: Split Into Modular Files**
```
src/v3/configs/
├── __init__.py
├── sports.py          ← All SPORTS_CONFIG
├── bookmakers.py      ← All BOOKMAKER_RATINGS
├── weights.py         ← All SPORT_WEIGHT_PROFILES
├── fair_odds.py       ← Fair odds configs per sport
├── regions.py         ← Region configs per sport
├── api_tiers.py       ← Tier extraction configs
└── ev_detection.py    ← EV thresholds
```

**Proposed Structure (Option B):**

```python
# src/v3/configs/fair_odds.py
FAIR_ODDS_CONFIGS = {
    "basketball_nba": {
        "outlier_threshold": 0.05,
        "min_sharp_count": 2,
        "weight_profile": {
            "sharps": ["pinnacle", "draftkings", "fanduel"],
            "weights": {"pinnacle": 0.50, "draftkings": 0.30, "fanduel": 0.20},
        },
        "special_rules": {
            "player_props": "ignore_au_books",
            "h2h": "all_books_ok",
        }
    },
    "americanfootball_nfl": {
        "outlier_threshold": 0.03,
        "min_sharp_count": 1,
        "weight_profile": {
            "sharps": ["pinnacle", "draftkings"],
            "weights": {"pinnacle": 0.60, "draftkings": 0.40},
        },
    }
}
```

```python
# src/v3/configs/regions.py
REGION_CONFIGS = {
    "basketball_nba": {
        "extract_from": ["au", "us", "eu"],
        "time_windows": {"au": 48, "us": 48, "eu": 72},
        "sharp_priority": ["us", "eu", "au"],
        "exclude_from_fair_odds": ["au"],  # AU is 1-star only
    },
    "cricket_big_bash": {
        "extract_from": ["au"],
        "sharp_priority": ["au"],
        "exclude_from_fair_odds": [],
    }
}
```

```python
# src/v3/configs/api_tiers.py
API_TIER_CONFIGS = {
    "basketball_nba": {
        "tier_1_base_markets": True,
        "tier_2_player_props": True,
        "tier_2_props_list": ["player_points", "player_rebounds", "player_assists"],
        "tier_3_advanced": False,
        "estimated_cost": 50,
    },
    "soccer_epl": {
        "tier_1_base_markets": True,
        "tier_2_player_props": False,
        "tier_3_advanced": True,  # Track 3-way markets
        "tier_3_advanced_markets": ["h2h_3way", "over_under_partials"],
        "estimated_cost": 40,
    }
}
```

**Impact on Code:**
```python
# Old: from src.v3.config import SPORTS_CONFIG
# New: from src.v3.configs import sports, fair_odds, regions, api_tiers
```

**Questions for you:**
- ✅ Prefer single expanded file or modular split?
- ❓ Any other configs you want separated?

---

### File 2: `src/v3/base_extractor.py`

**Current (480 lines):**
- Generic extraction logic
- CSV writing
- Data validation

**Proposed Changes:**

**Add methods for tiers:**
```python
class BaseExtractor(ABC):
    
    def fetch_odds(self):
        """Main method - calls tier methods"""
        markets = []
        
        # Tier 1: Base markets (always)
        if self.config["tier_1_base_markets"]:
            markets.extend(self._fetch_tier_1_base())
        
        # Tier 2: Player props (if enabled)
        if self.config["tier_2_player_props"]:
            markets.extend(self._fetch_tier_2_props())
        
        # Tier 3: Advanced (if enabled)
        if self.config["tier_3_advanced"]:
            markets.extend(self._fetch_tier_3_advanced())
        
        return markets
    
    def _fetch_tier_1_base(self):
        """Base markets: h2h, spreads, totals"""
        # Common for all sports
    
    def _fetch_tier_2_props(self):
        """Player props - override in subclass"""
        # Each sport customizes this
    
    def _fetch_tier_3_advanced(self):
        """Advanced markets - 3-way, partials, etc"""
        # Each sport customizes this
```

**Add region awareness:**
```python
def _get_regions(self):
    """Get regions for this sport"""
    from src.v3.configs import regions
    return regions.REGION_CONFIGS[self.SPORT_KEY]["extract_from"]

def _is_book_for_fair_odds(self, book):
    """Check if book should be used for fair odds"""
    from src.v3.configs import regions
    config = regions.REGION_CONFIGS[self.SPORT_KEY]
    book_region = self.BOOKMAKER_TO_REGION[book]
    return book_region not in config["exclude_from_fair_odds"]
```

**Impact:**
- ~100 more lines
- Better separation of concerns
- Each sport can override

**Questions for you:**
- ✅ Does tier-based approach work?
- ❓ Any methods you want added/removed?

---

### File 3: `src/v3/extractors/nba_extractor.py`

**Current (220 lines):**
```python
class NBAExtractor(BaseExtractor):
    SPORT_KEY = "basketball_nba"
    PLAYER_PROPS = ["player_points", "player_rebounds", ...]
```

**Proposed Changes:**

**Override tier methods:**
```python
class NBAExtractor(BaseExtractor):
    SPORT_KEY = "basketball_nba"
    
    def _fetch_tier_2_props(self):
        """NBA-specific: 5 major props only"""
        props = [
            "player_points",
            "player_rebounds",
            "player_assists",
        ]
        # Custom logic: per-event fetching for props
        # (expensive but necessary)
    
    def _fetch_tier_3_advanced(self):
        """Not needed for NBA"""
        return []
```

**Respect regions config:**
```python
def fetch_odds(self):
    from src.v3.configs import regions
    region_config = regions.REGION_CONFIGS[self.SPORT_KEY]
    self.REGIONS = region_config["extract_from"]
    # Now extracts only from configured regions
```

**Impact:**
- Clear, focused class
- Easy to customize
- Follows parent contract

**Questions for you:**
- ✅ Does this structure make sense?
- ❓ Any NBA-specific logic you want different?

---

### File 4: `src/v3/processors/fair_odds_v2.py`

**Current (380 lines):**
- Generic fair odds calculation
- Same logic for all sports

**Proposed Changes:**

**Refactor to base class:**
```
src/v3/processors/
├── fair_odds_base.py      ← Abstract base
├── fair_odds_nba.py       ← NBA implementation
├── fair_odds_nfl.py       ← NFL implementation
├── fair_odds_soccer.py    ← Soccer implementation
└── fair_odds_tennis.py    ← Tennis implementation
```

**Base class (150 lines):**
```python
class FairOddsBase(ABC):
    """Abstract - implement per sport"""
    
    @abstractmethod
    def calculate_fair_odds(self, market_data):
        pass
    
    @abstractmethod
    def get_sharp_books(self):
        pass
    
    def calculate_implied_probability(self, odds):
        """Common for all"""
        return 1.0 / odds if odds > 0 else 0.0
    
    def detect_arbitrage(self, over, under):
        """Common for all"""
        return (1.0/over + 1.0/under) < 1.0
```

**NBA Implementation (150 lines):**
```python
class NBAFairOdds(FairOddsBase):
    
    def get_sharp_books(self):
        """NBA sharps: Pinnacle, DK, FD"""
        from src.v3.configs import fair_odds
        config = fair_odds.FAIR_ODDS_CONFIGS["basketball_nba"]
        return config["weight_profile"]["sharps"]
    
    def calculate_fair_odds(self, market_data):
        """NBA-specific logic"""
        # Aggressive outlier removal for sparse props
        # Weight as configured
        # Respect region exclusions (no AU books)
```

**NFL Implementation (150 lines):**
```python
class NFLFairOdds(FairOddsBase):
    
    def get_sharp_books(self):
        """NFL sharps: Pinnacle, DK"""
        from src.v3.configs import fair_odds
        config = fair_odds.FAIR_ODDS_CONFIGS["americanfootball_nfl"]
        return config["weight_profile"]["sharps"]
    
    def calculate_fair_odds(self, market_data):
        """NFL-specific logic"""
        # Conservative outlier removal
        # Allow single sharp if coverage good
```

**Usage in Pipeline:**
```python
from src.v3.processors import fair_odds_nba, fair_odds_nfl

calculator = fair_odds_nba.NBAFairOdds()
fair_over, fair_under = calculator.calculate_fair_odds(market_data)
```

**Impact:**
- Flexible per-sport fair odds
- Clear implementation per sport
- Easy to test each sport

**Questions for you:**
- ✅ Does per-sport class approach work?
- ❓ What's the custom logic you want for each sport?

---

### File 5: `pipeline_v3.py`

**Current (280 lines):**
- Runs extractors
- Merges CSVs
- Prints summary

**Proposed Changes:**

**Add tier awareness:**
```python
def run_sport(self, sport_key: str, tiers: str = "1,2"):
    """
    Run extractor for sport
    
    Args:
        sport_key: "basketball_nba"
        tiers: "1" (base only), "1,2" (base+props), "1,2,3" (all)
    """
    # Enable/disable tiers dynamically
```

**Add dry-run mode:**
```bash
python pipeline_v3.py --sports basketball_nba --dry-run
# Output:
# Sport: NBA
# Regions: au,us,eu
# Tiers: 1,2 (base markets + props)
# Estimated cost: 50 credits
# Fair odds: Custom NBA logic
# Ready? (y/n)
```

**Better logging:**
```python
logger.info(f"[CONFIG] Sport: {sport}")
logger.info(f"[CONFIG] Regions: {regions}")
logger.info(f"[CONFIG] Fair odds: {fair_odds_class}")
logger.info(f"[CONFIG] Estimated cost: {cost}")
logger.info(f"[API] Fetching tier 1: base markets...")
logger.info(f"[API] Fetching tier 2: {props_count} props...")
```

**Merge with options:**
```bash
python pipeline_v3.py --merge-only
# Merges base + props (tier 1,2)

python pipeline_v3.py --merge-only --include-advanced
# Merges all tiers (1,2,3)
```

**Impact:**
- More transparency
- User can control tiers
- Dry-run before running

**Questions for you:**
- ✅ Does dry-run approach work?
- ❓ Want to control tiers per sport individually?

---

### File 6: `backend_api.py`

**Current Endpoints:**
```python
GET /api/odds/raw?limit=100     → Raw odds
GET /api/ev/hits?limit=50       → EV opportunities
GET /health                      → Health check
```

**Proposed Changes:**

**New endpoints (optional):**
```python
GET /api/analytics/coverage
# Returns: % events with 2+ sharp books per sport

GET /api/advanced/all-markets
# Returns: 3-way markets, advanced markets for analytics

GET /api/config
# Returns: Current configuration (transparent)
```

**Update existing endpoints:**
```python
GET /api/odds/raw?sport=basketball_nba&limit=100
# Now supports sport filtering

GET /api/ev/hits?sport=basketball_nba&min_ev=1.5
# Support custom EV threshold
```

**Impact on Frontend:**
- Can fetch sport-specific data
- Can filter by EV threshold
- Can show data quality metrics

**Questions for you:**
- ✅ Need new analytics endpoints?
- ❓ Any custom filtering needs?

---

## 🎨 PART 5: Frontend Impact Analysis

### Current Frontend Consumption

**RawOddsTable.js:**
```javascript
fetch('/api/odds/raw?limit=100')
  .then(data => {
    // Expects: 17 columns
    // Renders: Table with bookmakers
  })
```

**EVHits.js:**
```javascript
fetch('/api/ev/hits?limit=50')
  .then(data => {
    // Shows EV opportunities
    // Displays best book + odds
  })
```

**Dashboard.js:**
```javascript
fetch('/api/ev/summary')
  .then(data => {
    // Shows: total hits, avg EV, by sport
  })
```

### Proposed Frontend Additions

**New Column: Data Quality**
```javascript
// Add column showing if 2+ sharp books used
// Color green if good, yellow if marginal, red if poor
<span className={getQualityClass(sharpCount)}>
  {sharpCount} sharps
</span>
```

**New Filter: Show/Hide by Sport Fair Odds Type**
```javascript
// Dropdown: "Fair Odds Type"
// Options: NBA, NFL, Soccer, etc
// Shows which custom logic was used
```

**New Page: Analytics (Optional)**
```javascript
// GET /api/analytics/coverage
// Shows: % of events with good sharp coverage
// Chart: Coverage by sport and market
```

### NO Breaking Changes
- ✅ Existing endpoints remain same
- ✅ CSV format compatible
- ✅ Frontend doesn't need changes immediately
- ⚠️ Can add features over time

**Questions for you:**
- ✅ OK to keep backward compatible?
- ❓ Any frontend features you want NOW?

---

## 💾 PART 6: Storage Efficiency Analysis

### Current Storage

**Per Run:**
```
nba_raw.csv:      ~100 KB (87 markets)
nfl_raw.csv:      ~80 KB  (156 markets)
all_raw_odds.csv: ~180 KB (combined)
```

**Per Month (10 runs):**
```
Total: ~1.8 MB
```

### Proposed Storage (With Tiers)

**With Advanced Markets:**
```
nba_base_markets.csv:   ~80 KB
nba_player_props.csv:   ~40 KB
nba_advanced.csv:       ~30 KB (3-way markets, etc)
Total per NBA run:      ~150 KB

Per month (10 runs):    ~1.5 MB
```

**Archive Strategy:**
```
data/v3/
├── extracts/           ← Latest only (keep clean)
├── merged/             ← Latest merged CSV
└── archive/
    ├── 2025-12-20/     ← Daily backups
    ├── 2025-12-21/
    └── 2025-12-22/
```

### Database Alternative (If Added Later)

```sql
-- More efficient storage
-- Normalized: no duplicate event data
-- Per month: ~500 KB if using PostgreSQL

events table:        50 KB
markets table:       100 KB
odds table:          300 KB
ev_calculations:     150 KB
```

**Advantages:**
- ✅ Queryable by date, sport, book
- ✅ Time-series analysis easier
- ✅ Historical tracking
- ⚠️ Requires DB setup

**Questions for you:**
- ✅ Current CSV storage sufficient?
- ❓ Want to archive old data?
- ❓ Future database?

---

## ✅ APPROVAL CHECKLIST

Before I implement anything, please review and approve:

### Section 1: Fair Odds Customization
```
[ ] Yes, create per-sport FairOdds classes
[ ] No, keep generic for all sports
[ ] Modify: ________________
```

### Section 2: Regions Customization
```
[ ] Yes, use proposed region config structure
[ ] No, keep simple per-sport
[ ] Modify: ________________
```

### Section 3: API Tier Strategy
```
[ ] Yes, implement 3-tier approach (Base + Props + Advanced)
[ ] No, keep current approach
[ ] Modify: Only tier 1 & 2, skip advanced
[ ] Modify: ________________
```

### Section 4: Configuration Structure
```
[ ] Option A: Expand src/v3/config.py (single file)
[ ] Option B: Split into src/v3/configs/ (modular)
[ ] Option C: Hybrid approach
[ ] Modify: ________________
```

### Section 5: Dry-Run Mode
```
[ ] Yes, implement --dry-run flag
[ ] No, config-driven only
[ ] Modify: ________________
```

### Section 6: Backend API Updates
```
[ ] Add new analytics endpoints
[ ] Keep existing endpoints only
[ ] Modify: ________________
```

### Section 7: Frontend Changes
```
[ ] Add data quality column
[ ] Add fair odds type indicator
[ ] Add analytics page (later)
[ ] Keep exactly as is
[ ] Modify: ________________
```

---

## 🎯 NEXT STEPS

Once you approve above:

1. **Phase 1: Configuration** (1 hour)
   - Restructure config.py
   - Add per-sport fair odds config
   - Add regions config
   - Add API tiers config

2. **Phase 2: Extractors** (2 hours)
   - Update base_extractor.py with tier methods
   - Update NBA extractor
   - Update NFL extractor
   - Test tier functionality

3. **Phase 3: Fair Odds** (2 hours)
   - Create fair_odds_base.py
   - Implement NBA fair odds
   - Implement NFL fair odds
   - Implement Soccer fair odds

4. **Phase 4: Pipeline** (1 hour)
   - Add dry-run mode
   - Update orchestrator logging
   - Add tier controls

5. **Phase 5: Testing** (2 hours)
   - Test each sport extraction
   - Verify fair odds per sport
   - Check merged output
   - Validate frontend compatibility

6. **Phase 6: Documentation** (1 hour)
   - Update README
   - Add configuration guide
   - Add troubleshooting

---

## 📝 SUBMIT YOUR FEEDBACK

Please answer:

1. Fair Odds: Per-sport classes? (yes/no/modify)
2. Regions: Custom config? (yes/no/modify)
3. API Tiers: 3-tier approach? (yes/no/modify)
4. Config: Single file or modular? (A/B/C)
5. Dry-run: Yes or no?
6. Backend: New endpoints?
7. Frontend: Changes?
8. Anything else I missed?

Once approved, I'll show you code samples for each file before implementing.

---

**Status:** 🔴 AWAITING YOUR APPROVAL  
**Next:** Implement with 100% transparency
