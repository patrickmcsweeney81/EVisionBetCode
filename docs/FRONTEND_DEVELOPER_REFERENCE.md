# Frontend Developer: Phase 5 API Reference

## Data Structures for React Components

### 1. Weight Configuration (From `/api/config/weights`)

**TypeScript Interface:**
```typescript
interface WeightConfig {
  sports: {
    [sportKey: string]: {
      weights: {
        [bookmaker: string]: number;
      };
      title: string;
    };
  };
  timestamp: string;
  note: string;
}

// Example for NBA
interface NBAWeightConfig {
  weights: {
    pinnacle: number;      // 4 (highest trust)
    betfair: number;       // 3
    draftkings: number;    // 3
    fanduel: number;       // 3
    betfairaus: number;    // 2
    sportsbet: number;     // 1 (lowest trust)
  };
}
```

**Real Response:**
```json
{
  "sports": {
    "basketball_nba": {
      "weights": {
        "pinnacle": 4,
        "betfair": 3,
        "draftkings": 3,
        "fanduel": 3,
        "betfairaus": 2,
        "sportsbet": 1
      },
      "title": "NBA"
    }
  },
  "timestamp": "2025-12-26T10:30:00.000000",
  "note": "These are EVisionBet's hidden weights..."
}
```

### 2. EV Hits (From `/api/ev/hits`)

**TypeScript Interface:**
```typescript
interface EVHit {
  sport: string;                   // "NBA", "NFL", etc.
  event_id: string | null;         // Odds API event ID
  away_team: string | null;        // "San Antonio Spurs"
  home_team: string | null;        // "New York Knicks"
  commence_time: string | null;    // "01:40 17/12/25"
  market: string | null;           // "Rebounds", "Player Points", etc.
  point: number | null;            // 4.5 (line for Over/Under)
  selection: string | null;        // "Julian Champagnie Under"
  player: string | null;           // Player name or null
  fair_odds: number;               // 1.7693 (backend pre-calculated)
  best_book: string;               // "Unibet_AU"
  best_odds: number;               // 1.97
  ev_percent: number;              // 0.1134 (11.34% EV)
  sharp_book_count: number;        // 4 (number of sharp books used)
  implied_prob: number;            // 0.5652 (56.52%)
  stake: number;                   // 100.0 (default stake)
  kelly_fraction: number | null;   // Kelly fraction
  detected_at: string | null;      // Timestamp
  created_at: string | null;       // Timestamp
  bookmaker: string;               // Alias for best_book
  odds_decimal: number;            // Alias for best_odds
}

interface EVHitsResponse {
  hits: EVHit[];
  count: number;                   // Length of returned hits
  total_count: number;             // Total available
  last_updated: string;            // ISO timestamp
  filters: {
    limit: number;
    offset: number;
    min_ev: number;
    sport: string | null;
  };
  warning?: string;                // Optional error message
}
```

**Real Response (Sample):**
```json
{
  "hits": [
    {
      "sport": "NBA",
      "event_id": null,
      "away_team": "San Antonio Spurs",
      "home_team": "New York Knicks",
      "commence_time": "01:40 17/12/25",
      "market": "Rebounds",
      "point": 4.5,
      "selection": "Julian Champagnie Under",
      "player": null,
      "fair_odds": 1.7693,
      "best_book": "Unibet_AU",
      "best_odds": 1.97,
      "ev_percent": 0.1134,
      "sharp_book_count": 4,
      "implied_prob": 0.5652,
      "stake": 100.0,
      "kelly_fraction": null,
      "detected_at": null,
      "created_at": null,
      "bookmaker": "Unibet_AU",
      "odds_decimal": 1.97
    }
  ],
  "count": 1,
  "total_count": 106,
  "last_updated": "2025-12-25T23:40:30.392434",
  "filters": {
    "limit": 10,
    "offset": 0,
    "min_ev": 0.01,
    "sport": null
  }
}
```

### 3. Raw Odds (From `/api/odds/raw`)

**TypeScript Interface:**
```typescript
interface RawOdds {
  sport: string;
  event_id: string;
  commence_time: string;
  market: string;
  point: number | null;
  selection: string;
  bookmaker: string;
  odds: number;
  extracted_at: string;
  created_at: string;
}
```

## Frontend Implementation Examples

### Load Weights on App Startup

```typescript
// useEffect hook in main App component
useEffect(() => {
  const loadWeights = async () => {
    try {
      const response = await fetch(`${API_URL}/api/config/weights`);
      const config = await response.json();
      
      // Store all sport weights
      const bookmakers = {};
      Object.entries(config.sports).forEach(([sportKey, sportData]) => {
        bookmakers[sportKey] = Object.keys(sportData.weights);
      });
      
      setBookmakers(bookmakers);
      setWeightConfig(config);
    } catch (error) {
      console.error('Failed to load weight config:', error);
      // Fallback: use default bookmakers
    }
  };
  
  loadWeights();
}, []);
```

### Initialize User Weights (All Zeros)

```typescript
const [userWeights, setUserWeights] = useState({});

useEffect(() => {
  if (bookmakers) {
    // Initialize all weights to 0 (no adjustment)
    const initialWeights = {};
    Object.keys(bookmakers).forEach(sport => {
      initialWeights[sport] = {};
      bookmakers[sport].forEach(book => {
        initialWeights[sport][book] = 0;
      });
    });
    setUserWeights(initialWeights);
  }
}, [bookmakers]);
```

### Weight Slider Component

```typescript
const WeightSlider: React.FC<{
  bookmaker: string;
  value: number;
  onChange: (newValue: number) => void;
  sport: string;
}> = ({ bookmaker, value, onChange, sport }) => {
  const handleChange = (newVal: number) => {
    onChange(newVal);
    // Trigger recalculation in parent
  };
  
  return (
    <div className="weight-slider">
      <label>{bookmaker}</label>
      <input
        type="range"
        min="0"
        max="4"
        value={value}
        onChange={(e) => handleChange(Number(e.target.value))}
        step="0.5"
      />
      <span className="value">{value}</span>
      <span className="hint">
        {value === 0 ? 'Not used' :
         value <= 1 ? 'Low trust' :
         value <= 2 ? 'Medium' :
         value <= 3 ? 'High trust' :
         'Highest trust'}
      </span>
    </div>
  );
};
```

### Fair Odds Calculation Function

```typescript
interface BookOdds {
  bookmaker: string;
  odds: number;
  is_sharp: boolean;
  is_outlier?: boolean;
}

function calculateWeightedFairOdds(
  odds: BookOdds[],
  weights: { [book: string]: number },
  outlierThreshold: number = 0.05
): number {
  // 1. Filter to sharp books only (3-4 stars)
  const sharpOdds = odds.filter(o => o.is_sharp);
  if (sharpOdds.length === 0) return 0;
  
  // 2. Remove outliers (use sorted approach)
  const sorted = sharpOdds
    .map(o => o.odds)
    .sort((a, b) => a - b);
  
  const count = sorted.length;
  const removeCount = Math.ceil(count * outlierThreshold);
  const filtered = sorted.slice(removeCount, count - removeCount);
  
  if (filtered.length === 0) return 0;
  
  // 3. Weight by normalized user weights
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  
  if (totalWeight === 0) {
    // Fallback: equal weight
    return filtered.reduce((a, b) => a + b) / filtered.length;
  }
  
  const normalizedWeights = Object.fromEntries(
    Object.entries(weights).map(([book, w]) => [
      book,
      w / totalWeight
    ])
  );
  
  // 4. Calculate weighted average
  let weightedSum = 0;
  let weightSum = 0;
  
  filtered.forEach(oddVal => {
    // Find which book this odd came from
    const book = sharpOdds.find(o => o.odds === oddVal)?.bookmaker;
    if (book && normalizedWeights[book]) {
      weightedSum += oddVal * normalizedWeights[book];
      weightSum += normalizedWeights[book];
    }
  });
  
  return weightSum > 0 ? weightedSum / weightSum : 0;
}
```

### EV Recalculation on Weight Change

```typescript
const recalculateEV = (
  fairOdds: number,
  bestOdds: number,
  userWeights: { [book: string]: number }
) => {
  // Calculate new fair odds with user weights
  const newFairOdds = calculateWeightedFairOdds(
    rawOdds,
    userWeights,
    outlierThreshold
  );
  
  // Calculate EV percentage
  const ev = ((newFairOdds * bestOdds) - 1) * 100;
  
  return {
    fairOdds: newFairOdds,
    ev: ev,
    evPercent: ev.toFixed(2),
    comparison: {
      backend: backendEV,
      userRecalc: ev,
      difference: (ev - backendEV).toFixed(2)
    }
  };
};
```

### Display EV Hit with Comparison

```typescript
const EVHitCard: React.FC<{ hit: EVHit }> = ({ hit }) => {
  const [userWeights, setUserWeights] = useState({});
  const [recalc, setRecalc] = useState({
    fairOdds: hit.fair_odds,
    ev: hit.ev_percent,
  });
  
  const handleWeightChange = (book: string, newValue: number) => {
    const updated = { ...userWeights, [book]: newValue };
    setUserWeights(updated);
    
    const newCalc = recalculateEV(
      hit.fair_odds,
      hit.best_odds,
      updated
    );
    setRecalc(newCalc);
  };
  
  return (
    <div className="ev-hit-card">
      <h3>{hit.selection}</h3>
      <p>{hit.home_team} vs {hit.away_team}</p>
      
      {/* Backend pre-calculated */}
      <div className="backend-ev">
        <h4>Backend (EVisionBet Weights)</h4>
        <p>Fair Odds: {hit.fair_odds.toFixed(4)}</p>
        <p>EV: {(hit.ev_percent * 100).toFixed(2)}%</p>
      </div>
      
      {/* User weight sliders */}
      <div className="weight-sliders">
        <h4>Your Weights (Adjust to Recalculate)</h4>
        {bookmakers.map(book => (
          <WeightSlider
            key={book}
            bookmaker={book}
            value={userWeights[book] || 0}
            onChange={(val) => handleWeightChange(book, val)}
            sport={hit.sport}
          />
        ))}
      </div>
      
      {/* User recalculated */}
      <div className="user-ev">
        <h4>Your EV (Recalculated)</h4>
        <p>Fair Odds: {recalc.fairOdds?.toFixed(4) || 'N/A'}</p>
        <p>EV: {recalc.ev?.toFixed(2) || 'N/A'}%</p>
        {recalc.comparison && (
          <p className="difference">
            Difference: {recalc.comparison.difference}%
          </p>
        )}
      </div>
      
      {/* Action */}
      <button className={recalc.ev > hit.ev_percent ? 'good' : 'neutral'}>
        Place Bet
      </button>
    </div>
  );
};
```

## API Call Examples (React)

### Fetch EV Hits

```typescript
const fetchEVHits = async (
  sport?: string,
  limit: number = 50,
  minEV: number = 0.01
) => {
  const params = new URLSearchParams({
    limit: limit.toString(),
    min_ev: minEV.toString(),
    ...(sport && { sport })
  });
  
  const response = await fetch(
    `${API_URL}/api/ev/hits?${params}`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to fetch EV hits: ${response.status}`);
  }
  
  const data: EVHitsResponse = await response.json();
  return data;
};

// Usage
useEffect(() => {
  fetchEVHits('basketball_nba', 50, 0.01)
    .then(data => {
      setHits(data.hits);
      setTotal(data.total_count);
    })
    .catch(err => console.error(err));
}, []);
```

### Fetch Raw Odds

```typescript
const fetchRawOdds = async (sport: string) => {
  const response = await fetch(
    `${API_URL}/api/odds/raw?sport=${sport}&limit=500`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to fetch raw odds: ${response.status}`);
  }
  
  return response.json();
};
```

## Testing in Browser Console

```javascript
// Load weights
fetch('http://localhost:8000/api/config/weights')
  .then(r => r.json())
  .then(data => console.log('Weights:', data.sports))

// Load EV hits
fetch('http://localhost:8000/api/ev/hits?limit=5')
  .then(r => r.json())
  .then(data => console.log('EV Hits:', data.hits))

// Load raw odds
fetch('http://localhost:8000/api/odds/raw?limit=10')
  .then(r => r.json())
  .then(data => console.log('Raw Odds:', data))
```

## Summary

Frontend now has:
- ✅ Weight config endpoint (`/api/config/weights`)
- ✅ EV hits endpoint (`/api/ev/hits`) with all needed fields
- ✅ Raw odds endpoint (`/api/odds/raw`) for recalculation
- ✅ Data structures documented with examples
- ✅ Implementation examples in React
- ✅ Fair odds calculation function

Ready to build: React components with weight sliders and instant EV recalculation!
