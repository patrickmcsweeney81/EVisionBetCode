# EVisionBet v3 - Implementation Plan with Code Samples

**Status:** Ready for approval before implementation  
**Date:** December 26, 2025

---

## 📋 IMPLEMENTATION OVERVIEW

This document shows EXACT code samples for all layers before we build.

---

## 1️⃣ CONFIGURATION LAYER

### File Structure
```
src/v3/configs/
├── __init__.py
├── sports.py          ← Sports + API tiers + regions
├── bookmakers.py      ← Bookmaker ratings (stars)
├── weights.py         ← EVisionBet weight profiles
├── fair_odds.py       ← Fair odds logic per sport
└── api_tiers.py       ← Tier configurations
```

---

### `src/v3/configs/sports.py` (Master Config)

```python
"""
Master sports configuration.
All sports defined here with:
- API tier settings (base markets, props, advanced)
- Regions to extract
- Fair odds strategy
- Enable/disable flag
"""

SPORTS_CONFIG = {
    # ============ BASKETBALL ============
    "basketball_nba": {
        "enabled": True,
        "title": "NBA",
        "group": "Basketball",
        
        # API TIER STRATEGY
        "api_tiers": {
            "fetch_base_markets": True,      # h2h, spreads, totals
            "fetch_player_props": True,
            "player_props_list": [
                "player_points",
                "player_rebounds",
                "player_assists",
            ],
            "fetch_advanced_markets": False,
        },
        
        # REGIONS
        "regions": ["au", "us", "us2", "eu"],
        "time_window_hours": 48,
        
        # FAIR ODDS (custom per sport)
        "fair_odds_class": "NBAFairOdds",
        "fair_odds_config": {
            "outlier_threshold": 0.05,  # Aggressive (sparse props)
            "min_sharp_count": 2,
            "weight_sharps": True,      # Use weight profile
        },
        
        # EVisionBet Hidden Weights (0-4 stars)
        "evisionbet_weights": {
            "pinnacle": 4,
            "draftkings": 3,
            "fanduel": 3,
            "betfair": 2,
            # ... other books at 0-4
        },
    },
    
    # ============ AMERICAN FOOTBALL ============
    "americanfootball_nfl": {
        "enabled": True,
        "title": "NFL",
        "group": "American Football",
        
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": True,
            "player_props_list": [
                "player_pass_yds",
                "player_rush_yds",
                "player_pass_tds",
            ],
            "fetch_advanced_markets": False,
        },
        
        "regions": ["us", "us2", "au"],
        "time_window_hours": 168,  # Weekly
        
        "fair_odds_class": "NFLFairOdds",
        "fair_odds_config": {
            "outlier_threshold": 0.03,  # Conservative
            "min_sharp_count": 1,
            "weight_sharps": True,
        },
        
        "evisionbet_weights": {
            "pinnacle": 4,
            "draftkings": 4,
            "fanduel": 3,
            # ...
        },
    },
    
    # ============ SOCCER ============
    "soccer_epl": {
        "enabled": False,  # Will enable after testing
        "title": "EPL",
        "group": "Soccer",
        
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": False,  # Props sparse
            "fetch_advanced_markets": True,  # Track 3-way markets
        },
        
        "regions": ["eu", "au", "us"],
        "time_window_hours": 72,
        
        "fair_odds_class": "SoccerFairOdds",
        "fair_odds_config": {
            "outlier_threshold": 0.04,
            "min_sharp_count": 1,
        },
        
        "evisionbet_weights": {
            "pinnacle": 4,
            "betfair": 3,
            # ...
        },
    },
    
    # ... add all 12 sports here
}

# ============ SHORTCUTS ============
ENABLED_SPORTS = {
    key: config 
    for key, config in SPORTS_CONFIG.items() 
    if config.get("enabled", True)
}
```

---

### `src/v3/configs/bookmakers.py`

```python
"""
Master bookmaker list with 0-4 star ratings.
These are DEFAULT ratings used for fair odds.
Users can override weights 0-4 in frontend.
"""

BOOKMAKER_RATINGS = {
    # SHARPS (3-4 stars) - Used for fair odds calculation
    "pinnacle": {"stars": 4, "category": "sharp", "region": "int"},
    "betfair": {"stars": 4, "category": "sharp", "region": "eu"},
    "betfairaus": {"stars": 4, "category": "sharp", "region": "au"},
    "draftkings": {"stars": 3, "category": "sharp", "region": "us"},
    "fanduel": {"stars": 3, "category": "sharp", "region": "us"},
    
    # TARGETS (1-2 stars) - For EV detection
    "sportsbet": {"stars": 2, "category": "target", "region": "au"},
    "pointsbetus": {"stars": 2, "category": "target", "region": "us"},
    "betmgm": {"stars": 1, "category": "target", "region": "us"},
    "caesars": {"stars": 1, "category": "target", "region": "us"},
    # ... 20+ more books
}

def get_sharp_books():
    """Get all books rated 3-4 stars"""
    return {
        k: v for k, v in BOOKMAKER_RATINGS.items() 
        if v["stars"] >= 3
    }

def get_books_by_region(region):
    """Get books available in region"""
    return {
        k: v for k, v in BOOKMAKER_RATINGS.items() 
        if v["region"] in ["int", region]
    }
```

---

### `src/v3/configs/weights.py`

```python
"""
EVisionBet weight profiles per sport.
These are HIDDEN from users.
Users see all books starting at weight 0.
"""

SPORT_WEIGHT_PROFILES = {
    "basketball_nba": {
        "pinnacle": 0.50,
        "draftkings": 0.30,
        "fanduel": 0.20,
    },
    "americanfootball_nfl": {
        "pinnacle": 0.60,
        "draftkings": 0.40,
    },
    "soccer_epl": {
        "pinnacle": 0.70,
        "betfair": 0.30,
    },
    # ... per sport
}
```

---

## 2️⃣ BACKEND LAYER

### Data Flow

```
Step 1: Extract (per sport)
  API → nba_base_markets.csv + nba_props.csv → all_raw_odds.csv

Step 2: Enrich & Calculate
  all_raw_odds.csv → Add fair odds (using EVisionBet weights)
                  → Add EV% calculation
                  → Save as all_ev_hits.csv

Step 3: Derive Secondary CSVs
  all_raw_odds.csv → outliers.csv (for future analytics)
  all_ev_hits.csv  → arbs.csv (arbitrage opportunities)
  all_raw_odds.csv → pattys_picks.csv (custom criteria)
```

---

### Backend API Endpoints

**Endpoint 1: Raw Odds (Admin Only)**
```python
@app.get("/api/admin/odds/raw")
def get_raw_odds(sport: str = None, limit: int = 1000):
    """
    Returns ALL odds (every market, every book)
    Admin page uses this
    
    Query: /api/admin/odds/raw?sport=basketball_nba
    """
    df = pd.read_csv("data/v3/merged/all_raw_odds.csv")
    if sport:
        df = df[df["sport"] == sport]
    return df.head(limit).to_dict("records")
```

**Endpoint 2: EV Hits with Initial Calculation**
```python
@app.get("/api/ev/hits")
def get_ev_hits(sport: str = None, min_ev: float = 2.0, limit: int = 50):
    """
    Returns 2-way markets with EV% calculated using EVisionBet weights
    Frontend main page uses this
    
    Query: /api/ev/hits?sport=basketball_nba&min_ev=1.5
    """
    df = pd.read_csv("data/v3/merged/all_ev_hits.csv")
    
    if sport:
        df = df[df["sport"] == sport]
    
    df = df[df["ev_percent"] >= min_ev]
    
    return df.head(limit).to_dict("records")
```

**Endpoint 3: Config (For Frontend Recalculation)**
```python
@app.get("/api/config/weights")
def get_weight_config(sport: str = None):
    """
    Returns EVisionBet weight config per sport
    Frontend uses this to recalculate when user adjusts weights
    
    Example response:
    {
        "basketball_nba": {
            "pinnacle": 4,      ← Your hidden weight (0-4)
            "draftkings": 3,
            "fanduel": 3,
            ...
        }
    }
    """
    from src.v3.configs.sports import SPORTS_CONFIG
    
    result = {}
    for sport_key, config in SPORTS_CONFIG.items():
        if sport and sport_key != sport:
            continue
        result[sport_key] = config.get("evisionbet_weights", {})
    
    return result
```

**Endpoint 4: Weight Ranges (For Frontend UI)**
```python
@app.get("/api/config/bookmakers")
def get_bookmakers():
    """
    Returns all bookmakers for frontend weight sliders
    
    Example response:
    {
        "pinnacle": {"stars": 4, "region": "int"},
        "draftkings": {"stars": 3, "region": "us"},
        ...
    }
    """
    from src.v3.configs.bookmakers import BOOKMAKER_RATINGS
    return BOOKMAKER_RATINGS
```

---

## 3️⃣ FRONTEND LAYER

### Data Structure (What Frontend Receives)

**From `/api/ev/hits`:**
```json
{
    "extracted_at": "2025-12-26T10:30:00Z",
    "sport": "basketball_nba",
    "league": "NBA",
    "event_id": "event_123",
    "event_name": "Lakers vs Warriors",
    "commence_time": "2025-12-26T23:00:00Z",
    "market_type": "h2h",
    "point": null,
    "selection": "Lakers",
    "player_name": null,
    "bookmaker": "pointsbetus",
    "stars_rating": 2,
    "odds_decimal": 2.15,
    "implied_prob": 0.465,
    "is_sharp": false,
    "is_target": true,
    "fair_odds_decimal": 1.95,      // ← From EVisionBet weights
    "ev_percent": 2.3,              // ← EV using your weights
    "notes": "Target book with positive EV"
}
```

---

### Frontend EV Hits Card

```javascript
// EVHitsCard.js

const EVHitsCard = () => {
  const [rawOdds, setRawOdds] = useState([]);
  const [evHits, setEvHits] = useState([]);
  const [weights, setWeights] = useState({});      // User-adjusted weights
  const [bookmakers, setBookmakers] = useState({}); // Book info
  
  // Load initial data
  useEffect(() => {
    fetchEVHits();      // Your calculated EV (hidden weights)
    fetchWeights();     // Your EVisionBet weights
    fetchRawOdds();     // For recalculation
    fetchBookmakers();  // For UI
  }, []);
  
  const fetchEVHits = async () => {
    const res = await fetch("/api/ev/hits?sport=basketball_nba");
    setEvHits(await res.json());
  };
  
  const fetchWeights = async () => {
    const res = await fetch("/api/config/weights");
    const config = await res.json();
    // Show all books at 0 weight (hidden from user)
    const userWeights = {};
    Object.keys(config["basketball_nba"]).forEach(book => {
      userWeights[book] = 0;  // ← User sees 0, doesn't see your weight
    });
    setWeights(userWeights);
  };
  
  const fetchRawOdds = async () => {
    const res = await fetch("/api/admin/odds/raw?sport=basketball_nba");
    setRawOdds(await res.json());
  };
  
  const fetchBookmakers = async () => {
    const res = await fetch("/api/config/bookmakers");
    setBookmakers(await res.json());
  };
  
  // When user adjusts weight slider
  const handleWeightChange = (bookmaker, newWeight) => {
    const updatedWeights = { ...weights, [bookmaker]: newWeight };
    setWeights(updatedWeights);
    
    // Recalculate EV with new weights
    const recalculatedEV = recalculateFairOdds(rawOdds, updatedWeights);
    setEvHits(recalculatedEV);
  };
  
  // Frontend calculation (same logic as backend fair_odds.py)
  const recalculateFairOdds = (odds, userWeights) => {
    // Use rawOdds + userWeights to recalculate EV
    // Only include books with weight > 0
    // Same formula as backend
    
    return odds.map(market => {
      // Recalc fair odds using userWeights
      const fairOdds = calculateFairPrice(market, userWeights);
      const ev = ((fairOdds * market.odds_decimal) - 1) * 100;
      
      return { ...market, ev_percent: ev, fair_odds_decimal: fairOdds };
    });
  };
  
  return (
    <div className="ev-hits-card">
      <h2>EV Opportunities</h2>
      
      {/* Weight Sliders */}
      <div className="weight-controls">
        <h3>Adjust Book Weights (0-4)</h3>
        {Object.entries(bookmakers).map(([book, info]) => (
          <div key={book} className="weight-slider">
            <label>{book} ({info.stars}★)</label>
            <input
              type="range"
              min="0"
              max="4"
              value={weights[book] || 0}
              onChange={(e) => handleWeightChange(book, parseInt(e.target.value))}
            />
            <span>{weights[book]}</span>
          </div>
        ))}
      </div>
      
      {/* EV Table */}
      <table>
        <thead>
          <tr>
            <th>Event</th>
            <th>Market</th>
            <th>Selection</th>
            <th>Best Book</th>
            <th>Odds</th>
            <th>Fair Price</th>
            <th>EV %</th>
          </tr>
        </thead>
        <tbody>
          {evHits.map((hit, idx) => (
            <tr key={idx}>
              <td>{hit.event_name}</td>
              <td>{hit.market_type}</td>
              <td>{hit.selection}</td>
              <td>{hit.bookmaker} ({hit.stars_rating}★)</td>
              <td>{hit.odds_decimal.toFixed(2)}</td>
              <td>{hit.fair_odds_decimal.toFixed(2)}</td>
              <td style={{ color: hit.ev_percent > 0 ? "green" : "red" }}>
                {hit.ev_percent.toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## 4️⃣ DATA DERIVATION STRATEGY

### Pipeline Execution

```python
# pipeline_v3.py

def run_full_pipeline(sports=None, command_line_override=None):
    """
    Step 1: Extract (from API)
    Step 2: Merge raw odds
    Step 3: Calculate EVisionBet EV hits
    Step 4: Derive secondary CSVs
    """
    
    # Step 1: EXTRACT
    if command_line_override:
        sports_to_run = command_line_override
    else:
        sports_to_run = get_enabled_sports()
    
    for sport_key in sports_to_run:
        extract_sport(sport_key)
    
    # Step 2: MERGE
    merge_all_raw_odds()  # Combine all sport CSVs → all_raw_odds.csv
    
    # Step 3: CALCULATE EV with EVisionBet WEIGHTS
    calculate_ev_hits()   # Read all_raw_odds.csv, add fair odds + EV → all_ev_hits.csv
    
    # Step 4: DERIVE SECONDARY
    derive_outliers()     # From all_raw_odds.csv
    derive_arbitrage()    # From all_ev_hits.csv
    # ... more derivations as needed
```

**Auto-Derivation:** All CSVs auto-derive from all_raw_odds.csv in one pipeline run.

---

## 5️⃣ WEIGHT SYSTEM SUMMARY

| Layer | What | Value | Who Sees |
|-------|------|-------|----------|
| **Backend Config** | EVisionBet weights per book | 0-4 stars | Only backend (hidden) |
| **Backend API** | Returns config weights | 0-4 stars | Frontend (for reference) |
| **Frontend Display** | User weight sliders | 0-4 range | Users (starts at 0) |
| **Frontend Calc** | User-adjusted weights | 0-4 values | Used for recalculation |
| **EV Hits** | Pre-calculated EV% | % | Users (from EVisionBet weights) |

---

## ✅ READY TO BUILD?

**All code samples above show EXACT structure.**

Shall I now:

1. **Create all config files** with full sports examples
2. **Create backend API endpoints** with EV calculation
3. **Create frontend components** with weight sliders
4. **Create pipeline** with step-by-step execution

Or **any changes needed first?**

