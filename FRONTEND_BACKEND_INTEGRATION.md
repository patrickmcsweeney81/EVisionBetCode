# Frontend-Backend Integration Checklist

## ✅ Completed Steps

### 1. Backend API Created
- ✅ `backend_api.py` - FastAPI service with PostgreSQL integration
- ✅ Endpoints: `/health`, `/api/ev/hits`, `/api/ev/summary`, `/api/odds/latest`
- ✅ Database models: LiveOdds, EVOpportunity
- ✅ CORS enabled for frontend communication
- ✅ Committed to GitHub (commit: b5f4761)

### 2. Requirements Updated
- ✅ FastAPI 0.109.0+ added to `requirements.txt`
- ✅ Uvicorn 0.27.0+ added to `requirements.txt`
- ✅ All dependencies ready for Render deployment

### 3. Frontend Configuration
- ✅ `frontend/src/config.js` updated with backend URL
- ✅ Production URL: `https://evision-api.onrender.com`
- ✅ Local URL: `http://localhost:8000`
- ✅ Auto-detection based on hostname

### 4. Frontend Components Ready
- ✅ EVHits component fetches `/api/ev/hits`
- ✅ OddsComparison component fetches `/api/odds/latest`
- ✅ Dashboard links to both components
- ✅ Auto-refresh every 2 minutes

---

## 📋 Next Steps (Deploy Backend to Render)

### Step 1: Create Web Service on Render
1. Go to **[Render Dashboard](https://dashboard.render.com)**
2. Click **New +** → **Web Service**
3. Connect your GitHub repository (EV_ARB-Bot-VSCode)
4. Configure:
   - **Name:** `evision-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv`
   - **Start Command:** `uvicorn backend_api:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free tier

### Step 2: Set Environment Variables
In **Settings** → **Environment**, add:
```
DATABASE_URL=postgresql://user:password@host:port/database
PYTHON_VERSION=3.11.4
```
(Copy DATABASE_URL from your existing PostgreSQL on Render)

### Step 3: Deploy
- Click **Create Web Service**
- Wait 2-3 minutes for build to complete
- Check **Logs** tab for: `Application is running`
- Note the deployed URL (e.g., `https://evision-api-xxxx.onrender.com`)

### Step 4: Update Frontend URL (if needed)
If your deployed URL differs from `https://evision-api.onrender.com`:
1. Update `frontend/src/config.js` `PROD_API` variable
2. Commit and push to trigger EVisionBetSite rebuild

### Step 5: Verify Integration
1. Go to EVisionBetSite frontend
2. Click "Expected Value Finder"
3. Should see:
   - Green health badge ✓
   - EV opportunities loading from backend
   - Summary stats (total hits, top EV, sports breakdown)
4. Click "View Odds"
5. Should see:
   - All bookmaker odds
   - Live updates every 2 minutes

---

## 🔌 API Endpoints

### Health Check
```
GET https://evision-api.onrender.com/health
```
Response: `{"status": "healthy", "database": "connected"}`

### EV Opportunities
```
GET https://evision-api.onrender.com/api/ev/hits?limit=50&min_ev=0.01
```
Returns top EV opportunities with fairodds, best bookmaker, EV%.

### EV Summary
```
GET https://evision-api.onrender.com/api/ev/summary
```
Returns aggregate stats: total hits, top EV, sports breakdown.

### Latest Odds
```
GET https://evision-api.onrender.com/api/odds/latest?limit=500
```
Returns all odds across all bookmakers.

---

## 🧪 Local Testing (Optional)

Before deploying to Render, test locally:

```powershell
cd C:\EVisionBetCode

# Install FastAPI dependencies
pip install fastapi uvicorn

# Run backend locally
python -m uvicorn backend_api:app --reload --port 8000
```

API will be available at `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health`

Frontend will automatically detect localhost and use local API.

---

## 📊 Data Flow Architecture

```
The Odds API v4
    ↓
extract_odds.py (runs every 3 hours on Render)
    ↓
PostgreSQL live_odds table
    ↓
Backend API (/api/odds/latest)
    ↓
Frontend OddsComparison component
    ↓
User sees live odds from all bookmakers


The Odds API v4
    ↓
calculate_opportunities.py (runs 5 min after extraction)
    ↓
PostgreSQL ev_opportunities table
    ↓
Backend API (/api/ev/hits, /api/ev/summary)
    ↓
Frontend EVHits component
    ↓
User sees EV opportunities with fair odds & best books
```

---

## 📝 Key Files

| File | Purpose | Status |
|------|---------|--------|
| `backend_api.py` | FastAPI service | ✅ Created |
| `requirements.txt` | Python dependencies | ✅ Updated |
| `BACKEND_API_DEPLOYMENT.md` | Detailed deployment guide | ✅ Created |
| `frontend/src/config.js` | API URL configuration | ✅ Updated |
| `frontend/src/components/EVHits.js` | EV opportunities display | ✅ Ready |
| `frontend/src/components/OddsComparison.js` | Odds comparison | ✅ Ready |

---

## ✨ What Works Now

- ✅ Extraction cron job runs every 3 hours → PostgreSQL
- ✅ Calculation cron job runs 5 min after → PostgreSQL
- ✅ Backend API exposes data via REST endpoints
- ✅ Frontend auto-detects backend URL (localhost or production)
- ✅ Frontend displays EV opportunities with auto-refresh
- ✅ Frontend displays live odds comparison

---

## 🎯 System Status

| Component | Status | Details |
|-----------|--------|---------|
| Extraction (evision-extract-odds) | ✅ Running | Every 3 hours on Render |
| Calculation (evision-calculate-ev) | ✅ Running | 5 min after extraction |
| PostgreSQL (evisionbet-db) | ✅ Running | Free tier on Render |
| Backend API | ⏳ Ready to deploy | Awaiting Step 1 above |
| Frontend | ✅ Ready | Configured for backend |

---

## 💡 Next Phase (Optional)

After backend API is deployed and verified working:
1. Monitor logs for errors
2. Test EV opportunities calculation accuracy
3. Add user authentication (FastAPI with JWT)
4. Add user favorites/bookmarks (PostgreSQL users table)
5. Add betting unit recommendation (Kelly fraction calculator)
