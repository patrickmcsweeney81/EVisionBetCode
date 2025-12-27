# Backend API v3 - Config-Driven Architecture

## Overview
The backend API now supports the v3 architecture with hidden EVisionBet weights and user-adjustable weight sliders on the frontend.

## New Endpoints

### GET `/api/config/weights`

Returns EVisionBet's weight configuration for all enabled sports and bookmakers.

**Response Example:**
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
  "timestamp": "2025-12-26T10:30:00",
  "note": "These are EVisionBet's hidden weights. Frontend users start at 0 for all books and adjust via sliders."
}
```

**Purpose:**
- Frontend loads this config on startup
- Shows users all bookmakers available for this sport
- Weights shown here are EVisionBet's internal logic (for transparency/debugging only)
- Users never see these weights in normal UI - they start at 0 and adjust

### Existing Endpoints (Enhanced)

#### GET `/api/ev/hits`
- Returns EV opportunities pre-calculated with EVisionBet's hidden weights
- Fair odds already calculated using backend's weight profile
- Frontend receives `fair_odds` and `best_odds` to display

#### GET `/api/odds/raw`
- Returns raw odds from all bookmakers
- Frontend can use this to recalculate fair odds with custom weights if needed

## Frontend Weight Adjustment Flow

### Step 1: Load Config
```javascript
const config = await fetch('/api/config/weights').then(r => r.json());
// config.sports.basketball_nba.weights = { pinnacle: 0.50, draftkings: 0.30, fanduel: 0.20 }
```

### Step 2: Initialize Sliders
```javascript
// Frontend creates sliders for each bookmaker
// Each slider starts at weight = 0
const userWeights = {
  pinnacle: 0,      // User hasn't adjusted yet
  draftkings: 0,
  fanduel: 0
};
```

### Step 3: User Adjusts Weights
```javascript
// User moves slider: pinnacle → 2, draftkings → 1
userWeights = {
  pinnacle: 2,
  draftkings: 1,
  fanduel: 0
};
```

### Step 4: Normalize & Recalculate
```javascript
// Normalize to 0-1 scale (same as backend)
const totalWeight = Object.values(userWeights).reduce((a, b) => a + b, 0);
const normalizedWeights = Object.fromEntries(
  Object.entries(userWeights).map(([book, w]) => [
    book,
    totalWeight > 0 ? w / totalWeight : 0
  ])
);
// { pinnacle: 0.667, draftkings: 0.333, fanduel: 0 }

// Recalculate fair odds using same formula as backend
const fairOdds = calculateWeightedFairOdds(rawOdds, normalizedWeights);
const ev = ((fairOdds * bestOdds) - 1) * 100;
```

## Key Design Points

### Hidden Weights
- EVisionBet's weights (`evisionbet_weights` in config) are server-side only
- Never enforced on frontend - users have full control
- Exposed via `/api/config/weights` for transparency/debugging
- Users' actual adjustment is completely independent

### User Slider Range
- Sliders: 0-4 scale (arbitrary choice)
- 0 means "I don't use this book"
- 4 means "I trust this book heavily"
- Normalized to 0-1 for fair odds calculation (sum to 1.0)

### Fair Odds Calculation
Both backend and frontend use identical logic:
1. Filter to sharp books (3-4 star rating)
2. Per-side calculation (Over/Under separately)
3. Remove outliers (5% for NBA, 3% for NFL)
4. Weight by user's adjusted weights
5. Calculate weighted average decimal odds

### CSV Output Compatibility
- Raw odds CSV: `/api/admin/raw-odds-csv` (all odds, unfiltered)
- EV hits CSV: `/api/admin/ev-opportunities-csv` (pre-calculated with EVisionBet weights)
- Users can export and analyze in Excel with any weights they want

## Testing the Endpoint

```bash
# Start backend
uvicorn backend_api:app --reload

# Test weights endpoint
curl http://localhost:8000/api/config/weights

# Test EV hits (pre-calculated with EVisionBet weights)
curl 'http://localhost:8000/api/ev/hits?limit=10&sport=basketball_nba'
```

## Integration with Pipeline

The pipeline now:
1. Extracts odds using per-sport config (tiers, regions)
2. Calculates fair odds using per-sport config (outlier thresholds, min sharps)
3. Stores in CSV with EVisionBet weights applied
4. Backend serves via `/api/ev/hits` (pre-calculated)
5. Frontend can recalculate with user weights via `/api/config/weights`

No changes to pipeline needed for frontend weight adjustment - it's purely frontend-side logic.
