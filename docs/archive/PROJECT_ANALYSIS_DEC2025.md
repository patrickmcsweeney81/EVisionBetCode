# EV Bot Project Analysis & Strategy (December 2025)

## Executive Summary

**Current State:** Functional EV detection system with comprehensive data collection but inefficient CSV format and workflow friction points.

**Primary Goal:** Build a web-based EV dashboard for Australian bookmakers while maintaining robust core engine.

**Immediate Pain Point:** CSV format creates one row per bookmaker per market (6,467 rows for same data that could be ~1,000 rows with pivot format).

---

## 1. CURRENT SYSTEM ARCHITECTURE

### Core Components (✅ Working)
```
ev_arb_bot.py → TheOddsAPI → core/raw_odds_logger.py → data/all_odds_analysis.csv
                                                      ↓
                                              split_extreme_evs.py
                                                      ↓
                                    ┌─────────────────┼─────────────────┐
                                    ↓                 ↓                 ↓
                            all_odds.csv      ev_hits.csv      extreme_odds.csv
                            (6,467 rows)      (2,362 rows)     (271 rows)
```

### Data Flow
1. **Bot collects** odds from API → logs to `all_odds_analysis.csv` (one row per bookmaker)
2. **Split script** separates into 3 CSVs by EV range
3. **Manual review** in Excel/CSV viewer

### File Structure (✅ Confirmed Working)
- `ev_arb_bot.py` - Main bot engine
- `core/` - Modular handlers (h2h, spreads, totals, props)
- `core/book_weights.py` - Unified sharp book weighting (v2.0)
- `core/raw_odds_logger.py` - CSV writing logic
- `split_extreme_evs.py` - Post-processing to create 3 CSVs
- `filter_ev_hits.py` - LEGACY (was for old format, now redundant)

---

## 2. KEY PROBLEMS IDENTIFIED

### Problem #1: Inefficient CSV Format ⚠️ HIGH IMPACT
**Current:** One row per bookmaker per market per selection
```csv
start_time,sport,event,market,selection,book,price,fair,ev,prob,stake,Pinnacle,Betfair,Sportsbet,Bet365...
2025-12-05 08:10,basketball_nba,Celtics @ Wizards,h2h,Celtics,sportsbet,1.210,1.233,-1.89%,81.08%,$0,1.240,1.240,1.210,...
2025-12-05 08:10,basketball_nba,Celtics @ Wizards,h2h,Celtics,pointsbet,1.220,1.233,-1.08%,81.08%,$0,1.240,1.240,,1.220...
2025-12-05 08:10,basketball_nba,Celtics @ Wizards,h2h,Celtics,ladbrokes,1.220,1.233,-1.08%,81.08%,$0,1.240,1.240,,,1.220...
```
**Problem:** Same market repeated 15+ times (one per AU bookie)
- 6,467 total rows for ~400 unique markets
- Duplicated fair price, prob, num_sharps on every row
- Hard to scan/compare bookmaker prices

**Desired:** One row per market with bookmaker columns populated
```csv
start_time,sport,event,market,selection,fair,prob,num_sharps,Sportsbet,Pointsbet,Ladbrokes,Betright,Pinnacle,Betfair...
2025-12-05 08:10,basketball_nba,Celtics @ Wizards,h2h,Celtics,1.233,81.08%,11,1.210,1.220,1.220,1.220,1.240,1.240...
```
**Impact:** ~15x fewer rows, faster Excel loading, easier comparison

---

### Problem #2: Manual Workflow Friction
**Current workflow:**
1. Run `python ev_arb_bot.py` (2-5 minutes)
2. Run `python split_extreme_evs.py` to generate 3 CSVs
3. Open `ev_hits.csv` in Excel
4. Manually filter/sort to find opportunities
5. Copy data to betting tracker spreadsheet

**Desired workflow:**
1. Run bot (automated via cron/scheduler)
2. Open web dashboard
3. Filter/sort instantly with UI
4. Click to see all bookmaker prices
5. Export selections to betting tracker

**Impact:** 5-10 minutes saved per session, better UX

---

### Problem #3: Data Quality Issues (From DATA_QUALITY_TODO.md)
- ✅ **Resolved:** Betfair coverage (intentionally low for props-heavy data)
- ⚠️ **Active:** Extreme EVs from Betright (417% edges - data quality)
- ⚠️ **Active:** Low Pinnacle coverage (38%) - impacts fair price confidence
- ⚠️ **Active:** 200+ market variations (normalization needed)
- ⚠️ **Active:** 59% negative EV rows (could pre-filter)

---

### Problem #4: Legacy Code Confusion
**Files with unclear purpose:**
- `filter_ev_hits.py` - LEGACY from old architecture (before split_extreme_evs.py)
- `extract_ev_hits.py` - Created today but redundant with split_extreme_evs.py
- Multiple test files without clear organization

**Impact:** Developer confusion, maintenance burden

---

## 3. STRATEGIC OPTIONS

### Option A: Quick Fix - Pivot CSV Format ⭐ RECOMMENDED SHORT-TERM
**Timeline:** 1-2 hours
**Effort:** Low
**Impact:** High

**Actions:**
1. Modify `core/raw_odds_logger.py` to collect data by market (not by bookmaker)
2. Write pivot function to create one row per market with bookmaker columns
3. Update `split_extreme_evs.py` to work with new format
4. Test with NBA/NBL data

**Benefits:**
- Immediate UX improvement for CSV users
- ~85% reduction in row count (6,467 → ~1,000)
- Faster Excel performance
- Easier to spot EV opportunities

**Drawbacks:**
- Still manual workflow (Excel-based)
- Doesn't solve web dashboard need

---

### Option B: Build Web Dashboard (MVP) ⭐ RECOMMENDED MEDIUM-TERM
**Timeline:** 4-7 days (per PRODUCT_PLAN.md)
**Effort:** Medium-High
**Impact:** Very High

**Architecture:**
```
Bot (Python) → SQLite/PostgreSQL → FastAPI → Next.js (React)
                                      ↓           ↓
                                   REST API    Web UI
```

**Phase 1 (MVP - 4-7 days):**
1. **Backend API (FastAPI)**
   - Read from `all_odds_analysis.csv` or SQLite
   - Endpoints: `/api/odds`, `/api/hits`, `/api/events`
   - Filters: sport, market, minEV, bookmaker, time window
   - CORS enabled

2. **Web UI (Next.js + Tailwind)**
   - EV hits table (sortable, filterable, mobile-first)
   - Row click → detail drawer with all bookmaker odds
   - AU bookmaker badges
   - Dark mode

3. **Deployment**
   - API: Render/Fly.io (free tier)
   - UI: Vercel (free tier)
   - Bot: Run locally or on free Heroku scheduler

**Benefits:**
- Modern UX (web-based, mobile-friendly)
- Real-time filtering without re-running bot
- Shareable with team/friends
- Foundation for future features (alerts, tracking, subscriptions)

**Drawbacks:**
- Requires learning FastAPI/Next.js (if not familiar)
- Deployment/hosting complexity
- Ongoing maintenance

---

### Option C: Hybrid - Pivot CSV + Simple HTML Viewer
**Timeline:** 2-3 hours
**Effort:** Low-Medium
**Impact:** Medium

**Actions:**
1. Implement pivot CSV format (Option A)
2. Create simple HTML/JS viewer that loads CSV
3. Add basic filtering/sorting with DataTables.js or similar
4. Host as single static HTML file (no backend needed)

**Benefits:**
- Quick to implement
- No backend/API needed
- Better than Excel, simpler than full web app
- Can open locally via browser

**Drawbacks:**
- Limited interactivity vs full web app
- Still file-based (no database)
- No mobile app potential

---

## 4. RECOMMENDED PATH FORWARD

### PHASE 1: Quick Wins (This Week)
**Goal:** Improve current workflow immediately

1. **Pivot CSV Format** ✅ Priority 1
   - Modify `raw_odds_logger.py` to output one row per market
   - Keep bookmaker odds as columns
   - Test with current data

2. **Consolidate Scripts** ✅ Priority 2
   - Delete `extract_ev_hits.py` (redundant)
   - Archive `filter_ev_hits.py` (legacy)
   - Update `split_extreme_evs.py` for new format
   - Clean up test files

3. **Data Quality Filters** ✅ Priority 3
   - Add max EV threshold (100%) to catch Betright issues
   - Add min sharp books requirement (e.g., 2+)
   - Pre-filter negative EV < -10% before logging

### PHASE 2: Web Dashboard MVP (Next Week)
**Goal:** Modern web-based analysis tool

1. **Backend Setup (Days 1-2)**
   - Install FastAPI, SQLAlchemy, pandas
   - Create `/api/odds` endpoint reading from CSV
   - Add filtering logic (sport, market, minEV, bookmaker)
   - Test with Postman

2. **Frontend Setup (Days 3-4)**
   - Initialize Next.js project with Tailwind
   - Create EV hits table component
   - Add filtering UI (dropdowns, sliders)
   - Mobile responsive design

3. **Integration & Deploy (Days 5-7)**
   - Wire frontend to API
   - Add detail drawer for bookmaker comparison
   - Deploy API to Render
   - Deploy UI to Vercel
   - Test end-to-end

### PHASE 3: Enhancement (Future)
- User authentication (email magic link)
- Telegram/Email notifications
- Historical EV tracking
- Bookmaker performance stats
- Kelly calculator
- Bet tracking integration

---

## 5. IMMEDIATE NEXT STEPS

### Decision Point: Choose One Path
**Question for you:**
1. Do you want to fix CSV format FIRST (Option A) for immediate relief?
2. OR jump straight to web dashboard (Option B) and skip CSV improvements?
3. OR try hybrid HTML viewer (Option C) as middle ground?

### Recommended Choice: **Option A → Option B** (Sequential)
**Reasoning:**
- Pivot CSV gives immediate value (today)
- Doesn't block web dashboard work (different codebases)
- CSV format will still be useful for Excel users and data exports
- Web dashboard can read from improved CSV format

---

## 6. TECHNICAL DEBT & CLEANUP

### Files to Archive/Delete
```
TO DELETE (redundant):
- extract_ev_hits.py (created today, unnecessary)

TO ARCHIVE (legacy):
- filter_ev_hits.py (pre-architecture change, no longer needed)
- ev_arb_bot_NEW.py (if exists)
- ev_arb_bot_OLD_MONOLITHIC.py (if exists)

TO KEEP:
- ev_arb_bot.py (main engine)
- split_extreme_evs.py (refactor for new format)
- All core/ modules
- All tests/
```

### Documentation to Update
```
TO UPDATE:
- README.txt (reflect new CSV format)
- PROJECT_SETUP.md (update workflow section)
- ARCHITECTURE_CHANGE.md (document pivot format)

TO CREATE:
- API_DOCUMENTATION.md (when web dashboard built)
- DEPLOYMENT_GUIDE.md (Render + Vercel setup)
```

---

## 7. SUCCESS METRICS

### Phase 1 (CSV Pivot) - Success Criteria
- [ ] Row count reduced from 6,467 → ~1,000
- [ ] Excel load time < 2 seconds
- [ ] All bookmaker prices visible in single row
- [ ] Fair price, EV, prob calculated correctly
- [ ] split_extreme_evs.py works with new format

### Phase 2 (Web Dashboard) - Success Criteria
- [ ] API responds in < 300ms for filtered queries
- [ ] UI loads first page in < 2 seconds on 4G
- [ ] Mobile-responsive (works on iPhone)
- [ ] Filter by sport, market, EV threshold works
- [ ] Detail drawer shows all bookmaker prices
- [ ] Deployed and accessible via public URL

---

## 8. OPEN QUESTIONS

1. **CSV Format:** Do you need backward compatibility with old format for any tools?
2. **Web Dashboard:** Do you have preferences on tech stack (FastAPI vs Flask, React vs Vue)?
3. **Hosting:** Are you okay with free tiers (Render/Vercel) or need paid/custom hosting?
4. **Data Storage:** Keep CSV-based or migrate to SQLite/PostgreSQL?
5. **User Base:** Just you or planning to share with others? (impacts auth requirements)
6. **Timeline:** What's more important - quick CSV fix or jump to web dashboard?

---

## CONCLUSION

**Recommendation:** Start with **Option A (Pivot CSV)** today to get immediate relief from inefficient format, then proceed to **Option B (Web Dashboard MVP)** next week for modern UX and scalability.

This gives you:
- ✅ Immediate productivity boost (better CSV)
- ✅ Foundation for web dashboard (cleaner data structure)
- ✅ Flexibility to pause after Phase 1 if needed
- ✅ Clear path to modern web-based analysis tool

**What do you think? Should we start with the CSV pivot or jump straight to web dashboard planning?**
