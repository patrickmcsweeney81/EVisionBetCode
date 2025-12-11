## 🚀 Option C Admin Dashboard - Quick Start

### Access the Admin Panel

**URL:** `http://localhost:3000/admin` (local) or `https://your-app.com/admin` (production)

**Password:** `admin123` (default)

---

### What You Can Do

1. **Login** - Click login with password
2. **View Stats** - See how many EV opportunities in database
3. **Download EV CSV** - Get all EV opportunities as downloadable file
4. **Download Raw Odds CSV** - Get latest odds extraction as downloadable file
5. **Works Anywhere** - No special software needed, works on any computer

---

### The Pipeline (Automatic)

```
Every 30 minutes:
1. extract_odds.py → Fetch odds from API → Write to database
2. calculate_opportunities.py → Calculate EV → Write to database
3. Your CSVs are generated from database, not files
```

---

### How Option C Works

```
Traditional:        CSV file sync between services
                   ↓
Option C:           Database is single source of truth
                   ↓
Admin downloads:    PostgreSQL → CSV (on demand)
                   ↓
Works anywhere:     Any computer with internet access
```

---

### File Changes Made

**Backend (`backend_api.py`):**
- Added `/api/admin/auth` - Login endpoint
- Added `/api/admin/ev-opportunities-csv` - Download EV data
- Added `/api/admin/raw-odds-csv` - Download odds data
- Added `/api/admin/database-stats` - View database stats

**Frontend (`AdminPanel.js`):**
- Login form with password
- Database statistics display
- Download buttons
- Mobile responsive design

**Pipeline (`calculate_opportunities.py`):**
- Now writes to PostgreSQL database
- Enabled option C workflow

---

### Testing Locally

```bash
# 1. Start backend
cd c:\EVisionBetCode
python -m uvicorn backend_api:app --reload --port 8000

# 2. Start frontend (separate terminal)
cd c:\EVisionBetSite\frontend
npm start

# 3. Visit http://localhost:3000/admin
# 4. Login with admin123
# 5. Download CSV button
```

---

### Change Admin Password (Production)

```bash
# 1. Generate SHA256 hash of new password
python -c "import hashlib; print(hashlib.sha256(b'mynewpassword').hexdigest())"

# 2. Copy the output hash

# 3. Add to Render environment variables:
ADMIN_PASSWORD_HASH=<your_hash_here>

# 4. Done! New password is active
```

---

### Database Statistics

When you login, you see:
- **EV Opportunities:** How many EV opportunities found
- **Raw Odds Rows:** How many odds from all bookmakers
- **Last Updated:** When each was last updated

---

### CSV Format

**EV Opportunities CSV:**
- Sport, Event ID, Teams, Market, Selection, Player
- Fair Odds, Best Odds, Best Book, EV%
- Sharp Book Count, Implied Probability
- Stake, Kelly Fraction, Detection Time

**Raw Odds CSV:**
- Sport, Event ID, Market, Selection
- Bookmaker Name, Odds
- Latest extraction from API

---

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid password" | Default is `admin123`, check spelling |
| "No data showing" | Wait for cron job to run (every 30 min) |
| Database not connected | Check DATABASE_URL env var is set |
| CSV shows 0 rows | Pipeline hasn't run yet, wait 30 min |

---

### What's Better About Option C

✅ Single source of truth (database)  
✅ No file syncing between services  
✅ Real-time data  
✅ Download from anywhere  
✅ Scalable for multiple admins  
✅ Database backup of all data  

---

### Commits

```
70809a9 - 📖 Add Option C admin dashboard documentation
f1eb667 - ✨ Option C: Admin/Designer CSV Download Dashboard (backend)
756527e - ✨ Option C: Admin/Designer CSV Download Dashboard (frontend)
```

All pushed to GitHub ✅

---

**Questions?** Check OPTION_C_ADMIN_DASHBOARD.md for detailed setup
