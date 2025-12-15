# EVisionBet Deployment Runbook

## Overview
Two-repo system:
- **EVisionBetCode** (Backend + Pipeline) → Render
- **EVisionBetSite** (Frontend) → Netlify

## Prerequisites

### API Keys & Secrets
1. **The Odds API Key**
   - Get from: https://the-odds-api.com/
   - Set in Render: `ODDS_API_KEY`

2. **Admin Password Hash** (optional, for protected endpoints)
   ```bash
   python -c "import hashlib; print(hashlib.sha256('yourpassword'.encode()).hexdigest())"
   ```
   - Set in Render: `ADMIN_PASSWORD_HASH`

3. **Database**
   - Auto-provisioned PostgreSQL in render.yaml
   - Connection string auto-populated as `DATABASE_URL`

## Render (Backend) Deployment

### Services Overview
1. **evision-api** (Web Service) - FastAPI backend
   - URL: https://evision-api.onrender.com
   - Auto-deploys on main branch push
   - Serves /api/ev/hits and /api/odds/raw endpoints

2. **evision-extract-odds** (Cron Job)
   - Schedule: Every 30 minutes (*/30 * * * *)
   - Fetches live odds from The Odds API
   - Writes to: PostgreSQL + raw_odds_pure.csv

3. **evision-calculate-ev** (Cron Job)
   - Schedule: :05 and :35 every hour (5 min after extract)
   - Calculates EV opportunities from raw odds
   - Writes to: PostgreSQL + ev_hits.csv

4. **evisionbet-db** (PostgreSQL Database)
   - Free tier: 256MB RAM, 1GB storage
   - Tables: live_odds, ev_opportunities, etc.

### Deployment Steps

1. **Push to GitHub**
   ```bash
   cd C:\EVisionBetCode
   git add -A
   git commit -m "Your changes"
   git push origin main
   ```

2. **Render Auto-Deploy**
   - Render detects push to main branch
   - Rebuilds all 3 services (API + 2 cron jobs)
   - Build time: ~3-5 minutes

3. **Verify Deployment**
   - Check [Render Dashboard](https://dashboard.render.com/project/prj-d4i72rfdies73c0hkvg)
   - API: https://evision-api.onrender.com/health
   - Expected response:
     ```json
     {
       "status": "healthy",
       "version": "2.0",
       "database": "connected",
       "pipelines": {
         "extract_odds": {"status": "healthy", "last_run": "2025-12-15T10:00:00", "age_seconds": 120},
         "calculate_ev": {"status": "healthy", "last_run": "2025-12-15T10:05:00", "age_seconds": 60}
       }
     }
     ```

4. **Check Cron Job Logs**
   - Navigate to evision-extract-odds service → Logs
   - Verify "✅ Wrote X rows" message
   - Navigate to evision-calculate-ev service → Logs
   - Verify "✅ Wrote X opportunities" message

## Netlify (Frontend) Deployment

### Service Overview
- **evisionbetsite** - React SPA
- URL: https://evisionbetsite.netlify.app
- API Target: https://evision-api.onrender.com

### Deployment Steps

1. **Push to GitHub**
   ```bash
   cd C:\EVisionBetSite
   git add -A
   git commit -m "Your changes"
   git push origin main
   ```

2. **Netlify Auto-Deploy**
   - Netlify detects push to main branch
   - Runs: `npm run build` in frontend/ directory
   - Build time: ~2-3 minutes
   - Deploys to CDN

3. **Verify Deployment**
   - Check [Netlify Dashboard](https://app.netlify.com/projects/evisionbetsite)
   - Visit: https://evisionbetsite.netlify.app
   - Login and verify EV hits load correctly

## Troubleshooting

### Cron Jobs Failing

**Problem:** `ModuleNotFoundError: No module named 'pandas'`
- **Cause:** Missing dependency in pyproject.toml
- **Fix:** Ensure pyproject.toml includes all required packages:
  ```toml
  dependencies = [
      "pandas>=2.0.0",
      "openpyxl>=3.1.0",
      "numpy>=1.24.0",
      # ... other deps
  ]
  ```

**Problem:** "Raw odds CSV not found"
- **Cause:** Extract job hasn't run or failed
- **Fix:** Check evision-extract-odds logs, verify ODDS_API_KEY is set

**Problem:** "File is X minutes old"
- **Cause:** Extract job not running on schedule
- **Fix:** Check cron schedule in render.yaml, verify service is active

### Frontend Build Failing

**Problem:** "Build script returned non-zero exit code: 2"
- **Cause:** Usually lint warnings treated as errors
- **Fix:** Check build logs, fix ESLint errors or add `CI=false` to build command

**Problem:** "API requests failing with CORS errors"
- **Cause:** API URL misconfigured
- **Fix:** Verify netlify.toml has correct REACT_APP_API_URL

### Database Issues

**Problem:** "Database not connected"
- **Cause:** DATABASE_URL not set or invalid
- **Fix:** Verify environment variable in Render dashboard

**Problem:** "Server closed connection unexpectedly"
- **Cause:** Database overloaded or connection pool exhausted
- **Fix:** API falls back to CSV automatically, check logs

## Monitoring

### Health Checks
- **API Health**: GET https://evision-api.onrender.com/health
- **EV Hits**: GET https://evision-api.onrender.com/api/ev/hits?limit=5
- **Raw Odds**: GET https://evision-api.onrender.com/api/odds/raw?limit=5

### Key Metrics
- **Extract Pipeline**: Should run every 30 min, write 500-2000 rows
- **Calculate Pipeline**: Should run 5 min after extract, find 50-200 opportunities
- **API Uptime**: Should respond within 1-2 seconds
- **Frontend Load**: Should load table in < 3 seconds

## Rollback Procedure

### Backend Rollback
1. Go to Render Dashboard
2. Select service (evision-api, evision-extract-odds, or evision-calculate-ev)
3. Click "Manual Deploy" → Select previous commit
4. Click "Deploy"

### Frontend Rollback
1. Go to Netlify Dashboard
2. Select evisionbetsite project
3. Navigate to "Deploys"
4. Find previous successful deploy
5. Click "Publish deploy"

## Emergency Contacts
- GitHub Repo Issues: https://github.com/patrickmcsweeney81/EVisionBetCode/issues
- The Odds API Support: https://the-odds-api.com/contact

## Quick Reference

### Environment Variables
| Variable | Required | Where | Purpose |
|----------|----------|-------|---------|
| ODDS_API_KEY | Yes | Render (all services) | Access The Odds API |
| DATABASE_URL | Yes | Render (all services) | PostgreSQL connection |
| ADMIN_PASSWORD_HASH | No | Render (API only) | Protect admin endpoints |
| REACT_APP_API_URL | Yes | Netlify | Backend API URL |

### File Paths (Render)
- Raw Odds: `/opt/render/project/src/data/raw_odds_pure.csv`
- EV Hits: `/opt/render/project/src/data/ev_hits.csv`
- Logs: Available in Render Dashboard → Service → Logs

### API Endpoints
- Health: `/health`
- EV Hits: `/api/ev/hits?limit=50&min_ev=0.01`
- Raw Odds: `/api/odds/raw?limit=500`
- Summary: `/api/ev/summary`
- Admin CSV Download: `/api/admin/ev-opportunities-csv` (auth required)

## Post-Deployment Checklist
- [ ] API health check returns "healthy"
- [ ] Extract pipeline logs show successful run
- [ ] Calculate pipeline logs show successful run
- [ ] Frontend loads without errors
- [ ] EV hits table displays data
- [ ] Filters and search work correctly
- [ ] Database shows recent data (if connected)
