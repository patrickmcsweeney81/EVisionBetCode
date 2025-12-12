# EVisionBetCode – Custom Bookmaker CSV Build Guide

## Bookmaker Column Order (2025)

This is the required order for bookmaker columns in all CSV outputs and data tables. Use this order for both backend processing and frontend display.

### 1. Sharpest Global Books
1. Pinnacle
2. Betfair_AU
3. Betfair_EU
4. Draftkings
5. Fanduel
6. Betmgm
7. Betonline
8. Bovada
9. Lowvig
10. Mybookie
11. Marathonbet
12. Matchbook
13. Williamhill_US
14. Betrivers
15. Betus

### 2. AU-Licensed Books
16. Sportsbet
17. Pointsbet
18. Tab
19. Tabtouch
20. Unibet_AU
21. Ladbrokes_AU
22. Neds
23. Betr
24. Boombet
25. Betright
26. Dabble_Au
27. Playup
28. Bet365_AU

### 3. Other/Global Books
29. Betsson
30. Nordicbet
31. Fanatics
32. Ballybet
33. Betparx
34. Espnbet
35. Fliff
36. Hardrockbet
37. Rebet
38. Williamhill_UK
39. Codere
40. Tipico
41. Leovegas
42. Parionssport
43. Winamax_FR
44. Winamax_DE
45. Unibet_FR
46. Unibet_NL
47. Unibet_SE
48. Betclic
49. Betanysports
50. Coolbet
51. Everygame
52. Gtbets
53. Onexbet
54. Sport888

---

## Usage
- Always use this order for CSV columns and data processing.
- Place all non-bookmaker columns (event info, market, etc.) before this list (see next step).
- Update backend and frontend code to match this order for consistency and easier expansion.

---

## Next Step
- Specify which columns you want before the bookmaker columns (e.g., event_id, market, etc.).
- We will finalize the full CSV schema and update the pipeline accordingly.
