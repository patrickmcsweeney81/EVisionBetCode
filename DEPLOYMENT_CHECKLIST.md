# Render Deployment Checklist

**Status:** In Progress  
**Date:** December 10, 2025

---

## ✅ Completed

- [x] GitHub repository cleaned up (EVisionBetCode)
- [x] Code tested locally (extract_odds.py + calculate_opportunities.py working)
- [x] Changes committed & pushed to GitHub
- [x] Database created on Render (evisionbet-db)
- [x] `.env` updated with DATABASE_URL
- [x] requirements.txt verified

---

## 🚀 In Progress - Cron Job Deployment

### Cron Job 1: Extract Odds

**Status:** Deploying (fixing root directory)

**Steps:**
1. ✅ Go to Render dashboard
2. ✅ Click on `evision-extract-odds` cron job
3. **TODO:** Click Settings (three dots menu)
4. **TODO:** Set Root Directory to `.` (just a dot)
5. **TODO:** Save & Redeploy
6. **TODO:** Check logs - should see `[OK] Read 972 rows...`

**Config (for reference):**
```
Name: evision-extract-odds
Repo: EV_ARB-Bot-VSCode
Branch: main
Root Directory: .
Build Command: pip install -r requirements.txt
Start Command: python pipeline_v2/extract_odds.py
Schedule: */30 7-23 * * *
```

**Environment Variables:**
```
ODDS_API_KEY=81d1ac74594d5d453e242c14ad479955
REGIONS=au,us,eu,us2
SPORTS=basketball_nba,basketball_nbl,americanfootball_nfl
MARKETS=h2h,spreads,totals
DATABASE_URL=postgresql://evisionbet_user:Ri8Ec7TiRdqsaycYwN1dKcQm8dkDo@dsp-db1u5ccds6x7z4ceb-a.oregon.postgres.render.com:5432/evisionbet
```

---

### Cron Job 2: Calculate EV

**Status:** Not yet created

**Steps (same as above):**
1. Click "New +"
2. Click "Cron Job"
3. Fill in config below
4. Set Root Directory to `.`
5. Create

**Config:**
```
Name: evision-calculate-ev
Repo: EV_ARB-Bot-VSCode
Branch: main
Root Directory: .
Build Command: pip install -r requirements.txt
Start Command: python pipeline_v2/calculate_opportunities.py
Schedule: 5,35 7-23 * * *
```

**Environment Variables:** (same as Cron Job 1)

---

## 📋 Post-Deployment

Once both cron jobs are deployed:

1. **Check logs** in Render for each job
2. **Verify extraction runs** - look for `[OK] Read XXX rows...`
3. **Verify calculation runs** - look for `[OK] Found XX opportunities...`
4. **Check database** - query tables to see data populated

---

## 🎯 Next Steps After Cron Jobs Work

1. **Create API Service** (optional) - expose data via FastAPI
2. **Connect Frontend** - EVisionBetSite dashboard calls API
3. **Monitor first week** - ensure consistent runs
4. **Delete legacy folder** - once confident system works

---

## ⚠️ Troubleshooting

**If deployment fails:**
- Check "Root Directory" is set to `.`
- Check all Environment Variables are copied exactly
- Look at deployment logs for specific errors
- Verify GitHub repo has latest code (run `git push` if needed)

**If tables aren't created:**
- Tables are created automatically by first successful run
- Check logs for database connection errors
- Verify DATABASE_URL is correct

**If no EV opportunities found:**
- Normal - depends on sports/markets
- Check raw_odds_pure.csv has data
- Verify sharp bookmakers have quotes

---

## 💾 Files Modified/Created

- ✅ `.env` - Added DATABASE_URL
- ✅ `create_tables.sql` - SQL schema
- ✅ `setup_database.py` - Database setup script
- ✅ `run_create_tables.py` - Alternative setup
- ✅ `pipeline_v2/extract_odds.py` - Extraction job
- ✅ `pipeline_v2/calculate_opportunities.py` - Calculation job

---

## 📞 Quick Reference

**Render Dashboard:** https://dashboard.render.com

**Your Services:**
- Database: `evisionbet-db`
- Cron Job 1: `evision-extract-odds`
- Cron Job 2: `evision-calculate-ev`

**GitHub Repo:** https://github.com/patrickmcsweeney81/EV_ARB-Bot-VSCode

---

**Last Updated:** 2025-12-10 22:00 UTC  
**Next Action:** Fix root directory on cron jobs and redeploy
