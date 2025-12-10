# Deploy Backend API to Render (5 minutes)

## Step 1: Create Web Service on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect GitHub repo: **EV_ARB-Bot-VSCode**
4. Configure:
   - **Name:** `evision-api`
   - **Environment:** Python 3
   - **Region:** Oregon
   - **Build Command:** `pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv`
   - **Start Command:** `uvicorn backend_api:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free tier

## Step 2: Set Environment Variable

In **Settings** → **Environment**, add:
```
DATABASE_URL=postgresql://evisionbet_user:Rlb0zu7fmNmpAawcywknIWsRrOf0o4Rs@dpg-d4jus5ruibrs73f4hfm0-a.oregon-postgres.render.com/evisionbet
```

## Step 3: Deploy

Click **Create Web Service** and wait 2-3 minutes for deployment.

## Step 4: Verify

Once deployed, you'll get a URL like: `https://evision-api-xxxx.onrender.com`

Test it:
```
curl https://evision-api-xxxx.onrender.com/health
```

Response should be:
```json
{"status": "healthy", "database": "connected", "timestamp": "..."}
```

## API Endpoints

Your backend will expose:

- **GET /health** - Health check
- **GET /api/ev/hits** - EV opportunities (filterable by sport, min_ev)
- **GET /api/ev/summary** - Summary stats (total hits, top EV, by sport)
- **GET /api/odds/latest** - All odds from all bookmakers

## Update Frontend URL (if needed)

If your deployed URL is different from `https://evision-api.onrender.com`:

1. Edit `frontend/src/config.js`
2. Update `PROD_API` to your actual URL
3. Commit and push (Netlify will auto-redeploy)

## Done!

Your system is now:
- ✅ Extracting odds every 3 hours
- ✅ Calculating EV every 3 hours
- ✅ Data in PostgreSQL
- ✅ API exposing data via REST
- ✅ Frontend displaying live opportunities

**Optional:** Monitor logs on Render dashboard for any errors.
