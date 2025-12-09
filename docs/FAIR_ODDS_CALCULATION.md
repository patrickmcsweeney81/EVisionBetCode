# Fair Odds Calculation - Technical Explanation

## Overview
Fair odds represent the "true" market price without bookmaker margins. We calculate this by analyzing odds from 15 sharp bookmakers and removing their built-in profit margin (vig).

---

## The 4-Step Process

### Step 1: Collect Sharp Bookmaker Odds
We only use bookmakers known for sharp lines and high limits. **Both sides required** (Over AND Under, or both teams in H2H).

**Example: LeBron James Over/Under 25.5 Points**

| Sharp Bookmaker | Over Odds | Under Odds |
|----------------|-----------|------------|
| Pinnacle       | 1.92      | 1.95       |
| DraftKings     | 1.87      | 2.00       |
| FanDuel        | 1.90      | 1.98       |
| BetMGM         | 1.88      | 1.99       |
| Betfair EU     | 1.91      | 1.96       |

**Why median instead of average?**  
Median is resistant to outliers. If one bookmaker has stale odds (e.g., 2.50 while others are 1.90), the median ignores it.

---

### Step 2: Remove Bookmaker Margin ("Devig")

Bookmakers add margin to ensure profit. Notice above: probabilities sum to **>100%** (overround).

**Proportional Devig Formula:**
```
Over Implied Prob = 1 / Over Odds
Under Implied Prob = 1 / Under Odds
Total = Over Prob + Under Prob

Fair Over Prob = Over Prob / Total
Fair Under Prob = Under Prob / Total

Fair Over Odds = 1 / Fair Over Prob
Fair Under Odds = 1 / Fair Under Prob
```

**Example (Pinnacle):**
```
Over: 1/1.92 = 0.5208 (52.08%)
Under: 1/1.95 = 0.5128 (51.28%)
Total: 1.0336 (103.36% → 3.36% margin)

Fair Over: 0.5208 / 1.0336 = 0.5039 → 1.9845 odds
Fair Under: 0.5128 / 1.0336 = 0.4961 → 2.0157 odds
```

After devigging all 5 sharp books:
- Over: [1.9845, 1.9355, 1.9650, 1.9450, 1.9745]
- Under: [2.0157, 2.0655, 2.0450, 2.0550, 2.0255]

---

### Step 3: Calculate Median (Consensus Fair Odds)

**Over Odds Sorted:** [1.9355, 1.9450, **1.9650**, 1.9745, 1.9845]  
**Median Over Fair Odds:** **1.9650**

**Under Odds Sorted:** [2.0157, 2.0255, **2.0450**, 2.0550, 2.0655]  
**Median Under Fair Odds:** **2.0450**

These are our "true market" prices.

---

### Step 4: Calculate EV Against Target Bookmakers

Now we check if Australian bookmakers offer better odds than fair value.

**Example: Sportsbet offers 2.05 on Over**

```
EV% = (Sportsbet Odds / Fair Odds - 1) × 100
EV% = (2.05 / 1.9650 - 1) × 100
EV% = 4.33%
```

**✓ Bet Recommended** (above 1% threshold)

---

## Sharp Bookmaker List (15 Total)

Our system uses these bookmakers to establish fair odds:

**Global Sharps:**
- Pinnacle (industry standard)
- Betfair Exchange (AU/EU/UK)
- MarathonBet
- Betsson
- Nordicbet

**US Majors:**
- DraftKings
- FanDuel
- BetMGM
- BetRivers

**Offshore:**
- BetOnline
- Bovada
- LowVig
- MyBookie

---

## Minimum Requirements

| Requirement | Value | Reason |
|------------|-------|--------|
| Min Sharp Books | 2 | Prevents single-source manipulation |
| Both Sides Required | Yes | Ensures complete market coverage |
| Min EV Threshold | 1% | Filters noise, practical edge |
| Devig Method | Proportional | Industry standard, fair removal |
| Consensus Method | Median | Outlier resistant |

---

## Real Output Example

From `ev_opportunities.csv`:

```csv
player,selection,best_book,odds_decimal,fair_odds,ev_percent,sharp_book_count
LeBron James,Over 25.5,Sportsbet,2.0500,1.9650,4.33%,5
```

**Interpretation:**
- **Fair odds:** 1.9650 (derived from 5 sharp sources)
- **Sportsbet odds:** 2.05
- **Edge:** 4.33% positive expectation
- **Confidence:** High (5 sharps agree)

---

## Why This Method Works

1. **Sharp bookmakers** have sophisticated pricing models and handle large bets → their odds reflect true probabilities
2. **Median consensus** averages out individual bookmaker biases
3. **Devigging** removes artificial margin, revealing true probability
4. **Australian books** often copy US/EU lines with delays → create exploitable edges

---

## Code Implementation

See `pipeline_v2/calculate_ev.py`:
- `devig_two_way()` - Removes bookmaker margin
- `fair_from_sharps()` - Collects and processes sharp odds
- `process_two_way_markets()` - Identifies EV opportunities

**Key Variables:**
```python
SHARP_COLS = [
    "Pinnacle", "Betfair_EU", "Betfair_UK", "Betfair_AU",
    "Draftkings", "Fanduel", "Betmgm", "Betonline", "Bovada",
    "Lowvig", "Mybookie", "Betrivers", "Marathonbet", "Betsson", "Nordicbet"
]
MIN_BOOKMAKER_COVERAGE = 2  # Minimum sharps required
EV_MIN_EDGE = 0.01  # 1% minimum EV threshold
```
