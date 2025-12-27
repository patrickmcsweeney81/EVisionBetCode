# Quick Action Plan - Efficiency Optimization

**Created:** December 27, 2025  
**Time to Complete:** ~30 minutes  
**Expected Time Savings:** 20+ minutes per dev session

---

## 🎯 5 Actions to Implement Right Now

### 1. Disable Conflicting Prettier (2 minutes)

**Why:** Two formatters cause config conflicts

**Steps:**
1. Open VS Code Extensions (`Ctrl+Shift+X`)
2. Search: `prettier-standard`
3. Click "Disable"
4. Keep `esbenp.prettier-vscode` active

**Verify:**
```powershell
# In terminal, save a Python file with bad formatting
# Should auto-format with Black (not affected)
```

---

### 2. Set Up Thunder Client (10 minutes)

**Why:** Save 30 seconds per API test

**Steps:**

1. **In VS Code:** Open Thunder Client (left sidebar)
2. **Create Collection:**
   - Click "Collections" → "+"
   - Name: `EVisionBet Local`
   - Save

3. **Add 4 Requests:**

   **Request 1: Health Check**
   - Method: `GET`
   - URL: `http://localhost:8000/health`
   - Save as: `Health Check`

   **Request 2: Raw Odds**
   - Method: `GET`
   - URL: `http://localhost:8000/api/odds/raw?limit=10`
   - Save as: `Get Raw Odds (10)`

   **Request 3: EV Hits**
   - Method: `GET`
   - URL: `http://localhost:8000/api/ev/hits?limit=5`
   - Save as: `Get EV Hits (5)`

   **Request 4: Bookmakers**
   - Method: `GET`
   - URL: `http://localhost:8000/api/bookmakers`
   - Save as: `Get Bookmakers`

4. **Test One:**
   - Click "Health Check"
   - Click Send
   - Should see `{"status": "ok"}` response

**Use in Future:**
- API not responding? Click `Health Check` → Send (2 clicks, 1 sec)
- Need test data? Click `Get Raw Odds (10)` → Send (fast verification)

---

### 3. Enable Settings Sync (5 minutes)

**Why:** Backup extensions/settings to cloud + easy team sharing

**Steps:**

1. Click **Gear icon** (bottom left) → **"Sign in with GitHub"**
2. Authorize VS Code to access GitHub account
3. Click **Gear icon** again → **"Turn on Settings Sync"**
4. Choose what to sync (default: Extensions + Settings + Keybindings)
5. Done!

**Benefits:**
- Extensions auto-install on new machine
- Settings auto-apply (Python path, formatting rules, etc.)
- Share "Settings Profile" with team as `.json`

**Team Use:**
```
1. New dev clones repo
2. Opens VS Code
3. Signs in with GitHub
4. All 42 extensions auto-install
5. All settings auto-apply
No manual setup needed!
```

---

### 4. Add Test & Pipeline Keybindings (5 minutes)

**Why:** Run commands with 2 keys instead of mouse clicks

**Steps:**

1. **Open Keybindings:**
   - Press `Ctrl+K Ctrl+S`
   - Or: Gear icon → Keyboard Shortcuts

2. **Search and Bind:**

   | Keybinding | Command | Action |
   |-----------|---------|--------|
   | `Ctrl+Shift+T` | `workbench.action.tasks.runTask` → `"test"` | Run pytest |
   | `Ctrl+Shift+P` then `>Pipeline: Extract` | (already in tasks.json) | Run NBA extraction |

3. **Or edit directly in `keybindings.json`:**
   ```json
   [
     {
       "key": "ctrl+shift+t",
       "command": "workbench.action.tasks.runTask",
       "args": "Python: Run Tests"
     },
     {
       "key": "ctrl+shift+e",
       "command": "workbench.action.tasks.runTask",
       "args": "Pipeline: Extract Odds"
     },
     {
       "key": "ctrl+shift+c",
       "command": "workbench.action.tasks.runTask",
       "args": "Pipeline: Calculate EV"
     }
   ]
   ```

4. **Test:**
   - Press `Ctrl+Shift+T` → Pytest runs
   - Press `Ctrl+Shift+E` → NBA extraction starts

---

### 5. Create VS Code Profile for Team (5 minutes)

**Why:** One-click onboarding for new developers

**Steps:**

1. **Create Profile:**
   - Click **Gear icon** → **Profiles** → **Create Profile**
   - Name: `EVisionBet Development`

2. **Profile Settings:**
   - Extensions: All 42 installed (auto-included)
   - Settings: Current Python/formatting rules (auto-included)
   - Keybindings: Custom keybindings from step 4 (auto-included)
   - Snippets: None needed (already in extensions)

3. **Export Profile:**
   - Click Profile → **Export Profile**
   - Save as: `EVisionBet-Dev-Profile.json`
   - Add to repo: `docs/vscode-profile.json`

4. **Team Use:**
   ```
   New dev receives link or file
   Opens VS Code
   Profiles → Import Profile
   Selects EVisionBet-Dev-Profile.json
   All extensions + settings auto-configured
   Dev is ready in 30 seconds!
   ```

---

## 📋 Bonus: Document Quick Reference

**Create:** `V3_DAILY_COMMANDS.md`

```markdown
# EVisionBet - Daily Commands (Copy & Paste)

## Start All Services
Terminal 1:
cd C:\EVisionBetCode
.\.venv\Scripts\Activate.ps1
uvicorn backend_api:app --reload

Terminal 2:
cd C:\EVisionBetSite\frontend
npm start

Terminal 3:
cd C:\EVisionBetCode
.\.venv\Scripts\Activate.ps1

## Quick Pipeline Runs
# Extract NBA (fresh data)
python pipeline_v3.py --sports basketball_nba

# Calculate EV opportunities
python src/pipeline_v2/calculate_opportunities.py

# Run all tests
pytest --cov

# Format all code
black src/

# Check code quality
flake8 src/

# Merge NBA to all_raw.csv
python merge_to_all_raw.py basketball_nba

## API Testing (in Thunder Client or Terminal 3)
# Test health
curl http://localhost:8000/health

# Get raw odds
curl "http://localhost:8000/api/odds/raw?limit=5"

# Get EV hits
curl "http://localhost:8000/api/ev/hits?limit=5"

## File Paths
Data extracts: C:\EVisionBetCode\data\v3\extracts\
Config: C:\EVisionBetCode\src\v3\configs\
Backend: C:\EVisionBetCode\backend_api.py
Frontend: C:\EVisionBetSite\frontend\src\

## Troubleshooting
# Backend won't start?
Check port 8000: netstat -ano | findstr 8000

# Frontend issues?
rm -r node_modules && npm install

# Python path wrong?
python -c "import sys; print(sys.executable)"

# Database error?
Check .env has DATABASE_URL set
```

---

## ⏱️ Implementation Schedule

**Right Now (2-3 minutes):**
✅ Disable Prettier Standard

**Next 10 minutes:**
✅ Configure Thunder Client

**Next 5 minutes:**
✅ Enable Settings Sync (GitHub sign-in)

**Next 5-10 minutes:**
✅ Add keybindings for test/pipeline

**Whenever convenient:**
✅ Create VS Code Profile
✅ Document daily commands

---

## 🎯 Expected Benefits

| Task | Before | After | Savings |
|------|--------|-------|---------|
| API test | Browser → type URL | Thunder Client click | 30 sec |
| Test run | Menu → Run tests | Ctrl+Shift+T | 15 sec |
| Pipeline | Type full command | Ctrl+Shift+E | 10 sec |
| Team onboarding | 45 min setup | 30 sec profile import | 44 min 30 sec |
| Multi-machine setup | 30 min install | Auto-sync from cloud | 30 min |

**Per development session:** ~1 minute saved × 10 test cycles = 10 minutes  
**Per week:** ~1 hour saved  
**Per month:** ~4-5 hours saved

---

## ✅ Verification

After all steps, you should see:

- [ ] **Extensions:** No "Prettier Standard" in list
- [ ] **Thunder Client:** 4 requests in "EVisionBet Local" collection
- [ ] **Settings Sync:** Cloud icon lit up (top right)
- [ ] **Keybindings:** `Ctrl+Shift+T` runs tests
- [ ] **Profile:** Exportable as `.json` from Profiles menu
- [ ] **Commands:** Documented in markdown file

---

## 🚀 When Done

You'll have:
- ✅ Clean extension setup (no conflicts)
- ✅ 2-click API testing
- ✅ 2-key command shortcuts
- ✅ Team-shareable environment
- ✅ Documented daily workflows
- ✅ +1 hour productivity per week

**Grade: A++ environment ready for production development**

