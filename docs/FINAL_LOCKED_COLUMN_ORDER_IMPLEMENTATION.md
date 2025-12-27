# FINAL: Bookmaker Ratings & Column Order - LOCKED ✅

**Status:** COMPLETE & COMMITTED  
**Date:** December 28, 2025  
**Commit:** c295f2e  

---

## What Was Locked

### 54 Bookmakers in 5-Tier Rating System

#### 4⭐ SHARPS (Fair Odds Calculation) - 6 books
- **pinnacle** - Premier exchange
- **betfair_ex_eu** - EU exchange
- **matchbook** - Betting exchange
- **draftkings** - US mainstream
- **fanduel** - US mainstream
- **lowvig** - US sharp book

#### 0⭐ TARGETS (EV Opportunity Surface) - 14 books
Australian regional books where we surface EV opportunities:
- **bet365** - Major international (AU operations)
- **betfair_ex_au** - AU exchange
- **sportsbet**, **dabble_au**, **pointsbetau**, **neds**
- **ladbrokes_au**, **unibet**, **betright**, **betr_au**
- **boombet**, **playup**, **tab**, **tabtouch**

#### 3⭐ SHARPS (Sharp Coverage Depth) - 4 books
Fallback sharps for fair odds if 4⭐ insufficient:
- **betonlineag**, **betmgm**, **betrivers**, **fanatics**

#### 2⭐ DECENT (Secondary Market Depth) - 6 books
Secondary books for market coverage:
- **hardrockbet**, **williamhill**, **williamhill_us**, **bovada**, **betanysports**, **espnbet**

#### 1⭐ SOFT (Regional/Promotional) - 24 books
Regional, soft, and promotional books:
- **betclic_fr**, **betsson**, **betus**, **coolbet**, **codere_it**, **everygame**
- **fliff**, **gtbets**, **leovegas_se**, **marathonbet**, **mybookieag**, **nordicbet**
- **onexbet**, **parionssport_fr**, **rebet**, **sport888**, **tipico_de**
- **unibet_fr**, **unibet_nl**, **unibet_se**, **winamax_de**, **winamax_fr**
- **ballybet**, **betparx** (US soft books, not AU)

---

## CSV Column Order (LOCKED FOR ALL SPORTS)

### Column Sequence (62 Total)

```
8 Core + 54 Bookmakers in Tier Order:

1. event_id
2. extracted_at
3. commence_time
4. league
5. event_name
6. market_type
7. point
8. selection

9-14:   [4⭐ Sharps - 6 cols]
15-28:  [0⭐ AU Targets - 14 cols]
29-32:  [3⭐ Sharps - 4 cols]
33-38:  [2⭐ Decent - 6 cols]
39-62:  [1⭐ Soft - 24 cols]
```

### Exact Bookmaker Order in CSV
```
pinnacle,betfair_ex_eu,matchbook,draftkings,fanduel,lowvig,
bet365,betfair_ex_au,sportsbet,dabble_au,pointsbetau,neds,ladbrokes_au,unibet,betright,betr_au,boombet,playup,tab,tabtouch,
betonlineag,betmgm,betrivers,fanatics,
hardrockbet,williamhill,williamhill_us,bovada,betanysports,espnbet,
betclic_fr,betsson,betus,coolbet,codere_it,everygame,fliff,gtbets,leovegas_se,marathonbet,mybookieag,nordicbet,onexbet,parionssport_fr,rebet,sport888,tipico_de,unibet_fr,unibet_nl,unibet_se,winamax_de,winamax_fr,ballybet,betparx
```

---

## Files Updated

### 1. **bookmaker_ratings.py** (NEW)
- Cleaned from malformed state
- Complete mapping of all 54 books to ratings
- FINAL_COLUMN_ORDER tuple for reference
- Helper functions: `get_sharp_books()`, `get_target_books()`, `get_books_by_rating()`
- Stats for verification

### 2. **extract_nba_v3.py** (UPDATED)
- BOOKMAKER_MAPPING: All 54 books mapped to API keys (already had bet365)
- ALL_BOOKMAKERS: Reordered to locked sequence
  - Moved ballybet & betparx from 0⭐ to 1⭐
  - Moved betmgm, betrivers, fanatics from 2⭐ to 3⭐
  - Reorganized all 54 books in tier order

---

## Verification Results

**Test Extraction Run:** Dec 28, 2025 @ 02:21:16  
**File:** `basketball_nba_raw_20251228_022116.csv`

```
✅ Expected: 62 columns
✅ Actual:   62 columns
✅ Order:    PERFECT MATCH

Structure Breakdown:
  ✓ 8 core columns
  ✓ 6 × 4⭐ sharps
  ✓ 14 × 0⭐ AU targets
  ✓ 4 × 3⭐ sharps
  ✓ 6 × 2⭐ decent
  ✓ 24 × 1⭐ soft

Data:
  ✓ 200 rows (9 NBA games)
  ✓ No data loss
  ✓ All bookmakers present
```

---

## What This Means

### From This Point Forward

1. **All future extractions** (NBA, NFL, NHL, etc.) will output **exactly 62 columns** in **this exact order**
2. **Column positions never change** - downstream code can rely on fixed indices
3. **Bookmaker strength is standardized** - same tier system applies to all sports
4. **Rating logic is documented** - in bookmaker_ratings.py for any future adjustments

### For EV Calculation

- **Fair odds:** Use ONLY 4⭐ books (6 books: pinnacle, betfair_ex_eu, matchbook, draftkings, fanduel, lowvig)
- **Fallback sharps:** Include 3⭐ books if 4⭐ count < 2 (4 additional: betonlineag, betmgm, betrivers, fanatics)
- **EV opportunities:** Surface against 0⭐ AU target books (14 books)
- **Weight totals:** Maintain separate per-side (e.g., Over vs Under) to prevent dilution

### For Pipeline Integration

- Import `bookmaker_ratings.py` functions for any tier-based logic
- Use FINAL_COLUMN_ORDER for CSV writing
- Test new sports by verifying 62-column order matches spec

---

## Decision Rationale

### Regional Classification Corrections
- **ballybet, betparx**: Reclassified as US soft books (not AU) → Moved to 1⭐
- Impact: 0⭐ AU targets now exactly 14 books (consistent set)

### 3⭐ Tier Expansion
- **betmgm, betrivers, fanatics**: Promoted to 3⭐ for sharp coverage depth
- Rationale: Industry-backed operators with reasonable spread management
- Impact: 3⭐ tier now 4 books (provides fallback without diluting 4⭐)

### 2⭐ Tier Refinement
- **espnbet**: Moved from 1⭐ to 2⭐ (decent secondary book)
- Impact: 2⭐ tier stable at 6 books

---

## Next Steps

1. **NFL Extraction**: Create extract_nfl_v3.py using same 54-bookmaker list in identical column order
2. **NHL Extraction**: Create extract_nhl_v3.py using same column structure
3. **Pipeline Integration**: calculate_opportunities.py will use bookmaker_ratings.py tiers for EV calculation
4. **Expand Testing**: Verify all sports output 62 columns in correct order

---

## Critical Notes for Future Developers

⚠️ **DO NOT CHANGE:**
- This column order is now permanent
- Any new sports use this same 54-book sequence
- The tier system (4/3/2/1/0) is locked

✓ **Safe to Change (with care):**
- Individual bookmaker ratings (if market conditions warrant)
- Weights assigned to each tier (if EV calculation needs tuning)
- Regional mappings (if new regions discovered)

Always commit these changes with "FINAL" messages noting the specific adjustment.

---

**Locked at Commit:** c295f2e  
**By:** User direction + comprehensive research + external AI model validation  
**Status:** READY FOR MULTI-SPORT EXPANSION
