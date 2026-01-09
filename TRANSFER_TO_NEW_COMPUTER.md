# 🚀 BEST WAY TO TRANSFER EVISIONBET TO NEW COMPUTER

## Executive Summary

**Recommended:** Git clone + 15-minute setup  
**Time:** ~15 minutes total setup  
**Effort:** Minimal (all code in GitHub, just install dependencies locally)

---

## Three Transfer Options

### **Option 1: Git Clone (RECOMMENDED) ✅**
**Best for:** New development, staying current with latest code  
**Time:** 15 minutes  
**Steps:** Git clone 2 repos + pip/npm install + create .env

```powershell
# 1. Clone backend
git clone https://github.com/patrickmcsweeney81/EVisionBetCode.git

# 2. Clone frontend
git clone https://github.com/patrickmcsweeney81/EVisionBetSite.git

# 3. Setup Python (EVisionBetCode)
cd EVisionBetCode
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
echo ODDS_API_KEY=your_key > .env

# 4. Setup Node (EVisionBetSite/frontend)
cd ../EVisionBetSite/frontend
npm install

# 5. Done! Run the pipeline
cd ../../EVisionBetCode
python run_nba_pipeline.py --extract
```

**Pros:**
- ✅ Full commit history
- ✅ Easy to pull latest updates (`git pull`)
- ✅ Can push changes back
- ✅ Smallest transfer size (no binaries)
- ✅ Standard workflow

**Cons:**
- Need Git installed

---

### **Option 2: GitHub Export + Manual Install**
**Best for:** Offline transfer, archival  
**Time:** 20 minutes

```powershell
# On GitHub: Click "Code" → "Download ZIP"
# Extract both zips to folders
# Run setup steps from Option 1 (skip git clone)
```

**Pros:**
- ✅ No Git needed
- ✅ Still uses GitHub source

**Cons:**
- ❌ No commit history
- ❌ Can't push changes back
- ❌ Manual update process

---

### **Option 3: Copy Entire Folder (NOT RECOMMENDED)**
**Best for:** Emergency backup, offline transfer  
**Time:** 5 minutes transfer + 10 minutes cleanup

```powershell
# Copy C:\EVisionBetCode and C:\EVisionBetSite to new machine
# Delete .venv/ and node_modules/ (they're large + machine-specific)
# Run: python -m venv .venv && pip install -e ".[dev]"
# Run: npm install in frontend/
```

**Pros:**
- ✅ Fastest initial copy

**Cons:**
- ❌ Carries machine-specific files (.venv, node_modules)
- ❌ Have to delete and rebuild anyway
- ❌ No clean git history
- ❌ Hard to sync updates

---

## ⭐ RECOMMENDED: Option 1 (Git Clone)

### Why Git Clone is Best

1. **Smallest transfer:** Only code files (~100 MB), not binaries  
2. **Clean setup:** Fresh .venv and node_modules on new machine  
3. **Version control:** Full commit history, easy to track changes  
4. **Updates:** Simple `git pull` to get latest code  
5. **Standard workflow:** How professional teams work  

### Step-by-Step Git Clone Setup

#### Prerequisites Check
```powershell
# Verify Git installed
git --version

# Verify Python 3.10+
python --version

# Verify Node.js 16+
node --version
```

#### Part 1: Clone Backend (2 min)
```powershell
# Create workspace
mkdir C:\EVisionWorkspace
cd C:\EVisionWorkspace

# Clone repo
git clone https://github.com/patrickmcsweeney81/EVisionBetCode.git
cd EVisionBetCode

# Verify clone
git log --oneline | head -5  # Should show commit history
```

#### Part 2: Setup Python (5 min)
```powershell
# Create venv
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies (from pyproject.toml)
pip install -e ".[dev]"

# Verify (should show no errors)
python -c "import pandas; import fastapi; print('✓ All packages installed')"
```

#### Part 3: Add API Key
```powershell
# Get key from: https://the-odds-api.com/
# Go to: Pricing & Account → API Key (free tier is 500/month)

# Create .env file
echo ODDS_API_KEY=your_actual_key_here > .env

# Verify (should show your key)
Get-Content .env
```

#### Part 4: Clone Frontend (2 min)
```powershell
# Navigate to parent
cd C:\EVisionWorkspace

# Clone frontend
git clone https://github.com/patrickmcsweeney81/EVisionBetSite.git
cd EVisionBetSite/frontend

# Install Node packages
npm install

# Verify
npm list react
```

#### Part 5: Test Everything (3 min)
```powershell
# Backend test
cd C:\EVisionWorkspace\EVisionBetCode
.\.venv\Scripts\Activate.ps1
python run_nba_pipeline.py --extract  # Should show "✅ All 4 stages completed"

# Frontend test (new terminal)
cd C:\EVisionWorkspace\EVisionBetSite\frontend
npm start  # Should open http://localhost:3000
```

---

## 📊 Transfer Time Breakdown

| Phase | Time | What Happens |
|-------|------|-------------|
| **Download Git repos** | 2 min | Clone EVisionBetCode + EVisionBetSite |
| **Python setup** | 5 min | Create .venv, install dependencies (pandas, fastapi, etc.) |
| **Create .env** | 1 min | Add API key |
| **Frontend setup** | 4 min | npm install (installs React, TypeScript, etc.) |
| **Test pipeline** | 3 min | Run `python run_nba_pipeline.py --extract` |
| **Total** | **15 min** | Ready to code! |

---

## 🔄 After Transfer: Keep in Sync

### Pull Latest Code
```powershell
cd C:\EVisionWorkspace\EVisionBetCode
git pull

cd C:\EVisionWorkspace\EVisionBetSite
git pull
```

### Push Your Changes
```powershell
git add .
git commit -m "Your changes"
git push
```

### Revert to Latest
```powershell
git reset --hard origin/main
```

---

## 📦 What Gets Transferred

### Option 1 (Git Clone) - What's Copied
```
✅ Source code (.py, .js, .ts files)
✅ Configuration (pyproject.toml, package.json)
✅ Documentation (README.md, PATS_FILE.md)
✅ Tests (test_pairing.py)
✅ Git history (.git folder)
❌ .venv/ (created fresh on new machine)
❌ node_modules/ (created fresh on new machine)
❌ .env (you create with your API key)
❌ data/ (created by pipeline)
```

### What You Install Locally
```
🔧 Python 3.10+
🔧 Node.js 16+
🔧 Git
🔧 pip dependencies (pandas, fastapi, networkx, etc.)
🔧 npm dependencies (react, typescript, etc.)
🔧 Your API key (ODDS_API_KEY)
```

---

## ✅ Verification After Transfer

```powershell
# 1. Backend dependencies installed
cd EVisionBetCode
.\.venv\Scripts\Activate.ps1
pip list | findstr fastapi

# 2. Frontend dependencies installed
cd ../EVisionBetSite/frontend
npm list react

# 3. Python can import key packages
python -c "import pandas, fastapi, networkx; print('✓')"

# 4. API starts
uvicorn backend_api:app --reload
# Should say: "Application startup complete"

# 5. Pipeline runs
python run_nba_pipeline.py --extract
# Should say: "All 4 stages completed successfully"

# 6. Frontend loads
npm start
# Should open browser to http://localhost:3000
```

---

## 🆘 If Something Goes Wrong

### Git clone fails
```powershell
# Try with HTTPS instead
git clone https://github.com/patrickmcsweeney81/EVisionBetCode.git

# Or SSH (if configured)
git clone git@github.com:patrickmcsweeney81/EVisionBetCode.git
```

### Python install fails
```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Try install again
pip install -e ".[dev]"

# If still fails, install manually
pip install pandas fastapi uvicorn networkx pytest
```

### npm install fails
```powershell
# Clear cache
npm cache clean --force

# Delete and retry
rm package-lock.json
npm install
```

### API key missing
```powershell
# Check .env file exists
Get-Content .env

# Should show: ODDS_API_KEY=your_key

# If missing, create it
echo ODDS_API_KEY=your_key_from_the_odds_api_com > .env
```

---

## 🎯 Quick Checklist for New Machine

- [ ] Git installed (`git --version`)
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Node.js installed (`node --version`)
- [ ] Cloned EVisionBetCode
- [ ] Cloned EVisionBetSite
- [ ] Created Python venv (`.venv\Scripts\Activate.ps1`)
- [ ] Installed pip dependencies (`pip install -e ".[dev]"`)
- [ ] Created .env with ODDS_API_KEY
- [ ] Installed npm dependencies (`npm install`)
- [ ] Pipeline runs (`python run_nba_pipeline.py --extract`)
- [ ] Backend starts (`uvicorn backend_api:app --reload`)
- [ ] Frontend starts (`npm start`)

---

## 📚 Key Files on New Machine

After transfer, you'll have:

```
C:\EVisionWorkspace\
  EVisionBetCode\
    ├── NEW_COMPUTER_SETUP.md ← Detailed setup guide
    ├── README.md ← Full documentation
    ├── PATS_FILE.md ← Current status
    ├── PAIRING_IMPLEMENTATION_SUMMARY.md ← Latest features
    ├── filter_nba_v3.py ← Composite Key pairing (NEW)
    ├── test_pairing.py ← 8 pytest tests (NEW)
    ├── run_nba_pipeline.py ← Orchestrator
    ├── backend_api.py ← FastAPI server
    └── .env ← You create this with API key
    
  EVisionBetSite\
    frontend\
      ├── src/ ← React components
      ├── package.json ← Dependencies
      └── README.md
```

---

## 🚀 After Transfer: First Day

```powershell
# Day 1: Get everything running

# Terminal 1: Backend API
cd C:\EVisionWorkspace\EVisionBetCode
.\.venv\Scripts\Activate.ps1
uvicorn backend_api:app --reload

# Terminal 2: Frontend (new terminal)
cd C:\EVisionWorkspace\EVisionBetSite\frontend
npm start

# Terminal 3: Fresh data (optional, new terminal)
cd C:\EVisionWorkspace\EVisionBetCode
.\.venv\Scripts\Activate.ps1
python run_nba_pipeline.py --extract

# Visit http://localhost:3000 → Should show EV opportunities!
```

---

## 💡 Pro Tips

1. **Use VS Code** - Open both EVisionBetCode and EVisionBetSite folders in workspace
2. **Keep .env secret** - Don't commit it to GitHub (it's in .gitignore)
3. **Pull updates often** - `git pull` in both repos to stay current
4. **Run tests** - `pytest test_pairing.py -v` to verify pairing logic
5. **Fresh data** - Run `python run_nba_pipeline.py --extract` daily for latest odds

---

## ✨ You're Ready!

**Option 1 (Git Clone) is the best way.** It's fast, clean, and keeps you synced with the latest code.

**Time required: 15 minutes**  
**Effort required: Minimal**  
**Result: Fully functional EVisionBet on new machine**

Any questions? Check NEW_COMPUTER_SETUP.md or README.md in the repo!
