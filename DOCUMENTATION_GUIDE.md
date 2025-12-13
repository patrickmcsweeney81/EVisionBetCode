# 📚 EVisionBetCode Documentation Guide

This guide shows which documentation files are current and which are archival/outdated.

---

## ✅ Active Documentation (Keep & Use)

### Primary
- **[README.md](README.md)** – Main entry point, setup guide, common tasks
- **[VSCODE_SETUP.md](VSCODE_SETUP.md)** – VS Code configuration (extensions, interpreter, debugging)
- **[src/pipeline_v2/README.md](src/pipeline_v2/README.md)** – Pipeline architecture and design

### Deployment & Configuration
- **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)** – Render setup, services, env vars
- **[BACKEND_API_DEPLOYMENT.md](BACKEND_API_DEPLOYMENT.md)** – API endpoints, FastAPI config
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** – AI agent guidelines

### Technical Details
- **[docs/BUGFIX_FAIR_ODDS_DEC10_2025.md](docs/BUGFIX_FAIR_ODDS_DEC10_2025.md)** – Fair odds calculation
- **[docs/PRODUCT_PLAN.md](docs/PRODUCT_PLAN.md)** – Product overview & concepts

---

## 🗂️ Archive / Obsolete (Can Delete)

### Outdated Setup Guides (Superseded by [VSCODE_SETUP.md](VSCODE_SETUP.md) + [README.md](README.md))
- `docs/SETUP_GUIDE.md` – Old setup (replaced by VSCODE_SETUP.md)
- `QUICK_START.md` – Outdated (replaced by README.md Quick Start)
- `QUICK_REFERENCE.md` – Partial info (consolidated in README.md)
- `OPTION_C_QUICK_START.md` – Old option (irrelevant now)
- `OPTION_C_ADMIN_DASHBOARD.md` – Incomplete feature (remove)

### Deployment / Handoff Notes (History Only)
- `HANDOFF_DEC9_2025.md` – Handoff notes (archive)
- `HANDOVER_DEC10_2025.md` – Handover notes (archive)
- `DEPLOYMENT_CHECKLIST.md` – Old checklist (consolidate into RENDER_DEPLOYMENT.md)
- `DEPLOYMENT_COMPLETE.md` – Status note (remove)
- `SESSION_SUMMARY.md` – Session notes (archive)
- `UNCOMMITTED_CHANGES.md` – Status snapshot (remove)

### Feature Documentation (Experimental / Incomplete)
- `LINE_MOVEMENT_SETUP.md` – Experimental feature (incomplete)
- `LINE_MOVEMENT_COMPLETE.md` – Experimental feature (incomplete)
- `FRONTEND_INTEGRATION_GUIDE.md` – Partial integration (covered in README.md)
- `FRONTEND_BACKEND_INTEGRATION.md` – Partial integration (covered in README.md)

### Path Fix Notes (One-Time Issues)
- `RENDER_PATH_FIX_DEC11_2025.md` – One-time fix documentation (archive)

### Analysis / Reference Documents
- `docs/BOOK_WEIGHTS_INTEGRATION.md` – Legacy integration notes (reference only)
- `docs/BOOKMAKER_CSV_BUILD.md` – Legacy CSV building (reference only)
- `docs/RAW_ODDS_EXTRACTION.md` – Extraction details (covered in src/pipeline_v2/README.md)
- `docs/PROJECT_SETUP.md` – Old setup (replaced by VSCODE_SETUP.md)
- `docs/PROJECT_ANALYSIS_DEC2025.md` – Project analysis (reference only)
- `docs/BETFAIR_ANALYSIS.md` – Betfair bookmaker analysis (reference only)
- `docs/CLEANUP_REPORT_DEC2025.md` – Cleanup report (archival)
- `src/legacy/CLEANUP_SUMMARY_DEC9_2025.md` – Legacy cleanup notes (archive)
- `.github/agents/gitkracken.agent.md` – Agent file (system file, not user doc)

### Backend Deployment (Covered in RENDER_DEPLOYMENT.md)
- `DEPLOY_BACKEND_API.md` – Outdated (replaced by RENDER_DEPLOYMENT.md)
- `SYSTEM_ARCHITECTURE.md` – Old overview (replaced by pipeline README.md)
- `TEST_PLAN.md` – Old test plan (covered in README.md & make commands)

---

## 📋 Recommended Action Plan

### Phase 1: Consolidate Critical Docs (1-2 hours)
1. ✅ [VSCODE_SETUP.md](VSCODE_SETUP.md) – Created with complete setup
2. ✅ [README.md](README.md) – Rewritten with main guide
3. 🔄 Review & update [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) if needed
4. 🔄 Review & update [BACKEND_API_DEPLOYMENT.md](BACKEND_API_DEPLOYMENT.md) if needed

### Phase 2: Archive Old Docs (30 min)
Create folder: `docs/archive/` and move:
```
docs/archive/
├── BOOK_WEIGHTS_INTEGRATION.md
├── BOOKMAKER_CSV_BUILD.md
├── BETFAIR_ANALYSIS.md
├── PROJECT_ANALYSIS_DEC2025.md
├── CLEANUP_REPORT_DEC2025.md
├── etc.
```

### Phase 3: Delete Obsolete Files (15 min)
```bash
# Delete from root:
QUICK_START.md
QUICK_REFERENCE.md
OPTION_C_QUICK_START.md
OPTION_C_ADMIN_DASHBOARD.md
HANDOFF_DEC9_2025.md
HANDOVER_DEC10_2025.md
DEPLOYMENT_CHECKLIST.md
DEPLOYMENT_COMPLETE.md
SESSION_SUMMARY.md
UNCOMMITTED_CHANGES.md
LINE_MOVEMENT_SETUP.md
LINE_MOVEMENT_COMPLETE.md
FRONTEND_INTEGRATION_GUIDE.md
FRONTEND_BACKEND_INTEGRATION.md
RENDER_PATH_FIX_DEC11_2025.md
DEPLOY_BACKEND_API.md
SYSTEM_ARCHITECTURE.md
TEST_PLAN.md
README_OLD_DEC13.md

# Delete from docs/:
docs/SETUP_GUIDE.md
docs/RAW_ODDS_EXTRACTION.md
docs/PROJECT_SETUP.md
docs/FAIR_ODDS_CALCULATION.md

# Delete from src/:
src/legacy/CLEANUP_SUMMARY_DEC9_2025.md
```

---

## 📖 Reading Order (For New Users)

1. **[README.md](README.md)** (15 min) – Overview, quick start, common tasks
2. **[VSCODE_SETUP.md](VSCODE_SETUP.md)** (10 min) – Configure VS Code
3. **[src/pipeline_v2/README.md](src/pipeline_v2/README.md)** (20 min) – How pipeline works
4. **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)** (10 min, if deploying) – Deploy to Render
5. **[docs/BUGFIX_FAIR_ODDS_DEC10_2025.md](docs/BUGFIX_FAIR_ODDS_DEC10_2025.md)** (15 min, if curious) – EV math

**Total time:** ~70 minutes to full understanding

---

## 🔍 File Organization (After Cleanup)

```
EVisionBetCode/
├── README.md                           ← Main guide (start here)
├── VSCODE_SETUP.md                     ← VS Code config
├── RENDER_DEPLOYMENT.md                ← Deploy to Render
├── BACKEND_API_DEPLOYMENT.md           ← API endpoints
├── .github/copilot-instructions.md     ← AI agent rules
├── src/
│   └── pipeline_v2/
│       └── README.md                   ← Pipeline architecture
├── docs/
│   ├── BUGFIX_FAIR_ODDS_DEC10_2025.md ← EV calculation
│   ├── PRODUCT_PLAN.md                ← Product overview
│   └── archive/                        ← Historical docs
│       ├── BOOK_WEIGHTS_INTEGRATION.md
│       ├── BETFAIR_ANALYSIS.md
│       └── ... (10+ files)
└── data/
    └── (csv files, not docs)
```

---

## 🎯 Current Status

- ✅ **VSCODE_SETUP.md** created (complete with extensions, interpreter, debugging)
- ✅ **README.md** rewritten (clean, references VSCODE_SETUP.md)
- 🔄 **Pending:** Delete/archive obsolete files
- 🔄 **Pending:** Final review of RENDER_DEPLOYMENT.md

---

## 📝 Notes for Future Maintainers

- **Never commit `.env` file** – It's in `.gitignore`
- **Update README.md if changing pipeline behavior** – Keep docs in sync with code
- **Add to VSCODE_SETUP.md if adding new VS Code extensions** – Maintain complete setup guide
- **Archive old docs when creating new versions** – Don't delete, move to `docs/archive/`
- **Link to specific docs from README.md** – Help new users find what they need

---

**Created:** December 13, 2025  
**Purpose:** Organize and consolidate documentation for clarity and maintainability

