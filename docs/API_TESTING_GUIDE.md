# API Testing Guide - Phase 5

## Quick Start

Backend API is running at: **http://localhost:8000**

## Test Commands

### 1. Check API Health
```bash
curl http://localhost:8000/health
```

### 2. List All Endpoints
```bash
curl http://localhost:8000/
```

### 3. Get Weight Configuration (NEW!)
```bash
curl http://localhost:8000/api/config/weights
```

**Response (Example):**
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
    },
    "americanfootball_nfl": {
      "weights": {
        "pinnacle": 4,
        "draftkings": 4,
        "fanduel": 3,
        "betfair": 2
      },
      "title": "NFL"
    }
  },
  "timestamp": "2025-12-26T10:30:00.000000",
  "note": "These are EVisionBet's hidden weights..."
}
```

### 4. Get EV Opportunities
```bash
# Basic - top 10 opportunities
curl 'http://localhost:8000/api/ev/hits?limit=10'

# With sport filter
curl 'http://localhost:8000/api/ev/hits?limit=10&sport=basketball_nba'

# With EV threshold (1% minimum)
curl 'http://localhost:8000/api/ev/hits?limit=10&min_ev=0.01'

# With pagination
curl 'http://localhost:8000/api/ev/hits?limit=50&offset=0'
```

**Response (Example - Truncated):**
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

### 5. Get Raw Odds (All Books)
```bash
curl 'http://localhost:8000/api/odds/raw?limit=20&sport=basketball_nba'
```

## PowerShell Testing

### Test Config Weights
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/config/weights" -UseBasicParsing
$json = $response.Content | ConvertFrom-Json
$json.sports | ConvertTo-Json
```

### Test EV Hits with Filters
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/ev/hits?limit=5&min_ev=0.05" -UseBasicParsing
$data = $response.Content | ConvertFrom-Json
$data.hits | Select-Object sport, selection, best_odds, ev_percent | ConvertTo-Json
```

## Frontend Integration Examples

### Load Weights on Startup (JavaScript)
```javascript
async function loadWeights() {
  const response = await fetch('http://localhost:8000/api/config/weights');
  const config = await response.json();
  
  const nbaWeights = config.sports.basketball_nba.weights;
  console.log('NBA bookmakers:', Object.keys(nbaWeights));
  // Output: ['pinnacle', 'betfair', 'draftkings', 'fanduel', 'betfairaus', 'sportsbet']
  
  return nbaWeights;
}
```

### Load EV Hits (JavaScript)
```javascript
async function loadEVHits(sport, limit = 50) {
  const query = new URLSearchParams({
    limit,
    sport,
    min_ev: 0.01
  });
  
  const response = await fetch(`http://localhost:8000/api/ev/hits?${query}`);
  const data = await response.json();
  
  console.log(`Found ${data.count} EV opportunities`);
  console.log(`Total available: ${data.total_count}`);
  
  return data.hits;
}
```

### Recalculate EV with Custom Weights (JavaScript)
```javascript
function calculateFairOdds(odds, weights) {
  // Filter to sharp books (3-4 stars)
  // Remove outliers
  // Weight by normalized weights
  // Return weighted average decimal odds
  
  const validOdds = odds.filter(o => o.is_sharp);
  const weighted = validOdds.reduce((sum, o) => {
    return sum + (o.odds * weights[o.bookmaker]);
  }, 0);
  
  return weighted / Object.values(weights).reduce((a, b) => a + b);
}

function calculateEV(fairOdds, bestOdds) {
  return ((fairOdds * bestOdds) - 1) * 100;
}
```

## Common Use Cases

### 1. Display All Available Weights
```bash
curl http://localhost:8000/api/config/weights | jq '.sports | keys'
```

### 2. Get All NBA Opportunities
```bash
curl 'http://localhost:8000/api/ev/hits?sport=basketball_nba&limit=100' | jq '.hits | length'
```

### 3. Top 5 EV Opportunities Across All Sports
```bash
curl 'http://localhost:8000/api/ev/hits?limit=5' | jq '.hits[] | {selection, best_odds, ev_percent}'
```

### 4. EV Opportunities Above 10%
```bash
curl 'http://localhost:8000/api/ev/hits?limit=50&min_ev=0.10' | jq '.hits | length'
```

### 5. NFL Only, High EV
```bash
curl 'http://localhost:8000/api/ev/hits?sport=americanfootball_nfl&min_ev=0.05&limit=20'
```

## Headers & Auth

### Public Endpoints (No Auth Required)
- GET `/api/config/weights` ✅ Public
- GET `/api/ev/hits` ✅ Public
- GET `/api/odds/raw` ✅ Public (limited)
- GET `/api/ev/summary` ✅ Public
- GET `/api/odds/latest` ✅ Public
- GET `/health` ✅ Public
- GET `/` ✅ Public

### Admin Endpoints (Require Auth)
```bash
# Get auth token
curl -X POST 'http://localhost:8000/api/admin/auth?password=YOUR_PASSWORD'
# Returns: { "access_token": "...", "token_type": "bearer" }

# Use token for admin CSV exports
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/admin/ev-opportunities-csv
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/admin/raw-odds-csv
```

## Troubleshooting

### Config Weights Returns Error
- Check that `src/v3/configs/` directory exists
- Verify `sports.py` has `get_enabled_sports()` function
- Check `PYTHONPATH` includes EVisionBetCode root

### EV Hits Returns Empty
- Check `data/ev_hits.csv` exists and has data
- Run pipeline: `python src/pipeline_v2/calculate_opportunities.py`
- Or check backend logs for CSV read errors

### API Won't Start
- Check port 8000 is available: `netstat -ano | findstr :8000`
- Check `.env` file has `ODDS_API_KEY` (optional for CSV mode)
- Check all imports work: `python -c "from src.v3.configs import get_sport_config"`

## Performance Notes

- **Config Weights**: Instant (~10ms) - loads from memory
- **EV Hits (10 items)**: ~50ms - reads from CSV or DB
- **EV Hits (1000 items)**: ~500ms - full CSV scan
- **Raw Odds**: ~100-200ms - large dataset

For production, consider:
- Caching config in memory (already cached on startup)
- Pagination for large result sets (limit/offset)
- Database instead of CSV for faster queries
