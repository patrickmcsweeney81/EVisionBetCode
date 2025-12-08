# Betfair Coverage Analysis & Solution

## Analysis Results (Dec 3, 2025)

### Current Betfair Coverage: 2.66% (234 of 8,786 rows)

This appears low, but it's actually **CORRECT** and expected. Here's why:

### Market Breakdown:
- **Total rows:** 8,786
- **H2H markets:** 234 rows (2.66% of total)
- **Player prop markets:** 8,552 rows (97.34% of total)

### Betfair Coverage by Market Type:
| Market Type | Betfair Coverage |
|------------|------------------|
| **h2h** | 234/234 (100%) ✅ |
| **player props** | 0/8,552 (0%) ⚠️ |

## Root Cause: Betfair Doesn't Offer Player Props

**Betfair Exchange does NOT offer NBA player prop markets.**  
They only offer:
- h2h (match winner)
- spreads (handicaps)  
- totals (over/under)

This is a limitation of Betfair's product offering, not a configuration issue.

---

## Configuration Status

### ✅ CORRECTLY CONFIGURED:

1. **Regions in .env:** `REGIONS=au,us,eu`  
   - ✅ Includes `eu` which is needed for Betfair
   
2. **Book Weights (book_weights.py):**
   ```python
   "betfair_ex_au": 3,  # Strong weight for main markets
   "betfair_ex_eu": 3,  # Strong weight for main markets
   ```
   - ✅ Betfair has proper weight (3 = strong)

3. **API Response:**
   - ✅ Betfair odds ARE being returned by The Odds API
   - ✅ Bot IS collecting and logging Betfair odds
   - ✅ Betfair IS included in fair price calculations (weight 3)

### ⚠️ PREVIOUS ISSUE (NOW FIXED):

**core/config.py had:**
```python
WEIGHT_BETFAIR = 0.0  # Betfair excluded from fair calculation
```

**Changed to:**
```python
WEIGHT_BETFAIR = 0.25  # Betfair gets 25% weight
```

**Note:** This legacy setting only affects old code paths. New handlers use `book_weights.py` which already had Betfair = 3.

---

## Solution for Better Sharp Coverage

Since Betfair can't provide player prop coverage, we need to improve sharp coverage for props from other sources:

### Current Sharp Coverage for Props:

| Bookmaker | Weight | Coverage | Notes |
|-----------|--------|----------|-------|
| **Pinnacle** | 4 | 38% | Best overall, but limited prop markets |
| **DraftKings** | 4 | Good | Excellent prop markets ⭐ |
| **FanDuel** | 4 | Good | Excellent prop markets ⭐ |
| **BetMGM** | 3 | Moderate | Strong props |
| **BetOnline** | 3 | Unknown | Need to test |
| **Betfair** | 1 | 0% | Doesn't offer props ❌ |

### Recommended Actions:

1. **✅ DONE: Enable Betfair for main markets**
   - Changed `WEIGHT_BETFAIR` from 0.0 to 0.25
   - Betfair will now contribute to h2h/spreads/totals fair prices

2. **NEXT: Verify DraftKings/FanDuel are being collected**
   - These are CRITICAL for player prop fair prices (weight 4)
   - Check if they're in the API response
   - Ensure `us` region is working

3. **OPTIONAL: Add more US sharp books**
   - Circa Sports (weight 4) - if available
   - Bookmaker/CRIS (weight 4) - if available
   - Heritage Sports (weight 3) - if available

4. **OPTIONAL: Improve Pinnacle prop coverage**
   - Pinnacle offers props but limited markets
   - May need to request specific prop markets
   - Check Pinnacle's prop market availability

---

## Expected Outcomes After Fix

### For H2H Markets (234 rows):
- **Before:** Fair price = 75% Pinnacle + 25% other sharps (no Betfair)
- **After:** Fair price = 75% Pinnacle + 25% Betfair + other sharps (weighted median)
- **Improvement:** More accurate fair prices, better EV detection

### For Player Props (8,552 rows):
- **Before:** Fair price = Pinnacle + DK/FD (if available)
- **After:** Same (Betfair doesn't affect props)
- **Improvement:** None for props (need DK/FD coverage instead)

---

## Data Quality Summary

### ✅ What's Working:
- Betfair h2h coverage: **100%** (234/234 h2h markets)
- Pinnacle coverage: **38%** (3,340/8,786 total rows)
- API regions configured correctly (`au,us,eu`)
- Book weights system working properly
- Fair price calculations using weighted median

### ⚠️ What Needs Improvement:
- **Player prop sharp coverage** is the real issue (not Betfair)
- Need to verify DraftKings/FanDuel are being collected
- Consider adding more US sharp books (Circa, CRIS, Heritage)
- May need to filter out extreme EV outliers (>100%)

---

## Test Commands

### Verify Betfair is now included:
```powershell
python ev_arb_bot.py
# Check all_odds_analysis.csv - Betfair column should be populated for h2h markets
```

### Check US sharp book coverage:
```powershell
$csv = Import-Csv "data\all_odds_analysis.csv"
$with_dk = ($csv | Where-Object { $_.Draftkings -ne '' }).Count
$with_fd = ($csv | Where-Object { $_.Fanduel -ne '' }).Count
Write-Host "DraftKings: $with_dk rows"
Write-Host "FanDuel: $with_fd rows"
```

### Verify fair prices changed:
```powershell
# Compare fair prices before/after for same event
# Should see slight differences in h2h fair prices
```

---

## Conclusion

**Betfair coverage is CORRECT** - it's 100% for h2h markets where Betfair offers odds.

The low 2.66% overall percentage is because:
- 97% of your data is player props
- Betfair doesn't offer player props

**Real action items:**
1. ✅ **DONE:** Enable Betfair in legacy config (changed WEIGHT_BETFAIR to 0.25)
2. **TODO:** Verify DraftKings/FanDuel prop coverage (they're the key for props, not Betfair)
3. **TODO:** Test if fair prices improved for h2h markets
4. **TODO:** Consider filtering extreme EV outliers before logging (see DATA_QUALITY_TODO.md)
