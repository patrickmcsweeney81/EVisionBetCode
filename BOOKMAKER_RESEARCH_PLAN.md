# FINAL BOOKMAKER ORDER & RESEARCH PLAN

## New CSV Column Structure (LOCKED)

**8 Core Columns:**
```
event_id, extracted_at, commence_time, league, event_name, market_type, point, selection
```

**Then 54 Bookmakers (NEW: adding bet365):**

### TIER 1: 4⭐ SHARPS (Fair Odds Calculation) - 6 Books
```
pinnacle, betfair_ex_eu, matchbook, draftkings, fanduel, lowvig
```

### TIER 2: 0⭐ TARGET AU BOOKS (EV Surface) - ~15 Books
**Prioritized (named first):**
```
bet365, sportsbet, dabble_au, pointsbetau, neds, unibet
```

**Remaining AU (any order):**
```
betfair_ex_au, betr_au, betright, boombet, ladbrokes_au, playup, tab, tabtouch, ballybet, betparx
```

### TIER 3 & 4: SECONDARY & REGIONAL (Need Research) - ~33 Books
**Current list (TO BE RESEARCHED & REORDERED):**
```
betanysports, betclic_fr, betmgm, betrivers, betsson, betus, bovada, codere_it, coolbet, 
espnbet, everygame, fanatics, fliff, gtbets, hardrockbet, leovegas_se, marathonbet, 
mybookieag, nordicbet, onexbet, parionssport_fr, rebet, sport888, tipico_de, unibet_fr, 
unibet_nl, unibet_se, williamhill, williamhill_us, winamax_de, winamax_fr
```

---

## RESEARCH PLAN: Understand Remaining 33 Books

**Need to determine for each:**
1. **NBA Coverage** - Does it offer NBA markets?
2. **Prop Market Support** - Player props, team props, etc?
3. **Line Strength** - How sharp/competitive are their odds?
4. **Regional Focus** - Where is it primarily used?
5. **Suggested Rating** - 3⭐, 2⭐, or lower?

---

## Books to Research Online

### US Mainland Books (likely 2-3⭐):
- betmgm - DK/FD sibling, likely 3⭐
- betrivers - Good mainland coverage, likely 2-3⭐
- betanysports - Unknown tier
- betus - Unknown tier
- everygame - Unknown tier
- fanatics - New mainstream, likely 2-3⭐

### US Offshore/Secondary (likely 2⭐):
- bovada - Legacy offshore, 2⭐
- coolbet - Unknown
- espnbet - ESPN property, unknown
- fliff - Unknown
- gtbets - Unknown
- hardrockbet - Hard Rock brand, 2⭐?
- mybookieag - Offshore, 2⭐
- onexbet - Unknown
- rebet - Unknown
- sport888 - Unknown

### European (likely 2-3⭐):
- betclic_fr - French market, 2⭐?
- betsson - Betsson Group (established), 2-3⭐
- codere_it - Italian, regional
- leovegas_se - Swedish, regional
- marathonbet - European, 2⭐
- nordicbet - Nordic, regional
- parionssport_fr - French state-owned, 2-3⭐?
- tipico_de - German, regional
- unibet_* (fr, nl, se) - Kindred Group, 2-3⭐
- williamhill* - UK established, 2⭐
- winamax_* (de, fr) - French, regional

---

## Next Steps

1. **Review online** for each book's:
   - NBA market availability
   - Prop market depth
   - Reputation/sharpness
   - Regional strength

2. **Propose tiers:**
   - Which should be 3⭐? (Betmgm? Betrivers? Fanatics? Betsson? Parionssport?)
   - Which should be 2⭐?
   - Any that should be removed/0⭐ for NBA?

3. **Finalize order:**
   - 4⭐ (6 books)
   - 3⭐ (? books) 
   - 2⭐ (? books)
   - 0⭐ AU targets (15 books)

4. **Lock & commit** as final CSV column order

---

## Questions for You

1. **"uni"** in AU books - is this `unibet` (base) or should it be a specific AU variant?
2. Should **bet365** be added to API extractor? (Currently not in BOOKMAKER_MAPPING)
3. Any books you recognize as obviously sharp or obviously weak for NBA/props?

