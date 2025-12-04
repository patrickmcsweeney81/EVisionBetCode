# Data Quality TODO - all_odds_analysis.csv Issues

## 🚨 Critical Issues (High Priority)

### 1. Extreme EV Outliers (417% - 388%)
**Problem:** Betright showing absurdly high odds (8.5-9.0) vs fair price (~1.7-1.9)
- Example: Player props showing 9.0 odds when fair is 1.74
- Likely causes: Stale odds, data entry errors, or bookmaker system glitches

**Solution Options:**
- [ ] Add max EV threshold filter (e.g., reject EV > 100%)
- [ ] Add odds range validation (reject if price/fair ratio > 3.0)
- [ ] Flag suspicious odds for manual review before logging
- [ ] Add timestamp checks to detect stale odds from API

**Impact:** False positives waste analysis time and could lead to bad bets

---

### 2. ~~Low Betfair Coverage (2.66%)~~ ✅ RESOLVED
**Problem:** ~~Only 234 of 8,786 rows have Betfair odds~~
- **RESOLVED:** Betfair has 100% coverage for h2h markets (234/234)
- Low overall % is because 97% of data is player props (which Betfair doesn't offer)
- This is EXPECTED BEHAVIOR - not a bug

**What was done:**
- [x] Analyzed coverage by market type - Betfair perfect for h2h
- [x] Fixed legacy config: Changed `WEIGHT_BETFAIR` from 0.0 to 0.25
- [x] Verified book_weights.py already has Betfair = 3 (strong)
- [x] Confirmed DK/FD have excellent prop coverage (86-87%)
- [x] Created BETFAIR_ANALYSIS.md with full details

**Impact:** Fair prices for h2h markets now properly include Betfair (weight 3)

---

### 3. Low Pinnacle Coverage (38%)
**Problem:** Only 3,340 of 8,786 rows have Pinnacle odds
- Pinnacle is the gold standard for sharp pricing
- Many rows rely on fewer sharp books

**Solution Options:**
- [ ] Verify Pinnacle regions in config (needs 'us' or 'eu')
- [ ] Check which markets Pinnacle offers (may not cover all player props)
- [ ] Add fallback sharp books (Circa Sports, BetOnline sharp lines)
- [ ] Consider minimum sharp book requirement (e.g., need 3+ sharps)

**Impact:** Lower confidence in fair price accuracy

---

## ⚠️ Medium Priority Issues

### 4. Market Fragmentation (200+ Market Variations)
**Problem:** Each line creates a separate market (player_points_10.5, player_points_11.5, etc.)
- 200+ different market types make analysis difficult
- Hard to aggregate and compare similar opportunities
- Example: "player_points_rebounds_assists_39.5" has only 46 rows

**Solution Options:**
- [ ] Normalize market names (all "player_points" regardless of line)
- [ ] Store line value in separate column consistently
- [ ] Group by base market type for analysis
- [ ] Create market categories (h2h, spreads, totals, props)

**Impact:** Better aggregation and trend analysis

---

### 5. High Negative EV Percentage (59%)
**Problem:** 5,209 of 8,786 rows (59%) have negative EV
- Normal for market efficiency, but high percentage
- Logging many unfavorable opportunities

**Solution Options:**
- [ ] Add pre-filter before logging (only log EV > -5%?)
- [ ] Keep all data but add flag for "analysis only" rows
- [ ] Review bookmaker selection (are we including too many recreational books?)
- [ ] Consider separate CSVs for positive vs all opportunities

**Impact:** Cleaner data, faster processing, smaller files

---

### 6. Bookmaker Data Validation
**Problem:** No validation for stale or suspicious odds
- Betright showing extreme outliers suggests data quality issues
- No timestamp/staleness checks

**Solution Options:**
- [ ] Add odds update timestamp from API
- [ ] Reject odds older than X minutes
- [ ] Add min/max odds validation per market type
- [ ] Cross-validate against multiple books (flag if 1 book is 2x different)
- [ ] Add bookmaker reliability scoring

**Impact:** More reliable odds data

---

## ✅ What's Working Well

- ✅ No missing fair prices (all rows have calculated fair value)
- ✅ All rows have sharp book count ≥2
- ✅ 1,803 opportunities with EV > 3% (20.5% of total)
- ✅ Good bookmaker variety (Sportsbet, Pointsbet, Dabble, Ladbrokes, etc.)
- ✅ CSV format correctly updated to lowercase (start_time, sport, event, etc.)
- ✅ Comprehensive data collection (8,786 opportunities logged)

---

## 📊 Current Data Stats (Dec 3, 2025)

- **Total Rows:** 8,786
- **Positive EV:** 3,483 (39.64%)
- **EV > 3%:** 1,803 (20.5%)
- **Negative EV:** 5,209 (59.29%)
- **Pinnacle Coverage:** 3,340 rows (38.02%)
- **Betfair Coverage:** 234 rows (2.66%)

**Top Bookmakers by Volume:**
1. Sportsbet: 1,748
2. Pointsbet: 1,645
3. Dabble: 1,492
4. Betright: 949
5. Ladbrokes: 919

**Top Markets:**
1. player_double_double: 528
2. player_first_basket: 478
3. player_threes_1.5: 388
4. player_threes_2.5: 317
5. h2h: 234

---

## 🎯 Recommended Implementation Order

1. **First:** Add extreme EV filter (>100%) to prevent obvious errors
2. **Second:** Improve Betfair/Pinnacle coverage by checking config
3. **Third:** Add odds validation (timestamp, min/max ranges)
4. **Fourth:** Market name normalization for better analysis
5. **Fifth:** Optimize negative EV logging strategy

---

## 📝 Notes

- Data generated from all_odds_analysis.csv on Dec 3, 2025
- Bot successfully processes NBA player props from multiple AU bookmakers
- CSV format migration to lowercase completed (commit 10d540c)
- Time filters currently disabled (MIN_TIME_TO_START_MINUTES=0, MAX_TIME_TO_START_HOURS=999)
