# 🗂️ Archive Analysis - December 14, 2025

This document identifies files that can be archived in both EVisionBetCode and EVisionBetSite repositories.

---

## 📋 EVisionBetCode Repository

### ✅ Active/Essential Files (DO NOT ARCHIVE)
- `backend_api.py` - Main FastAPI server
- `src/pipeline_v2/` - Active data pipeline
- `tests/` - Test suite
- `README.md` - Main documentation
- `Makefile` - Development tasks
- `pyproject.toml` - Package configuration
- `requirements/` & `requirements.txt` - Dependencies
- `.github/AI_AGENT_GUIDE.md` - AI agent instructions
- `VSCODE_SETUP.md` - Setup guide
- `DOCUMENTATION_GUIDE.md` - Documentation index
- `RENDER_DEPLOYMENT.md` - Deployment guide
- `OPTIMIZATION_GUIDE.md` - Performance guide
- `docs/BUGFIX_FAIR_ODDS_DEC10_2025.md` - Important bug history
- `docs/PRODUCT_PLAN.md` - Product roadmap
- `docs/TWO_STAGE_PIPELINE.md` - Architecture doc
- `data/ev_opportunities.csv` - Latest output
- `data/raw_odds_pure.csv` - Latest raw data
- `data/market_discovery.json` - Market metadata

### 🗃️ Files to Archive

#### 1. Database Setup Scripts (One-Time Use, Obsolete)
**Reason:** These were used for initial database setup. Tables are now created and maintained via migrations or ORM.
- `setup_database.py` (93 lines) - Initial table creation
- `run_create_tables.py` - One-time setup script
- `create_tables.sql` - Raw SQL schema
- `create_tables_enhanced.sql` - Enhanced schema
- `verify_database.py` (94 lines) - Initial verification script

**Action:** Move to `archive/database_setup/`

#### 2. Discovery/Exploration Scripts (One-Time Use)
**Reason:** Market discovery was completed. Results stored in `data/market_discovery.json`.
- `discover_markets.py` (170 lines) - Market discovery script

**Action:** Move to `archive/exploration/`

#### 3. Old Timestamped Data Files (Historical Data)
**Reason:** Outdated extractions. Latest data is in `raw_odds_pure.csv`.
- `data/raw_odds_pure_20251213T103747.csv`
- `data/raw_odds_pure_20251213T110105.csv`
- `data/raw_odds_pure_20251213T125036.csv`
- `data/raw_odds_pure_20251214T095336.csv`

**Action:** Move to `archive/old_data/`

#### 4. Status/Completion Documentation (Historical)
**Reason:** Session-specific completion notes. Superseded by current documentation suite.
- `CLEANUP_NOTES_DEC13_2025.md`
- `CODE_REVIEW_FIXES_DEC13.md`
- `COMPLETION_SUMMARY_DEC13.md`
- `STATUS_DOCUMENTATION_COMPLETE_DEC13.md`
- `BACKEND_API_DEPLOYMENT.md` (superseded by RENDER_DEPLOYMENT.md)

**Action:** Move to `archive/session_notes/`

---

## 📋 EVisionBetSite Repository

### ✅ Active/Essential Files (DO NOT ARCHIVE)
- `frontend/src/` - React application source
- `frontend/public/` - Static assets
- `frontend/build/` - Production build
- `README.md` - Main documentation
- `VSCODE_SETUP.md` - Setup guide
- `DEVELOPMENT.md` - Development workflow
- `STARTUP_CHECKLIST.md` - Daily checklist
- `PROJECT_SUMMARY.md` - Project overview
- `DOCUMENTATION_INDEX.md` - Doc navigation
- `SESSION_COMPLETION.md` - Latest session summary
- `render.yaml` - Render deployment config
- `netlify.toml` - Netlify config
- `package.json` - Dependencies
- `scripts/` - Logo management scripts
- `docs/ARCHITECTURE.md` - Architecture doc
- `docs/PROJECT_PLAN.md` - Project plan
- `docs/LOGO_APIS.md` - Logo API reference

### 🗃️ Files to Archive

#### 1. Deployment-Related (Historical/Unused)
**Reason:** Currently deployed on Render, not using Netlify or Heroku.
- `Procfile` - Heroku deployment (not using Heroku)
- `requirements.txt` - Python dependencies (backend is in separate repo)

**Action:** Move to `archive/deployment_configs/`

#### 2. Frontend Setup Documentation (Superseded)
**Reason:** Replaced by comprehensive documentation suite (VSCODE_SETUP.md, DEVELOPMENT.md, STARTUP_CHECKLIST.md).
- `FRESH_DATA_DIAGNOSTIC.md` - Troubleshooting guide (superseded)
- `FRONTEND_SETUP_ACTION_PLAN.md` - Old setup plan
- `FRONTEND_SETUP_NEXT_STEPS.md` - Old next steps
- `FRONTEND_VSCODE_SETUP.md` - Superseded by VSCODE_SETUP.md
- `LOGO_API_QUICKREF.md` - Quick ref (details in docs/LOGO_APIS.md)

**Action:** Move to `archive/old_docs/`

#### 3. Test/Debug Files (Development Artifacts)
**Reason:** Test HTML for API fetch testing. Not part of production.
- `test_api_fetch.html` - API testing page

**Action:** Move to `archive/testing/`

#### 4. Deployment Documentation (Obsolete)
**Reason:** Superseded by current deployment workflow (render.yaml + GitHub auto-deploy).
- `DEPLOYMENT.md` - Old deployment guide (if not linked from current docs)

**Action:** Move to `archive/deployment_configs/` (if obsolete)

---

## 📊 Archive Summary

### EVisionBetCode
| Category | Files | Action |
|----------|-------|--------|
| Database Setup Scripts | 5 files | → `archive/database_setup/` |
| Discovery Scripts | 1 file | → `archive/exploration/` |
| Old Data Files | 4 CSV files | → `archive/old_data/` |
| Session Notes | 5 MD files | → `archive/session_notes/` |
| **Total** | **15 files** | |

### EVisionBetSite
| Category | Files | Action |
|----------|-------|--------|
| Deployment Configs | 2 files | → `archive/deployment_configs/` |
| Old Documentation | 5 MD files | → `archive/old_docs/` |
| Test Files | 1 HTML file | → `archive/testing/` |
| **Total** | **8 files** | |

---

## 🎯 Archive Structure

### EVisionBetCode/archive/
```
archive/
├── database_setup/
│   ├── setup_database.py
│   ├── run_create_tables.py
│   ├── create_tables.sql
│   ├── create_tables_enhanced.sql
│   └── verify_database.py
├── exploration/
│   └── discover_markets.py
├── old_data/
│   ├── raw_odds_pure_20251213T103747.csv
│   ├── raw_odds_pure_20251213T110105.csv
│   ├── raw_odds_pure_20251213T125036.csv
│   └── raw_odds_pure_20251214T095336.csv
├── session_notes/
│   ├── CLEANUP_NOTES_DEC13_2025.md
│   ├── CODE_REVIEW_FIXES_DEC13.md
│   ├── COMPLETION_SUMMARY_DEC13.md
│   ├── STATUS_DOCUMENTATION_COMPLETE_DEC13.md
│   └── BACKEND_API_DEPLOYMENT.md
└── [existing archive/ files remain]
```

### EVisionBetSite/archive/
```
archive/
├── deployment_configs/
│   ├── Procfile
│   └── requirements.txt
├── old_docs/
│   ├── FRESH_DATA_DIAGNOSTIC.md
│   ├── FRONTEND_SETUP_ACTION_PLAN.md
│   ├── FRONTEND_SETUP_NEXT_STEPS.md
│   ├── FRONTEND_VSCODE_SETUP.md
│   └── LOGO_API_QUICKREF.md
└── testing/
    └── test_api_fetch.html
```

---

## ✅ Benefits of Archiving

1. **Cleaner Repository**
   - Easier to navigate root directories
   - Clear distinction between active and historical files

2. **Preserved History**
   - All work documented and accessible
   - Can reference old scripts if needed
   - Git history intact

3. **Better Onboarding**
   - New developers see only relevant files
   - Documentation index clearer
   - Less confusion about what to read

4. **Maintained Context**
   - Archive preserves "why we did this"
   - Can recover scripts if needed
   - Historical decision documentation

---

## 🚀 Next Steps

1. **Review this analysis** - Confirm files can be archived
2. **Create archive folders** - Set up directory structure
3. **Move files** - `git mv` to preserve history
4. **Update references** - Check for broken links
5. **Commit changes** - Clear commit message
6. **Update .gitignore** - Exclude old data files pattern

---

## ⚠️ Important Notes

- **DO NOT DELETE** - Only move to archive folders
- **Preserve Git History** - Use `git mv` not `mv` + `git add`
- **Check Links** - Update any documentation references
- **Keep Archives** - Future reference and context
- **Test After** - Ensure nothing broke

---

**Created:** December 14, 2025  
**Purpose:** Organize repositories by archiving obsolete/historical files  
**Status:** Ready for review and execution
