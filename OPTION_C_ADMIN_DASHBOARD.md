# Option C: Admin/Designer CSV Download Dashboard

**Status:** ✅ COMPLETE & DEPLOYED

---

## Overview

You now have a complete **Option C setup** where:
- ✅ Pipeline writes data directly to **PostgreSQL database**
- ✅ Admin page (`/admin`) allows password-protected access
- ✅ Download complete database as CSV on **any computer**
- ✅ View real-time database statistics
- ✅ Works from anywhere with internet access

---

## How It Works

### 1. **Pipeline → Database** (Automatic - Every 30 min)

```
extract_odds.py (fetch from The Odds API)
    ↓
calculate_opportunities.py (calculate EV)
    ↓
PostgreSQL Database (all data stored here)
```

**Data written to database:**
- `ev_opportunities` table - EV opportunities with fair odds, best books, percentages
- `live_odds` table - Raw odds from all bookmakers (backup)

### 2. **Admin Access** (Manual - Anytime)

**Navigate to:** `https://yourapp.com/admin`

**Login:**
- Default password: `admin123`
- Click "Login"

**You get:**
- 📊 Real-time database statistics
  - Total EV opportunities count
  - Total raw odds rows
  - Last update timestamp
- 💾 Download buttons:
  - **EV Opportunities CSV** - Download complete EV database
  - **Raw Odds CSV** - Download latest odds extract

**Download works on:**
- ✅ Local machine
- ✅ Work computer
- ✅ Laptop
- ✅ Any computer with internet (no special software needed)

---

## Components Created

### Backend (`EVisionBetCode/backend_api.py`)

**New Endpoints:**
```
POST   /api/admin/auth
       → Authenticate with password
       → Returns bearer token

GET    /api/admin/ev-opportunities-csv
       → Download EV CSV from database
       → Requires bearer token

GET    /api/admin/raw-odds-csv
       → Download raw odds CSV from database
       → Requires bearer token

GET    /api/admin/database-stats
       → View record counts and last update times
       → Requires bearer token
```

**Authentication:**
- Password verified via SHA256 hash
- Default: `admin123`
- Change via env var: `ADMIN_PASSWORD_HASH`

### Frontend (`EVisionBetSite/frontend/src/components/AdminPanel.js`)

**Features:**
- Clean login form
- Display database statistics
- Download buttons for EV CSV
- Download buttons for raw odds CSV
- Info section explaining the system
- Mobile responsive design
- Dark theme with teal accents

### Database Integration (`calculate_opportunities.py`)

**Updated to:**
- ✅ Write all EV opportunities to database
- ✅ Clear old records on each run
- ✅ Handle database errors gracefully
- ✅ Maintain CSV backup regardless

---

## Setup Instructions

### Local Testing

1. **Start backend API:**
```bash
cd c:\EVisionBetCode
python -m uvicorn backend_api:app --reload --port 8000
```

2. **Test in browser:**
```
http://localhost:3000/admin
Password: admin123
```

3. **Or test API directly:**
```bash
# Get token
curl -X POST "http://localhost:8000/api/admin/auth?password=admin123"

# Use token to download (replace TOKEN)
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/admin/ev-opportunities-csv \
     > my_ev_data.csv
```

### Production Deployment (Render)

1. **Ensure DATABASE_URL is set** in Render environment
   - Format: `postgresql://user:pass@host/dbname`
   - Should already be configured

2. **Set admin password** (optional):
   ```bash
   # Generate SHA256 hash of your password
   python -c "import hashlib; print(hashlib.sha256(b'mypassword').hexdigest())"
   
   # Add to Render env vars:
   ADMIN_PASSWORD_HASH=your_hash_here
   ```

3. **No other changes needed!**
   - Render will use updated code on next deployment
   - Cron jobs continue running every 30 min
   - Data auto-written to database

---

## Data Flow

```
Timeline (UTC):
00:00 - extract_odds.py runs
        → Fetches odds from API
        → Writes raw_odds to live_odds table
        → Outputs raw_odds_pure.csv

00:05 - calculate_opportunities.py runs
        → Reads raw_odds_pure.csv
        → Calculates fair odds
        → Detects EV opportunities
        → Writes to ev_opportunities table
        → Outputs ev_opportunities.csv

Anytime - Admin visits /admin
        → Views live database stats
        → Downloads CSV from database
        → Works on any computer
```

---

## CSV Format

### EV Opportunities CSV
```
sport,event_id,away_team,home_team,commence_time,market,point,selection,player,
fair_odds,best_odds,best_book,ev_percent,sharp_book_count,implied_prob,stake,kelly_fraction,detected_at

basketball_nba,event123,Phoenix,LA,2025-12-11T18:00:00,h2h,,Phoenix,,8.59,9.50,Sportsbet,10.65%,12,..
```

### Raw Odds CSV
```
sport,event_id,commence_time,market,point,selection,bookmaker,odds

basketball_nba,event123,2025-12-11T18:00:00,h2h,,Phoenix,Sportsbet,9.50
basketball_nba,event123,2025-12-11T18:00:00,h2h,,Phoenix,Betfair_EU,8.80
```

---

## Security Notes

⚠️ **For local/testing:** Default password `admin123` is fine

🔒 **For production:** Change the password!

```bash
# Change password:
1. Generate new hash:
   python -c "import hashlib; print(hashlib.sha256(b'YOUR_SECURE_PASSWORD').hexdigest())"

2. Set in Render environment:
   ADMIN_PASSWORD_HASH=<your_hash>

3. Only you know the password - share carefully!
```

**Token Security:**
- Tokens expire after 1 hour
- Only valid for CSV download endpoints
- Required for all admin endpoints

---

## Monitoring

**Check database stats anytime:**
```bash
curl -H "Authorization: Bearer <TOKEN>" \
     https://your-api.render.com/api/admin/database-stats
```

**Expected response:**
```json
{
  "ev_opportunities": {
    "count": 51,
    "latest_update": "2025-12-11T12:22:56.789Z"
  },
  "live_odds": {
    "count": 2316,
    "latest_update": "2025-12-11T12:05:18.456Z"
  },
  "price_history": {
    "count": 0
  }
}
```

---

## Next Steps

### Optional Enhancements:

1. **Add rate limiting** to admin endpoints
   ```python
   from slowapi import Limiter
   limiter.limit("10/minute")(admin_auth)
   ```

2. **Add audit logging** - Track who downloads what
   ```python
   # Log download with timestamp
   log_admin_action(user_ip, action, timestamp)
   ```

3. **Email notifications** - Get alerted when high EV found
   ```python
   if ev_percent > 5.0:
       send_email(f"High EV found: {ev_percent}%")
   ```

4. **Scheduled exports** - Auto-email CSV daily
   ```bash
   # Add cron job on Render
   0 18 * * * python send_admin_email.py
   ```

5. **Database-only** - Remove CSV files, query database always
   ```python
   # Stop writing raw_odds_pure.csv
   # Frontend fetches from /api/odds/latest endpoint
   ```

---

## Troubleshooting

**❌ "Invalid password"**
- Check spelling (case-sensitive)
- Default is `admin123`
- If changed, verify ADMIN_PASSWORD_HASH env var

**❌ "Unauthorized - missing token"**
- Must log in first to get token
- Token header format: `Authorization: Bearer <token>`

**❌ "Database connection failed"**
- Check DATABASE_URL is set in Render
- Should be `postgresql://...` format
- Pipeline still works (CSV written as backup)

**❌ CSV download shows 0 rows**
- Wait for cron job to run
- Check database stats to see record count
- If count is 0, pipeline hasn't written yet

---

## Summary

✅ **You now have:**
1. Full database-first architecture (Option C)
2. Admin page with secure login
3. Real-time CSV downloads from database
4. Works on any computer
5. Automatic pipeline every 30 minutes
6. Backup CSV files for safety

📊 **Admin workflow:**
1. Visit `/admin`
2. Login with password
3. View database stats
4. Download CSV
5. Analyze offline

🚀 **Ready for production!**

---

## Git Commits

- `f1eb667` - Option C: Admin/Designer CSV Download Dashboard (Backend)
- `756527e` - Option C: Admin/Designer CSV Download Dashboard (Frontend)

Both pushed to GitHub ✅
