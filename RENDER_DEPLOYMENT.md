# Render Backend Deployment Guide

**Purpose:** Set up auto-running extraction and calculation on Render  
**Status:** Ready to deploy

---

## Prerequisites

- ✅ Render account (render.com)
- ✅ GitHub repository with EVisionBetCode
- ✅ PostgreSQL database (Render or external)
- ✅ Odds API key (in .env)

---

## Step 1: Create PostgreSQL Database on Render

### Option A: Render PostgreSQL (Easiest)
1. Go to Render dashboard
2. Click "New" → "PostgreSQL"
3. Name: `evision-db`
4. Region: Same as backend (e.g., Ohio for US)
5. Instance Type: Starter (free tier) or Standard
6. Copy connection string: `postgresql://user:password@host:5432/db`
7. Save for `.env` as `DATABASE_URL`

### Option B: External PostgreSQL
- Use managed service (AWS RDS, Railway, etc.)
- Get connection string: `postgresql://user:password@host:5432/db`
- Add to `.env` as `DATABASE_URL`

---

## Step 2: Create Database Tables

Run this SQL once to set up tables:

```sql
-- Table 1: All extracted odds
CREATE TABLE live_odds (
    id SERIAL PRIMARY KEY,
    extracted_at TIMESTAMP NOT NULL,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    bookmaker VARCHAR(50) NOT NULL,
    odds DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_event_market (event_id, market),
    INDEX idx_bookmaker (bookmaker),
    INDEX idx_extracted_at (extracted_at),
    UNIQUE(event_id, market, point, selection, bookmaker, extracted_at)
);

-- Table 2: Calculated EV opportunities
CREATE TABLE ev_opportunities (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    player VARCHAR(200),
    fair_odds DECIMAL(10,2) NOT NULL,
    best_book VARCHAR(50) NOT NULL,
    best_odds DECIMAL(10,2) NOT NULL,
    ev_percent DECIMAL(5,2) NOT NULL,
    sharp_book_count INT,
    stake DECIMAL(10,2),
    kelly_fraction DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_detected_at (detected_at),
    INDEX idx_sport (sport),
    INDEX idx_ev_percent (ev_percent)
);

-- Table 3: Line movement tracking (optional, for future)
CREATE TABLE line_movements (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    market VARCHAR(50) NOT NULL,
    bookmaker VARCHAR(50) NOT NULL,
    old_odds DECIMAL(10,2),
    new_odds DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    
    INDEX idx_detected_at (detected_at),
    INDEX idx_event (event_id)
);
```

---

## Step 3: Update .env with Database URL

Add to `.env` in your repo:

```bash
# Render PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Or use connection pooling (recommended for serverless)
DATABASE_URL_POOLED=postgresql://user:password@host:6543/dbname
```

**Note:** If deploying to Render, use `DATABASE_URL_POOLED` for better connection handling

---

## Step 4: Deploy Extract Odds to Render

### Create a Cron Job Service

1. Go to Render dashboard
2. Click "New" → "Cron Job"
3. Configure:

**Basic Settings:**
- Name: `evision-extract-odds`
- GitHub repo: Select your EVisionBetCode repo
- Branch: `main`
- Root directory: `.` (leave empty)

**Build Settings:**
- Build command: `pip install -r requirements.txt`
- Start command: `python pipeline_v2/extract_odds.py`

**Environment Variables:**
Add to Render environment (or use .env file):
```
ODDS_API_KEY=your_key_here
REGIONS=au,us,eu,us2
SPORTS=basketball_nba,basketball_nbl,americanfootball_nfl
MARKETS=h2h,spreads,totals
DATABASE_URL=postgresql://...
```

**Schedule:**
- Every 30 minutes during game hours
- Cron: `*/30 7-23 * * *` (7am-11pm UTC)
- Or: `*/60 * * * *` (hourly, all day)
- Adjust based on your sports schedule

### Alternative: Use Render Background Worker + Scheduler

If cron jobs aren't available:
1. Create a Background Worker service
2. Deploy Python app that runs extraction loop
3. Add sleep(1800) to wait between runs

---

## Step 5: Deploy Calculate Opportunities to Render

### Create Second Cron Job

1. Go to Render dashboard
2. Click "New" → "Cron Job"
3. Configure:

**Basic Settings:**
- Name: `evision-calculate-ev`
- GitHub repo: Same EVisionBetCode repo
- Branch: `main`

**Build Settings:**
- Build command: `pip install -r requirements.txt`
- Start command: `python pipeline_v2/calculate_opportunities.py`

**Environment Variables:**
Same as above

**Schedule:**
- Run after `extract_odds` completes
- Cron: `5,35 7-23 * * *` (5 min after :00 and :30)
- Or delay to: `10,40 7-23 * * *` (10 min after each extraction)

**Timing:**
- Extract runs at :00 and :30
- Calculate waits 5-10 minutes, then runs
- Prevents race conditions

---

## Step 6: Create API Endpoints (Optional)

### Option A: FastAPI Microservice

Create `render_api.py`:

```python
from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL_POOLED") or os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

app = FastAPI()

@app.get("/api/odds/latest")
def get_latest_odds(sport: str = "basketball_nba", limit: int = 100):
    """Get latest odds for a sport"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM live_odds 
            WHERE sport = :sport 
            ORDER BY extracted_at DESC 
            LIMIT :limit
        """), {"sport": sport, "limit": limit})
        return [dict(row) for row in result]

@app.get("/api/opportunities/current")
def get_opportunities(sport: str = None, min_ev: float = 1.0):
    """Get current EV opportunities"""
    query = "SELECT * FROM ev_opportunities WHERE ev_percent >= :min_ev"
    params = {"min_ev": min_ev}
    
    if sport:
        query += " AND sport = :sport"
        params["sport"] = sport
    
    query += " ORDER BY ev_percent DESC LIMIT 50"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row) for row in result]

@app.get("/health")
def health():
    return {"status": "ok"}
```

Deploy as Render Web Service:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn render_api:app --host 0.0.0.0 --port 10000`
- Environment: Same as cron jobs

---

## Step 7: Connect Frontend to Backend

### Update EVisionBetSite API Client

In `EVisionBetSite/frontend/src/api/client.js`:

```javascript
// Backend URL (Render)
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://evision-api.render.com';

export const fetchLatestOdds = async (sport, limit = 100) => {
    const response = await fetch(`${BACKEND_URL}/api/odds/latest?sport=${sport}&limit=${limit}`);
    return response.json();
};

export const fetchOpportunities = async (sport = null, minEV = 1.0) => {
    let url = `${BACKEND_URL}/api/opportunities/current?min_ev=${minEV}`;
    if (sport) url += `&sport=${sport}`;
    const response = await fetch(url);
    return response.json();
};
```

### Update Dashboard Cards

```javascript
// Card 1: All Odds
import { fetchLatestOdds } from '../api/client';

function AllOddsCard() {
    const [odds, setOdds] = useState([]);
    
    useEffect(() => {
        fetchLatestOdds('basketball_nba').then(setOdds);
    }, []);
    
    return (
        <div className="odds-card">
            <h3>All Odds</h3>
            {odds.map(odd => (
                <div key={odd.id}>
                    {odd.selection} @ {odd.bookmaker}: {odd.odds}
                </div>
            ))}
        </div>
    );
}

// Card 2: EV Hits
import { fetchOpportunities } from '../api/client';

function EVHitsCard() {
    const [opportunities, setOpportunities] = useState([]);
    
    useEffect(() => {
        fetchOpportunities('basketball_nba', 1.0).then(setOpportunities);
    }, []);
    
    return (
        <div className="ev-card">
            <h3>EV Opportunities</h3>
            {opportunities.map(opp => (
                <div key={opp.id}>
                    {opp.selection}: {opp.ev_percent}% @ {opp.best_book} ({opp.best_odds})
                </div>
            ))}
        </div>
    );
}
```

---

## Step 8: Monitor Render Logs

1. Go to Render dashboard
2. Click each service (extract-odds, calculate-ev, api)
3. View "Logs" tab to watch execution
4. Check for errors or performance issues

**Expected logs:**
```
2025-12-10 14:30:00 INFO: Starting extraction...
2025-12-10 14:31:45 INFO: Fetched 1,245 rows from API
2025-12-10 14:32:10 INFO: Wrote to live_odds table
2025-12-10 14:35:00 INFO: Starting EV calculation...
2025-12-10 14:35:30 INFO: Found 23 opportunities
2025-12-10 14:35:45 INFO: Calculation complete
```

---

## Step 9: Test Full Flow

### Local Testing
```bash
# Stage 1
python pipeline_v2/extract_odds.py

# Check CSV
head -5 data/raw_odds_pure.csv

# Stage 2
python pipeline_v2/calculate_opportunities.py

# Check results
head -5 data/ev_opportunities.csv
```

### Render Testing
1. Trigger cron jobs manually in Render dashboard
2. Check logs for success
3. Query database to verify data:
   ```sql
   SELECT COUNT(*) FROM live_odds;
   SELECT COUNT(*) FROM ev_opportunities;
   ```
4. Test API endpoints:
   ```bash
   curl https://evision-api.render.com/api/odds/latest?sport=basketball_nba
   curl https://evision-api.render.com/api/opportunities/current
   ```
5. Check frontend for data display

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No connection" to DB** | Check DATABASE_URL in Render env vars |
| **"Module not found"** | Ensure requirements.txt has all dependencies |
| **API timeout** | Increase cron job timeout in Render settings |
| **No data in DB** | Check logs for extraction errors; verify API key |
| **Frontend shows no data** | Test API endpoint directly; check CORS settings |
| **Out of disk space** | Render free tier has 512MB - archive old CSV data |

---

## Maintenance

### Weekly
- Check logs for errors
- Verify data freshness (recent timestamps)
- Monitor EV opportunity count

### Monthly
- Archive old CSVs to avoid disk space issues
- Review bookmaker coverage
- Adjust EV threshold if needed

### As Needed
- Edit `.env` or `config.py` via GitHub mobile app
- Push changes
- Render auto-redeploys
- Monitor new run for correctness

---

## Summary

✅ Database created  
✅ Extract odds cron job deployed  
✅ Calculate EV cron job deployed  
✅ API endpoints created (optional)  
✅ Frontend connected  
✅ Mobile editing enabled  
✅ System auto-running on schedule  

**Result:** 
- Every 30 min: All sports odds fetched
- Every 30 min (delayed): EV opportunities calculated
- Frontend: Real-time "All Odds" + "EV Hits" cards
- CSVs: Backup on your computer when online
- Mobile: Edit .env or config.py from GitHub app, auto-redeploy
