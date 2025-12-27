# EVisionBet Archive Index
## Consolidated Reference Library
**Created:** December 28, 2025

---

## 📋 WHAT'S HERE

This archive contains all previous versions, experiments, and documentation from the EVisionBet project development. Everything is organized for easy reference and searching.

---

## 📁 DIRECTORY STRUCTURE

### **1. OLD CODE & PIPELINES**

#### `pipeline_v2/`
- Original V2 extraction pipeline
- Uses raw API structure
- Reference for: fair odds calculation, bookmaker grouping

#### `v3/`
- Modular V3 architecture attempt
- Per-sport extractors with base class
- Reference for: DRY patterns, scalability ideas

#### `*.py` (root level)
- `pipeline_v3.py` - Orchestrator for V3 (not used)
- `filter_two_way.py` - Utility to filter 2-way markets
- `format_csvs.py` - CSV formatting utility
- `raw_NFL.py` - NFL extraction test
- `setup_production.py` - Production setup script

### **2. DOCUMENTATION & ANALYSIS**

#### Root Level Docs
- `PHASE_5_SUMMARY.txt` - Project phase completion notes
- `ARCHIVE_ANALYSIS.md` - Analysis of what was done
- `ARCHIVE_COMPLETE.md` - Completion report
- `DOCUMENTATION_GUIDE.md` - How docs were organized
- `OPTIMIZATION_GUIDE.md` - Performance/cost optimization ideas
- `V3_START_HERE.txt` - V3 project startup guide

### **3. OLD PROJECTS & EXPLORATION**

#### `database_setup/`
- Database initialization scripts
- Schema definitions
- Connection setup utilities

#### `exploration/`
- Ad-hoc testing and research
- API experiments
- Market structure exploration

#### `old_data/`
- Previous CSV extracts
- Historical odds data
- Test datasets

#### `session_notes/`
- Development session logs
- Problem-solving notes
- Progress tracking

---

## 🔍 HOW TO SEARCH THIS ARCHIVE

### Find Fair Odds Ideas
→ Look in: `pipeline_v2/` or `OPTIMIZATION_GUIDE.md`

### Find V3 Architecture Patterns
→ Look in: `v3/base_extractor.py` or `V3_START_HERE.txt`

### Find Previous CSV Formats
→ Look in: `old_data/` or `PHASE_5_SUMMARY.txt`

### Find Deployment References
→ Look in: `setup_production.py` or session_notes

### Find Cost/Performance Ideas
→ Look in: `OPTIMIZATION_GUIDE.md`

---

## 💡 KEY TAKEAWAYS FROM ARCHIVE

**What Worked Well:**
- Bookmaker rating system (3⭐ sharp vs 1⭐ target)
- Two-stage pipeline (extract then calculate)
- CSV-first approach (resilient to DB issues)

**What We Moved Away From:**
- Modular per-sport extractors (too complex, use simple standardized instead)
- Orchestrator patterns (single file better for now)
- Separate fair odds calculation stage (merge into extraction later if needed)

**What's Still Valuable:**
- Fair odds weight calculations
- Bookmaker grouping logic
- Market pairing validation

---

## ✅ CURRENT ACTIVE SETUP

**Not in this archive** (currently in use):

- `extract_nba_v3.py` - Main active extractor
- `data/v3/extracts/` - Latest CSV outputs
- `backend_api.py` - FastAPI server
- `V3_STANDARDIZED_SETUP.md` - Active setup guide

---

## 📝 TO ADD IDEAS FROM ARCHIVE

When referencing something from this archive to implement:

1. Find the file/concept
2. Copy the relevant code/ideas
3. Adapt to current standardized format
4. Test thoroughly
5. Document in main README

---

**Last Updated:** December 28, 2025
**Archive Size:** ~17 items organized by type
**Easy Scanning:** ✅ Organized by function, documented with this index
