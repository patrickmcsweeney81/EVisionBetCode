# Final Bookmaker Order & Rating System

## Strategy
- **4⭐ (5):** Use for fair odds calculation
- **3⭐ (5):** Sharp coverage, fallback for fair odds
- **2⭐ (28):** Secondary/regional/specialty books  
- **0⭐ (15):** Target AU books (where we surface EV hits)

---

## Proposed Final CSV Column Order

```
Core 8 columns
│
├─ event_id
├─ extracted_at
├─ commence_time
├─ league
├─ event_name
├─ market_type
├─ point
└─ selection

Then 53 Bookmakers (by rating tier, then alphabetical):

4⭐ SHARPS (Fair Odds Calculation)
├─ pinnacle
├─ betfair_ex_eu
├─ draftkings
├─ fanduel
└─ matchbook

3⭐ SHARPS (Sharp Coverage Depth)
├─ betonlineag
├─ betrivers
├─ betsson
├─ lowvig
└─ [NEED 5TH - CONFIRM]

2⭐ SECONDARY (Regional/Specialty - 28 books)
├─ betanysports
├─ betclic_fr
├─ betmgm
├─ betus
├─ bovada
├─ codere_it
├─ coolbet
├─ espnbet
├─ everygame
├─ fanatics
├─ fliff
├─ gtbets
├─ hardrockbet
├─ leovegas_se
├─ marathonbet
├─ mybookieag
├─ nordicbet
├─ onexbet
├─ parionssport_fr
├─ rebet
├─ sport888
├─ tipico_de
├─ unibet
├─ unibet_fr
├─ unibet_nl
├─ unibet_se
├─ williamhill
└─ williamhill_us
    (+ winamax_de, winamax_fr = 30 total for 2⭐)

0⭐ TARGET AU BOOKS (Surface EV opportunities - 15 books)
├─ betfair_ex_au
├─ betr_au
├─ betright
├─ boombet
├─ dabble_au
├─ ladbrokes_au
├─ neds
├─ playub
├─ pointsbetau
├─ sportsbet
├─ tab
├─ tabtouch
├─ betparx
├─ ballybet
└─ bet365 (NEW - currently AFL/NRL only, empty for NBA)
```

---

## Issues to Confirm

1. **5th 3⭐ Book:** You specified 5 sharpest for 3⭐. I have 4 (Betonlineag, Betrivers, Betsson, Lowvig). What's the 5th?

2. **Betparx & Ballybet:** Currently in 2⭐ secondary. Move to 0⭐ target AU? Or keep as 2⭐?

3. **Bet365:** You mentioned adding bet365 to AU list. Should it be in 0⭐ with other AU targets?

4. **Winamax variants:** Should winamax_de and winamax_fr be in 2⭐ or moved elsewhere?

**Questions:**
- What's the 5th 3⭐ book?
- Confirm the 15 AU/target books final list?
- Confirm final total order?

Once confirmed, I'll create:
1. `bookmaker_ratings.py` with all mappings
2. Update `extract_nba_v3.py` ALL_BOOKMAKERS to this exact order
3. Commit with note: "This order is FINAL for all future CSVs"
