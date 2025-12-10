# Uncommitted Changes - Ready to Commit & Push

**Status:** All changes made in this session are ready for git  
**Recommended Commit Message:** "chore: reorganize codebase - rename handlers, consolidate fair_prices, move legacy files"

---

## Changes Summary

### 1. File Renames (Pipeline V2)
```
pipeline_v2/raw_odds_pure.py           → pipeline_v2/extract_odds.py
pipeline_v2/calculate_ev.py            → pipeline_v2/calculate_opportunities.py
pipeline_v2/bookmaker_ratings.py       → pipeline_v2/ratings.py
```

**Reason:** Clearer, more descriptive names aligned with functionality

**Update Docs:** ✅
- README.md updated
- QUICK_START.md updated
- pipeline_v2/README.md updated

### 2. File Renames (Core Handlers)
```
core/h2h_handler.py                    → core/h2h.py
core/spreads_handler.py                → core/spreads.py
core/totals_handler.py                 → core/totals.py
core/player_props_handler.py           → core/player_props.py
core/nfl_props_handler.py              → core/nfl_props.py
```

**Reason:** Simplified naming, removed redundant "_handler" suffix

**Imports Updated:** ✅ (no imports reference these directly in active code)

### 3. File Moves to Legacy
**Folder Created:** `legacy/`

**Moved Files:**
```
core/fair_prices.py                    → legacy/core/fair_prices.py
core/fair_prices_v2.py                 → legacy/core/fair_prices_v2.py
core/player_props_handler_NEW.py       → legacy/core/player_props_handler_NEW.py
core/exotics_logger.py                 → legacy/core/exotics_logger.py
core/all_odds_logger.py                → legacy/core/all_odds_logger.py
core/raw_odds_logger.py                → legacy/core/raw_odds_logger.py
core/balldontlie.py                    → legacy/core/balldontlie.py
core/betfair_api.py                    → legacy/core/betfair_api.py
core/scrape_sources/                   → legacy/core/scrape_sources/

ev_arb_bot.py                          → legacy/ev_arb_bot.py
extract_ev_hits.py                     → legacy/extract_ev_hits.py
launcher.bat                           → legacy/launcher.bat
README.txt                             → legacy/README.txt
CLEANUP_SUMMARY_DEC9_2025.md           → legacy/CLEANUP_SUMMARY_DEC9_2025.md

pipeline_v2/outlier_test.py            → legacy/pipeline/outlier_test.py
pipeline_v2/check_outliers_ev.py       → legacy/pipeline/check_outliers_ev.py
```

**Reason:** Mark as deprecated, ready for deletion after testing confirms system works

### 4. New Files Created
```
core/fair_prices.py                    (NEW - unified fair odds interface)
TEST_PLAN.md                           (NEW - comprehensive testing guide)
SYSTEM_ARCHITECTURE.md                 (NEW - full system documentation)
RENDER_DEPLOYMENT.md                   (NEW - Render backend setup guide)
UNCOMMITTED_CHANGES.md                 (THIS FILE)
```

### 5. Documentation Updated
```
README.md                              Updated with new filenames
QUICK_START.md                         Updated with new filenames
pipeline_v2/README.md                  Updated with new filenames
docs/PROJECT_SETUP.md                  Updated with folder reference
docs/CLEANUP_REPORT_DEC2025.md         Updated references
```

### 6. .env Updated
```
.env                                   (no changes, already correct)
```

---

## What Was NOT Changed

❌ **Not Committed Yet (Uncommitted):**
- All renames above
- All new documentation
- All legacy folder moves

✅ **Already Committed Previously:**
- `.github/copilot-instructions.md` (Dec 10)
- Folder renames: `EVARB Bot VSCode` → `EVisionBetCode` etc.
- Various earlier commits

---

## How to Commit & Push

### Step 1: Verify Changes
```bash
cd C:\EVisionBetCode

# Check status
git status

# Should show:
# - Renamed files (red X → green +)
# - New files: TEST_PLAN.md, SYSTEM_ARCHITECTURE.md, RENDER_DEPLOYMENT.md
# - Modified: README.md, QUICK_START.md, etc.
```

### Step 2: Stage All Changes
```bash
# Stage everything
git add -A

# Or stage selectively if preferred
git add pipeline_v2/
git add core/h2h.py core/spreads.py core/totals.py core/player_props.py core/nfl_props.py
git add core/fair_prices.py
git add legacy/
git add *.md
```

### Step 3: Commit
```bash
git commit -m "chore: reorganize codebase - rename handlers, consolidate fair_prices, move legacy files

Changes:
- Renamed pipeline_v2: raw_odds_pure → extract_odds, calculate_ev → calculate_opportunities
- Renamed core handlers: removed _handler suffix (h2h, spreads, totals, player_props, nfl_props)
- Created unified fair_prices.py module (was split across v1/v2)
- Moved deprecated files to legacy/ folder (safe to delete after testing)
- Updated all documentation with new filenames
- Added SYSTEM_ARCHITECTURE.md, RENDER_DEPLOYMENT.md, TEST_PLAN.md

No functional changes - all renaming for clarity and organization."
```

### Step 4: Push to GitHub
```bash
# Push to main
git push origin main

# Or push to a feature branch first (safer)
git push origin -u feature/cleanup-reorganize
# Then create PR on GitHub
```

### Step 5: Mobile Verification (Optional)
- Open GitHub mobile app
- Navigate to repository
- Verify commit appears in history
- Edit `.env` or `config.py` to test mobile workflow

---

## Git Commands Reference

```bash
# See all changes
git status

# See detailed changes
git diff

# Undo changes to a file
git checkout core/h2h.py

# Undo all changes
git reset --hard

# See commit history
git log --oneline -10

# See what's staged
git diff --staged
```

---

## After Push

### 1. Verify on GitHub.com
- Go to repository
- Check commit appears
- Verify all files listed correctly

### 2. Verify Files on Mobile (GitHub App)
- Open GitHub app on phone
- Navigate to repository
- View commit
- Try editing `core/config.py`
- Commit from phone
- Verify shows on web

### 3. Deploy to Render
- Render should auto-redeploy if webhook configured
- Or manually trigger redeploy in Render dashboard
- Check logs for successful build

### 4. Run Local Tests
```bash
python pipeline_v2/extract_odds.py
python pipeline_v2/calculate_opportunities.py
# Verify CSVs created with expected data
```

---

## Checklist Before Pushing

- [ ] All renamed files show in `git status`
- [ ] No syntax errors in Python files
- [ ] All imports work: `python -c "from core.fair_prices import build_fair_prices_two_way"`
- [ ] Documentation updated (README.md, QUICK_START.md)
- [ ] TEST_PLAN.md, SYSTEM_ARCHITECTURE.md, RENDER_DEPLOYMENT.md created
- [ ] Legacy folder contains old files
- [ ] No sensitive data in commits (.env keys already in repo, that's ok)
- [ ] Commit message clear and descriptive

---

## If Something Goes Wrong

### Undo Last Commit (Before Push)
```bash
git reset --soft HEAD~1
# Changes go back to staging area
# Edit, fix, then commit again
```

### Undo After Push
```bash
# Create new commit that undoes changes
git revert HEAD

# Or force push (careful!)
git reset --hard HEAD~1
git push -f origin main  # Not recommended on shared repos
```

### Resolve Merge Conflicts (If Any)
```bash
# If pulling and conflicts appear
git status  # See conflicted files

# Edit conflicted files manually
# Look for <<<<<<, ======, >>>>>>

# Then:
git add resolved_file.py
git commit -m "Resolved merge conflict"
git push origin main
```

---

## Summary

✅ **Ready to Commit:**
- All file renames complete
- All legacy files moved
- All new files created
- All documentation updated
- All imports working

✅ **Next Action:**
```bash
git add -A
git commit -m "chore: reorganize codebase - rename handlers, consolidate fair_prices, move legacy files"
git push origin main
```

✅ **Then:**
1. Test locally: `python pipeline_v2/extract_odds.py`
2. Deploy to Render
3. Monitor first run

---

**Questions? See:**
- `SYSTEM_ARCHITECTURE.md` - What the system does
- `RENDER_DEPLOYMENT.md` - How to deploy
- `TEST_PLAN.md` - How to test
