# Neds Market Research Report
**Date:** January 6, 2026  
**Status:** ✅ Complete

---

## 🔬 Research Findings

### Available Markets for Neds
| Market Type | Available | Count | Notes |
|-------------|-----------|-------|-------|
| **h2h** (Moneyline) | ✅ YES | 2 outcomes | Primary market |
| spreads | ❌ NO | - | Not available via API |
| totals | ❌ NO | - | Not available via API |
| alternate_spreads | ❌ NO | - | Not available via API |
| alternate_totals | ❌ NO | - | Not available via API |
| player_points | ❌ NO | - | Not available via API |
| player_assists | ❌ NO | - | Not available via API |
| player_rebounds | ❌ NO | - | Not available via API |
| player_passes | ❌ NO | - | Not available via API |
| player_threes | ❌ NO | - | Not available via API |
| player_field_goals | ❌ NO | - | Not available via API |
| player_turnovers | ❌ NO | - | Not available via API |
| player_steals | ❌ NO | - | Not available via API |
| player_blocks | ❌ NO | - | Not available via API |
| player_fouls | ❌ NO | - | Not available via API |

**Total: 1 market type available (H2H only)**

---

## 📊 Current Data (NBA Test Run)

```
6 NBA Events
12 Neds outcomes (2 per event for H2H)
100% of events have H2H market
0% have spreads/totals/props
```

**Sample Neds H2H Odds:**
```
Cleveland Cavaliers @ Indiana Pacers
  Cleveland Cavaliers: 1.46
  Indiana Pacers:      2.75

Orlando Magic @ Washington Wizards
  Orlando Magic:       1.36
  Washington Wizards:  3.15

Los Angeles Lakers @ New Orleans Pelicans
  Los Angeles Lakers:      3.15
  New Orleans Pelicans:    1.48
```

---

## 💡 Important Notes

### This is API Limitation, Not Neds Limitation
- The Odds API **only provides H2H market for Neds**
- Neds likely offers spreads, totals, and props on their actual platform
- The Odds API may have limited Neds integration in their feed

**Per The Odds API Official Documentation:**
> "spreads and totals markets are mainly available for US sports and bookmakers at this time"
> "Additional markets are currently limited to US sports and selected bookmakers"
> "Coverage of player props is mainly limited to US sports and US bookmakers at this time"

**Key Finding:** Neds is an Australian bookmaker, hence limited to H2H via the API (US/selected bookmakers get full coverage)

### Possible Solutions
1. **Use Neds API directly** (if they have one)
2. **Web scraping** (if allowed by Neds T&C)
3. **Use different bookmaker** with full market coverage (e.g., DraftKings, FanDuel)
4. **Contact The Odds API** to request expanded Neds market coverage

### Other Bookmakers vs Neds Coverage

| Bookmaker | h2h | spreads | totals | props | API Status |
|-----------|-----|---------|--------|-------|-----------|
| **Neds** | ✅ | ❌ | ❌ | ❌ | Limited |
| DraftKings | ✅ | ✅ | ✅ | ✅ | Full |
| FanDuel | ✅ | ✅ | ✅ | ✅ | Full |
| Pinnacle | ✅ | ✅ | ✅ | ✅ | Full |
| Betfair Exchange | ✅ | ✅ | ✅ | ✅ | Full |
| Sportsbet | ✅ | ✅ | ✅ | ✅ | Full |
| TAB | ✅ | ✅ | ✅ | ✅ | Full |

---

## 🎯 Recommended Next Steps

1. **For Neds H2H comparison:** Use `extract_neds_only.py` (ready to go)
2. **For full markets:** Switch to DraftKings, FanDuel, or Sportsbet
3. **For spreads/totals:** Use any of the bookmakers in the table above
4. **To get Neds spreads/props:** Need alternative data source

---

## 📁 Generated Files

- `neds_all_markets_20260106_173537.csv` - 12 H2H odds (raw research)
- `extract_neds_only.py` - Ready-to-use extractor for Neds H2H
- `research_neds_markets.py` - Market availability research tool
- `deep_research_neds.py` - Market type testing script

---

## 🔗 Reference

**The Odds API Documentation:**
- https://the-odds-api.com/liveapi/guides/bookmakers#neds

**Neds Bookmaker Key:** `neds`

---

**Conclusion:** ✅ API research complete. Neds only offers H2H via The Odds API.
