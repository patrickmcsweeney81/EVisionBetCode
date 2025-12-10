# Backend API Deployment Guide

## Overview

The FastAPI backend service (`backend_api.py`) exposes EV_ARB Bot data from PostgreSQL to the frontend via REST API endpoints. This document covers deployment to Render.

---

## Quick Start (Render Deployment)

### Step 1: Push Backend to GitHub

```powershell
cd C:\EVisionBetCode
git add backend_api.py
git commit -m "feat: add FastAPI backend API service"
git push origin main
```

### Step 2: Create Web Service on Render

1. Go to **[Render Dashboard](https://dashboard.render.com)**
2. Click **New +** → **Web Service**
3. Connect your GitHub repository (EVisionBetCode)
4. Configure:
   - **Name:** `evision-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv`
   - **Start Command:** `uvicorn backend_api:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free tier (sufficient for API requests)

5. **Environment Variables** (from Settings):
   ```
   DATABASE_URL=postgresql://...  # Copy from your existing PostgreSQL credentials
   PYTHON_VERSION=3.11.4
   ```

6. Click **Create Web Service**
7. Wait 2-3 minutes for deployment to complete

### Step 3: Get API URL

Once deployed, Render will assign a URL like:
```
https://evision-api.onrender.com
```

This is automatically set in `frontend/src/config.js` as `PROD_API`.

---

## API Endpoints

### Health Check
```
GET /health
```
Returns database connection status:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-10T15:30:00"
}
```

### Get EV Opportunities
```
GET /api/ev/hits?limit=50&min_ev=0.01&sport=basketball_nba
```

**Parameters:**
- `limit` (int, default=50): Max results (1-1000)
- `min_ev` (float, default=0.01): Minimum EV as decimal (0.01 = 1%)
- `sport` (string, optional): Filter by sport key

**Response:**
```json
{
  "hits": [
    {
      "sport": "basketball_nba",
      "event_id": "...",
      "event_name": "Team A vs Team B",
      "market": "h2h",
      "selection": "Team A",
      "fair_odds": 2.15,
      "best_odds": 2.25,
      "best_book": "DraftKings",
      "ev_percent": 4.65,
      "sharp_book_count": 8,
      "extracted_at": "2025-12-10T15:30:00"
    }
  ],
  "count": 42,
  "last_updated": "2025-12-10T15:30:00"
}
```

### Get EV Summary
```
GET /api/ev/summary
```

Returns aggregate statistics:
```json
{
  "available": true,
  "total_hits": 127,
  "top_ev": 6.42,
  "sports": {
    "basketball_nba": 45,
    "americanfootball_nfl": 82
  },
  "last_updated": "2025-12-10T15:30:00"
}
```

### Get Latest Odds
```
GET /api/odds/latest?limit=500&sport=basketball_nba
```

Returns all odds for all bookmakers:
```json
{
  "odds": [
    {
      "sport": "basketball_nba",
      "event_id": "...",
      "event_name": "Team A vs Team B",
      "market": "h2h",
      "selection": "Team A",
      "bookmaker": "DraftKings",
      "odds": 2.25,
      "extracted_at": "2025-12-10T15:30:00"
    }
  ],
  "count": 523,
  "last_updated": "2025-12-10T15:30:00"
}
```

---

## Database Models

### `live_odds` table
- **sport:** Sport key (basketball_nba, americanfootball_nfl, etc.)
- **event_id:** Unique event identifier from The Odds API
- **event_name:** Human-readable event name
- **market:** Market type (h2h, spreads, totals)
- **selection:** Selection name (Team A, Over, Under, etc.)
- **bookmaker:** Bookmaker name (DraftKings, FanDuel, etc.)
- **odds:** Decimal odds
- **extracted_at:** Extraction timestamp (UTC)

### `ev_opportunities` table
- **sport:** Sport key
- **event_id:** Event identifier
- **event_name:** Event name
- **market:** Market type
- **selection:** Selection name
- **fair_odds:** Fair odds calculated from sharp bookmakers
- **best_odds:** Best available odds across bookmakers
- **best_book:** Bookmaker offering best odds
- **ev_percent:** Expected value percentage (0.045 = 4.5%)
- **sharp_book_count:** Number of sharp bookmakers used in fair odds calc
- **extracted_at:** Extraction timestamp (UTC)

---

## Frontend Integration

The frontend automatically uses the backend API:

1. **EVHits Component** (`frontend/src/components/EVHits.js`)
   - Fetches `/api/ev/hits` on page load
   - Filters by min_ev, sport
   - Refreshes every 2 minutes

2. **OddsComparison Component** (`frontend/src/components/OddsComparison.js`)
   - Fetches `/api/odds/latest` for bookmaker odds
   - Displays odds comparison table

3. **Dashboard Component** (`frontend/src/components/Dashboard.js`)
   - Links to EV Finder (EVHits)
   - Links to Odds Comparison

---

## Local Development

To test the API locally:

### 1. Install Dependencies
```powershell
cd C:\EVisionBetCode
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
```

### 2. Run Locally
```powershell
# Ensure DATABASE_URL is set in .env
python -m uvicorn backend_api:app --reload --port 8000
```

API will be available at:
- **Base:** `http://localhost:8000`
- **Docs:** `http://localhost:8000/docs` (interactive Swagger UI)
- **OpenAPI:** `http://localhost:8000/openapi.json`

### 3. Test Endpoints
```powershell
# Health check
curl http://localhost:8000/health

# Get EV hits
curl "http://localhost:8000/api/ev/hits?limit=10&min_ev=0.01"

# Get summary
curl http://localhost:8000/api/ev/summary

# Get latest odds
curl "http://localhost:8000/api/odds/latest?limit=100"
```

### 4. Frontend Development
For local frontend development pointing to local API:
```bash
cd C:\EVisionBetSite\frontend
npm start
```
Frontend will automatically detect `localhost` hostname and use `http://localhost:8000` (LOCAL_API).

---

## Monitoring & Logs

### Check API Status
1. Go to **Render Dashboard** → **evision-api**
2. Click **Logs** tab
3. Look for:
   - `Application is running` - API started successfully
   - `INFO:     Uvicorn running on 0.0.0.0:PORT` - Ready to accept requests
   - Database connection errors - Check DATABASE_URL

### Common Issues

**Issue:** "ERROR: No module named 'fastapi'"
- **Fix:** Ensure build command includes `pip install fastapi uvicorn`

**Issue:** "Error connecting to PostgreSQL"
- **Fix:** Check DATABASE_URL environment variable is set correctly
  - Should start with `postgresql://` (not `postgres://`)
  - Verify credentials in Render PostgreSQL settings

**Issue:** "502 Bad Gateway" from frontend
- **Fix:** API service may still be building. Wait 2-3 minutes.
- Check `/health` endpoint returns 200 status

**Issue:** "CORS error from frontend"
- **Fix:** API already has `CORSMiddleware` configured for all origins
- This is safe for public API; restrict if needed in production

---

## Production Considerations

### Cost
- **Free Tier:** Sufficient for current volume (< 100 API calls/minute)
- **Upgrade:** If > 1000 calls/minute, upgrade to Pro tier ($7/month)

### Performance
- Database queries are optimized with indexes on:
  - `sport`, `event_id`, `market`, `extracted_at`
  - Add indexes if response time > 500ms

### Security (Optional Future)
- Add API key authentication if exposing publicly
- Add rate limiting if needed
- Enable HTTPS (automatic on Render)

---

## Next Steps

1. ✅ Backend deployed and running on Render
2. ✅ Frontend automatically uses backend API
3. Dashboard displays live EV opportunities
4. Monitor logs for any errors (see Monitoring section above)

---

## Reference

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Render Docs:** https://render.com/docs
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org
- **Uvicorn Docs:** https://www.uvicorn.org
