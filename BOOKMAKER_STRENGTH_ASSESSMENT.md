# NBA Bookmaker Strength Assessment

## 4⭐ SHARPS (Locked - 6 Books)
```
pinnacle, betfair_ex_eu, matchbook, draftkings, fanduel, lowvig
```
✅ These are your fair odds calculation books - established, sharp pricing, NBA specialists

---

## RECOMMENDED 3⭐ SHARPS (Best Secondary Options - Pick ~5-8)

### US Mainland (Sharp Depth) - RECOMMEND 2-3
1. **Betmgm** - Part of MGM/Entain, major US player, good NBA coverage, solid prop markets
2. **Betrivers** - Rivers Casino network, US mainland, mid-tier sharp, decent lines
3. **Fanatics** - New mainstream entry (ex-PointsBet tech), growing NBA reputation

### European (Regional Sharpness) - RECOMMEND 1-2
1. **Betsson** - Betsson Group (established 2002), European liquidity, NBA coverage
2. **Parionssport_fr** - French state-owned operator, strong pricing reputation (if has NBA)

### Specialty (Design-based Sharpness)
- **Lowvig** - Already in 4⭐ (low vig = sharp by design)

---

## RECOMMENDED 2⭐ SECONDARY (Regional/Depth) - ~25-30 Books

### US Offshore (Established, less sharp)
- betanysports, betus, bovada, coolbet, everygame, gtbets, mybookieag, sport888

### US Regional/New
- espnbet (ESPN property, newer)
- fliff (newer, unknown)
- hardrockbet (tribal/resort brand)
- onexbet (unknown depth)
- rebet (unknown)

### European Regional (Local Depth)
- betclic_fr (French market)
- codere_it (Italian)
- leovegas_se (Swedish)
- nordicbet (Nordic)
- tipico_de (German)
- unibet (base), unibet_fr, unibet_nl, unibet_se (Kindred Group - established but regional)
- winamax_de, winamax_fr (French/German specialty)
- williamhill, williamhill_us (legacy, not as sharp as DK/FD)

### Betfair Matching Exchange
- matchbook (Already 4⭐)

---

## 0⭐ TARGET AU BOOKS (Surface EV Opportunities) - 15 Books

**Prioritized (You specified):**
- bet365 (Global, big margins, AFL/NRL focused, likely empty for NBA)
- sportsbet (AU corporate, high margin target)
- dabble_au (AU regional)
- pointsbetau (AU corporate, high margin)
- neds (AU regional)
- unibet (or AU variant) - Kindred Group, AU licensed

**Remaining AU (in any order):**
- betfair_ex_au (Exchange - 0⭐ per your decision, target for display)
- betr_au (AU startup)
- betright (AU regional)
- boombet (AU niche)
- ladbrokes_au (AU corporate)
- playup (AU niche)
- tab (AU state betting)
- tabtouch (AU state betting)
- ballybet (may be AU-accessible)
- betparx (may have AU options)

---

## CONFIDENCE NOTES

**High Confidence (Extensive NBA):**
- 4⭐: Pinnacle, Betfair EU, Matchbook, DK, FD, Lowvig ✓✓✓
- 3⭐ candidates: Betmgm, Betrivers, Fanatics ✓✓

**Medium Confidence (Some NBA):**
- 3⭐ candidates: Betsson, Parionssport ✓
- 2⭐: Most European regionals, US mainland secondaries ✓

**Low Confidence (Limited NBA Data):**
- Espnbet, Fliff, Hardrockbet, Rebet, Onexbet, many newer entrants
- **Recommendation:** Verify they even carry NBA before rating

**Unknown (AFL/NRL Focus, may be empty for NBA):**
- Bet365, Tab, Tabtouch - primarily Australia's AFL/NRL market

---

## NEXT STEPS

1. **Verify NBA Availability** - Do these books even offer NBA markets in the API?
   - Check API explorer output for each book
   - Remove books with 0 data in fresh extractions

2. **Finalize Your Tier List:**
   - Confirm 3⭐: (How many? 5, 6, 8?)
   - Confirm 2⭐: (Remaining books)
   - Confirm 0⭐: (15 AU targets confirmed?)

3. **Lock Column Order** with exact sequence:
   - 8 core → 6 × 4⭐ → X × 3⭐ → Y × 2⭐ → 15 × 0⭐

4. **Create `bookmaker_ratings.py`** with this exact mapping

5. **Update `extract_nba_v3.py` ALL_BOOKMAKERS** to this locked order

6. **Commit as "FINAL"** - This order never changes again (for data consistency)

---

## Questions

1. Should we remove books with 0 NBA data from the extraction entirely?
2. How many 3⭐ books do you want? (I suggest 5-8 for good sharp coverage depth)
3. Confirm bet365 can be added to API extractor (if not available in Odds API, mark as 0⭐ but keep in order)?
