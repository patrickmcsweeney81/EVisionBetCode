# EVisionBetCode Archive

This directory contains historical files that are no longer actively used but preserved for reference.

## 📂 Directory Structure

### database_setup/
**Purpose:** Initial database setup scripts (one-time use)
- `setup_database.py` - Initial table creation
- `run_create_tables.py` - Table creation runner
- `create_tables.sql` - Raw SQL schema
- `create_tables_enhanced.sql` - Enhanced schema
- `verify_database.py` - Initial verification

**Why Archived:** Database tables are now managed via migrations or ORM. These scripts were used for initial Render setup.

### exploration/
**Purpose:** Market discovery and exploration scripts
- `discover_markets.py` - Market discovery from Odds API

**Why Archived:** Market discovery completed. Results stored in `data/market_discovery.json`. Script preserved for reference if new sports added.

### old_data/
**Purpose:** Historical data extractions (deleted, not tracked by git)
- Old timestamped CSV files removed
- Only latest `raw_odds_pure.csv` kept in `data/`

**Why Archived:** Old extractions superseded by latest pipeline runs. Data older than 48 hours is stale for betting purposes.

### session_notes/
**Purpose:** Development session completion notes
- `CLEANUP_NOTES_DEC13_2025.md`
- `CODE_REVIEW_FIXES_DEC13.md`
- `COMPLETION_SUMMARY_DEC13.md`
- `STATUS_DOCUMENTATION_COMPLETE_DEC13.md`
- `BACKEND_API_DEPLOYMENT.md`

**Why Archived:** Session-specific completion notes. Superseded by comprehensive documentation suite (VSCODE_SETUP.md, DEVELOPMENT.md, etc.). Preserved for historical context.

### archive/ (pre-existing)
**Purpose:** Earlier archived documentation
- Various analysis and setup documents from earlier development phases
- Maintained as-is for historical reference

---

## 🔍 When to Reference Archive

- **Database Setup:** If recreating database schema from scratch
- **Market Discovery:** If adding new sports or markets
- **Historical Context:** Understanding past decisions and iterations
- **Recovery:** If old scripts needed for reference

---

## ⚠️ Important Notes

- **Do not modify** archived files - they are historical snapshots
- **Git history preserved** - All moves done via `git mv`
- **Reference only** - Use current documentation for active development
- **Context preserved** - These files explain "why we did this"

---

**Last Updated:** December 14, 2025  
**Archived By:** Repository cleanup and organization
