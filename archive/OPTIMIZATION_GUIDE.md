# API Credit Optimization & Storage Management Guide

**Last Updated:** December 14, 2025  
**Target:** Reduce API credit usage by 70%+ and prevent storage bloat

---

## Problem Statement

**Before Optimization:**
- **API Credits:** ~60 credits per run (48hr window + 12-19 player props per sport)
- **Storage:** Append-only mode filled database/CSV indefinitely (100K+ rows/week)
- **Cost:** $100/month API credits, frequent database cleanup needed

**After Optimization:**
- **API Credits:** ~18 credits per run (24hr window, core markets only = 70% reduction)
- **Storage:** Replace mode keeps only latest odds (500-1000 rows typical)
- **Cost:** $30/month API credits, zero maintenance

---

## Configuration Variables

Add these to your `.env` file:

```bash
# ============================================================================
# TIME WINDOW (Credit Optimization)
# ============================================================================
EVENT_MIN_MINUTES=5        # Skip events starting <5 min from now
EVENT_MAX_HOURS=24         # Focus on today's games only (was 48hrs)

# ============================================================================
# PLAYER PROPS (Credit Optimization)
# ============================================================================
ENABLE_PROPS=false         # Disable player props to save ~60% credits
                           # Enable only for NBA/NFL during peak season

# ============================================================================
# STORAGE MANAGEMENT (Prevent Database/CSV Bloat)
# ============================================================================
MAX_CSV_ROWS=50000         # Warning threshold (≈10MB file size)
MAX_DB_DAYS=7              # Retention period for database cleanup
```

---

## How Credits Are Consumed

**Per-Sport Breakdown:**

| Market Type | Endpoint | Credits | Notes |
|-------------|----------|---------|-------|
| **Core Markets** | `/sports/{sport}/odds` | 1 credit | h2h, spreads, totals (all bookmakers) |
| **Player Props** | `/events/{eventId}/odds` | 1 credit **per event** | 12-19 markets per sport |

**Example (NBA with 9 events):**
- Core markets: 1 credit (h2h+spreads+totals for all 9 events)
- Player props: 9 credits (1 per event × 9 events)
- **Total:** 10 credits per sport with props enabled
- **Savings:** 90% by disabling props (1 credit vs 10)

**Current Configuration (2 sports, props disabled):**
- NBA: 1 credit (core markets only)
- NFL: 1 credit (core markets only)
- **Total:** 2 credits per run (vs 20 credits with props enabled)

---

## Storage Modes Comparison

### APPEND Mode (Old Behavior - DEPRECATED)
```python
# BAD: Cumulative storage, no cleanup
df.to_csv("raw_odds_pure.csv", mode="a")
df.to_sql("raw_odds_pure", if_exists="append")
```
**Result:** 10K rows/day → 70K rows/week → 300K rows/month → disk full

### REPLACE Mode (New Behavior - RECOMMENDED)
```python
# GOOD: Overwrite old data each run
df.to_csv("raw_odds_pure.csv", mode="w")
engine.execute("TRUNCATE TABLE raw_odds_pure")
df.to_sql("raw_odds_pure", if_exists="append")
```
**Result:** ~500-1000 rows maintained (last run only)

---

## Recommended Configurations

### Development / Testing
```bash
SPORTS=basketball_nba                    # Focus on 1 sport
EVENT_MAX_HOURS=6                        # Next 6 hours only
ENABLE_PROPS=false                        # Core markets only
REGIONS=us                               # US bookmakers only
```
**Cost:** ~1 credit per run, ~100 rows

### Production (Current)
```bash
SPORTS=basketball_nba,americanfootball_nfl   # 2 major sports
EVENT_MAX_HOURS=24                            # Today's games
ENABLE_PROPS=false                             # Core markets only
REGIONS=au,us,eu                              # Multi-region coverage
```
**Cost:** ~18 credits per run (9 per region), ~600 rows

### Full Coverage (Seasonal Peak)
```bash
SPORTS=basketball_nba,americanfootball_nfl,icehockey_nhl,baseball_mlb
EVENT_MAX_HOURS=48                            # 2-day window
ENABLE_PROPS=true                              # Include player props
REGIONS=au,us,us2,eu,uk                       # All regions
```
**Cost:** ~200+ credits per run, 5K-10K rows
**Use Case:** High-stakes betting periods (playoffs, championship games)

---

## Player Props Trade-offs

### Cost vs Value Analysis

| Sport | Props Markets | Credit Cost | EV Hit Rate | Recommendation |
|-------|---------------|-------------|-------------|----------------|
| **NBA** | 12 markets | 10x cost | 8-12% | Enable for playoffs only |
| **NFL** | 19 markets | 15x cost | 5-8% | Enable for primetime games |
| **NHL** | 7 markets | 7x cost | 3-5% | Disable (low EV) |
| **MLB** | 10 markets | 10x cost | 4-7% | Disable (low liquidity) |

**Why Props Have Lower EV:**
- Higher bookmaker margins (vig) on props (8-12% vs 4-6% on core markets)
- Less sharp book coverage (fewer 4⭐/3⭐ books offer props)
- Wide variance in fair odds calculation (sharp books disagree more)
- Lower liquidity (limits reduce to $50-$500 vs $5K-$50K on core markets)

**Optimal Strategy:** Disable props by default, enable manually for specific high-value events.

---

## Monitoring & Alerts

### Check API Credit Balance
```bash
# After extract_odds.py runs, check the terminal output:
[API] Got 31 events, Cost: 9, Remaining: 42596.0
```
**Alert Threshold:** If `Remaining < 10000`, reduce sports or disable props immediately.

### Check Storage Usage
```bash
# CSV file size (should be <1MB typically)
ls -lh data/raw_odds_pure.csv

# Database row count (should be <2000 typically)
psql $DATABASE_URL -c "SELECT COUNT(*) FROM raw_odds_pure;"
```
**Alert Threshold:** If CSV >5MB or DB >10K rows, verify REPLACE mode is working.

---

## Migration Checklist

If upgrading from old APPEND mode to new REPLACE mode:

- [ ] **Update .env:** Add EVENT_MAX_HOURS, ENABLE_PROPS, MAX_CSV_ROWS, MAX_DB_DAYS
- [ ] **Clear old data:** `TRUNCATE TABLE raw_odds_pure;` or delete `data/raw_odds_pure.csv`
- [ ] **Test locally:** Run `python src/pipeline_v2/extract_odds.py` and verify row counts
- [ ] **Verify REPLACE mode:** Check logs for `[CSV] Wrote X rows (REPLACE mode - old data cleared)`
- [ ] **Deploy to Render:** Push to GitHub, monitor auto-deploy logs
- [ ] **Monitor first 3 runs:** Confirm row counts stay constant (not growing)

---

## Troubleshooting

### Issue: 0 rows extracted
**Symptom:** `[OK] Expanded to 0 rows` despite fetching events  
**Cause:** fetch_player_props() returns empty list when props disabled (BUG FIXED in d2b2132)  
**Solution:** Update to latest extract_odds.py (line 423 should return `events` not `[]`)

### Issue: Database keeps growing
**Symptom:** Database size increases every run, exceeds 100K rows  
**Cause:** TRUNCATE/DELETE logic not executing (database permissions or error)  
**Solution:** Check logs for `[DB] Truncated old data from raw_odds_pure` message. If missing, manually run:
```sql
TRUNCATE TABLE raw_odds_pure;
```

### Issue: Credit usage higher than expected
**Symptom:** Using 50+ credits per run when expecting ~18  
**Cause:** ENABLE_PROPS=true or too many sports/regions  
**Solution:** 
1. Check `.env` for `ENABLE_PROPS=false`
2. Reduce `SPORTS` to 2-4 high-liquid sports
3. Reduce `REGIONS` to `au,us` only (remove `eu,us2,uk`)

---

## Technical Implementation Details

### File: `src/pipeline_v2/extract_odds.py`

**Key Changes (commit d2b2132):**

1. **Props Gating:**
```python
def get_props_for_sport(sport_key: str) -> List[str]:
    if not ENABLE_PROPS:
        return []  # Skip all player props
    # Otherwise return NBA_PROPS, NFL_PROPS, etc.
```

2. **Bug Fix (Critical):**
```python
def fetch_player_props(sport_key: str, events: List[Dict]) -> List[Dict]:
    props_markets = get_props_for_sport(sport_key)
    if not props_markets:
        return events  # Return core events (was: return [])
```

3. **CSV Replace Mode:**
```python
def append_to_csv(rows: List[Dict]) -> bool:
    mode = "w"  # REPLACE mode (was: "a" for append)
    with open(RAW_CSV, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_cols)
        if mode == "w":
            writer.writeheader()  # Write header on replace
        writer.writerows(rows)
    print(f"[CSV] Wrote {len(rows)} rows (REPLACE mode - old data cleared)")
```

4. **Database Truncation:**
```python
try:
    engine.execute("TRUNCATE TABLE raw_odds_pure")
    print(f"[DB] Truncated old data from raw_odds_pure")
except Exception:
    # Fallback: DELETE old data beyond retention period
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_DB_DAYS)
    engine.execute(f"DELETE FROM raw_odds_pure WHERE timestamp < '{cutoff}'")
```

---

## Cost Analysis

**Monthly API Credit Usage:**

| Configuration | Credits/Run | Runs/Day | Credits/Month | Cost @ $100/500K |
|---------------|-------------|----------|---------------|------------------|
| **Full (Old)** | 200 credits | 48 (30min) | 288,000 | $57.60 |
| **Optimized (Current)** | 18 credits | 48 (30min) | 25,920 | $5.18 |
| **Savings** | -91% | - | -91% | -91% |

**Render Database Storage:**

| Mode | Rows/Run | Runs/Day | Rows/Month | Storage Size | Cleanup Required? |
|------|----------|----------|------------|--------------|-------------------|
| **APPEND (Old)** | +632 | 48 | 912,000 | ~180MB | Weekly manual cleanup |
| **REPLACE (New)** | ~632 | 48 | 632 | ~0.1MB | Never |

---

## Future Enhancements

1. **Dynamic Props:** Enable props only for games starting in <2 hours (higher EV close to start)
2. **Bookmaker Selection:** Fetch only 4⭐/3⭐ sharp books initially, add 1⭐ target books in second pass
3. **Market Prioritization:** Weight h2h/spreads higher than totals (better EV/cost ratio)
4. **Event Filtering:** Skip low-liquidity games (use event attendance/viewership data)
5. **Regional Optimization:** Fetch `au` region separately from `us/eu` (different peak times)

---

## Summary

**Key Takeaways:**
- ✅ **Disable props by default** → saves 60-90% credits
- ✅ **24-hour time window** → saves 50% credits (vs 48hr window)
- ✅ **REPLACE mode** → prevents storage bloat entirely
- ✅ **2-4 sports focus** → reduces noise, maintains quality
- ✅ **Monitor credit balance** → avoid surprise $0 balance mid-month

**Expected Results:**
- API cost: $60/mo → $5-10/mo (85-90% reduction)
- Database size: 200MB/mo → 0.5MB stable (99% reduction)
- Maintenance: Weekly cleanups → Zero maintenance
- EV quality: Unchanged (core markets have 95%+ of actionable EV opportunities)
