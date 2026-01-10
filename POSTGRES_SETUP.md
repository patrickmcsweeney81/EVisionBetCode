# Render Postgres Setup - Basic-256mb Plan
**Last Updated:** January 10, 2026

---

## 🎯 Recommended Plan: Basic-256mb ($6/month)

✅ **Perfect for your needs:**
- Current data: 4.29 MB
- Projected (12 sports): ~200 MB
- 256 MB RAM is ~5-10x more than needed
- Room to grow without upgrade

---

## 📋 Setup Steps on Render Dashboard

### 1. Create Postgres Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name:** `evisionbet-db`
   - **Database:** `evisionbet`
   - **Region:** Oregon (same as your services)
   - **Plan:** **Basic-256mb** ($6/month)
   - **PostgreSQL Version:** 16 (latest)

4. Click **Create Database**

### 2. Get Connection String

After creation, Render shows:
```
Internal Database URL:
postgresql://evisionbet_db_user:LONG_PASSWORD_HERE@dpg-xxxxx-a.oregon-postgres.render.com/evisionbet_db
```

**Copy this entire URL** - you'll need it for services.

### 3. Connect Services to Database

#### Option A: Automatic (via render.yaml) ✅ RECOMMENDED

Your `render.yaml` already has this configured:
```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: evisionbet-db
      property: connectionString
```

**This auto-populates `DATABASE_URL` on all services!**

#### Option B: Manual (if needed)

For each service (`evision-api`, `evision-extract-odds`, `evision-calculate-ev`):
1. Go to service → **Environment**
2. Add environment variable:
   - Key: `DATABASE_URL`
   - Value: Paste the connection string from step 2
3. Click **Save Changes**

### 4. Deploy Services

After database is created:
1. **Manual trigger:** Each service → **Manual Deploy** → **Clear build cache & deploy**
2. **Automatic:** Just push to GitHub (triggers auto-deploy)

---

## 🔍 Verify Connection

### Check API Health Endpoint

```bash
curl https://evision-api.onrender.com/health
```

**Expected response:**
```json
{
  "status": "ok",
  "database": "connected",
  "ev_csv": "AllSports_EV.csv",
  "timestamp": "2026-01-10T12:34:56.789"
}
```

If `"database": "csv_fallback"` → connection failed, check DATABASE_URL.

### Check Render Logs

1. Go to service → **Logs**
2. Look for:
   - ✅ `Database engine initialized`
   - ✅ `Using database for data retrieval`
   - ❌ `DATABASE_URL not set - running in CSV-only mode`

---

## 📊 Database Tables (Auto-Created)

Your backend auto-creates these tables on first connection:

| Table | Columns | Purpose |
|-------|---------|---------|
| `ev_opportunities` | 20+ columns | Calculated EV hits |
| `live_odds` | 15+ columns | Raw odds from API |

**Schema is in backend_api.py** - see `EVOpportunity` and `LiveOdds` models.

---

## 💰 Cost Breakdown

**Basic-256mb Plan:**
- Base: $6/month (256 MB RAM, 0.1 CPU)
- Storage: ~$0.25/month (1 GB at $0.25/GB)
- **Total: ~$6.25/month**

**When to upgrade to Basic-1gb ($19/month):**
- Database >500 MB
- 1,000+ concurrent users
- Complex analytics queries

---

## 🔧 Local Development

For local testing with Postgres:

```bash
# Option 1: Use CSV-only mode (current setup)
# Don't set DATABASE_URL in .env

# Option 2: Connect to Render database (from local)
# Add to .env:
DATABASE_URL=postgresql://evisionbet_db_user:PASSWORD@dpg-xxxxx.oregon-postgres.render.com/evisionbet_db

# Option 3: Run Postgres locally (Docker)
docker run --name evision-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:16
# Add to .env:
DATABASE_URL=postgresql://postgres:password@localhost:5432/evisionbet
```

**Recommended for local:** CSV-only mode (no DATABASE_URL). Faster, no database overhead.

---

## 🚨 Troubleshooting

### "FATAL: password authentication failed"
→ Check DATABASE_URL format: `postgresql://` (not `postgres://`)  
→ Backend auto-converts `postgres://` to `postgresql://`

### "database 'evisionbet_db' does not exist"
→ Database name mismatch. Check Render dashboard → Database → **Name** field

### "could not connect to server"
→ Check firewall/network  
→ Verify database region matches service region (both Oregon)

### "CSV-only mode" in logs
→ DATABASE_URL not set or connection failed  
→ Check environment variables in service settings

### Slow queries
→ Check Render dashboard → Database → **Metrics** tab  
→ If RAM usage >200 MB, upgrade to Basic-1gb

---

## 📈 Monitoring

**Render Dashboard → Database → Metrics:**
- **RAM Usage:** Should be <100 MB with current data
- **CPU Usage:** Should be <20% (mostly idle)
- **Connections:** Should be 1-3 (one per active service)
- **Storage:** Should be <1 GB

**Set alerts:**
- RAM >150 MB → consider upgrade
- Storage >5 GB → clean up old data

---

## 🎯 Next Steps

1. ✅ Create `evisionbet-db` database (Basic-256mb)
2. ✅ Wait for database to provision (~2 min)
3. ✅ Copy Internal Database URL
4. ✅ Services auto-connect via render.yaml (or add manually)
5. ✅ Trigger manual deploy on all 3 services
6. ✅ Check health endpoint: `/health` shows `"database": "connected"`
7. ✅ Run extract/calculate pipelines (writes to database)
8. ✅ Verify frontend displays data

**Once working:** CSV fallback is automatic if DB ever goes down!

---

**Questions?** Check backend_api.py lines 113-129 for database connection logic.
