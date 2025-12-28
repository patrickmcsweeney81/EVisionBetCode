# 📚 WHY DIFFERENT BOOKS OFFER DIFFERENT POINT VALUES
**Research Summary:** December 28, 2025

---

## Key Concept: Vigorish (The "Vig")

**Definition:** The fee/margin charged by a bookmaker for accepting a bet. It's how they guarantee profit regardless of the outcome.

**Formula:** For -6.5 to -8.0 variations, the vig is built into the **odds**, not just the point.

---

## Why Books Use Different Point Values

### 1. **Risk Management & Margin Control**

**Pinnacle (Sharp Book) @ -8.0:**
- Offers a "tighter" line (larger spread)
- Odds: 1.96 for Knicks
- Reason: Taking less action, so they need better odds to attract bets
- Lower vigorish (2-3% edge) = less margin, but attracts sharp bettors

**FanDuel (Target Book) @ -6.5:**
- Offers a "looser" line (smaller spread)  
- Odds: 1.69 for Knicks (worse than Pinnacle)
- Reason: Taking more action with worse odds, so higher vigorish (4-5% edge)
- Makes money on volume and margin

### 2. **Balancing Action (Most Important)**

Sportsbooks don't want to pick winners—they want balanced betting.

**Example from the data:**
```
If FanDuel sees $10,000 bet on Knicks @ -6.5
And only $5,000 bet on Hawks @ +6.5
Book is exposed to $5,000 loss if Knicks wins

Solution: Move the line
- Offer worse odds on Knicks
- Offer better odds on Hawks
- Until action balances

OR adjust the POINT VALUE
- Move from -6.5 to -7.5
- This makes Hawks look more attractive
- Encourages bets on Hawks
```

### 3. **Different Customer Base = Different Exposure**

**Pinnacle's Model:**
- Takes bets from professional/sharp bettors
- These bettors are accurate, so Pinnacle needs:
  - Tighter lines (bigger point spreads)
  - Lower margins (better odds)
  - To avoid being "caught out"

**FanDuel's Model:**
- Takes bets from casual bettors
- Casual bettors tend to pick favorites
- So FanDuel:
  - Looser lines (smaller spreads)
  - Higher margins (worse odds)
  - Can profit from the vig even if casual bettors are right

### 4. **Historical/Market Positioning**

```
Knicks are FAVORITES. Everyone wants to bet them.

Pinnacle @ -8.0:
  "We think Knicks is worth -8.0"
  (Most pessimistic on Knicks)
  High odds (1.96) to compensate
  
DraftKings @ -7.5:
  "Middle ground"
  Balanced action expected
  Mid-range odds (1.95)
  
FanDuel @ -6.5:
  "We know our customers bet favorites"
  Need looser line to limit exposure
  Low odds (1.69) to take margin
  (Most optimistic on Knicks)
```

---

## The Math Behind It

**Vigorish Formula:**
```
For even-odds market without vig: 2.0 / 2.0
With vig:                        1.90 / 2.00 (4.55% vig)
With higher vig:                 1.85 / 2.10 (higher vig)

Vigorish = 100 × (1 - pq / (p+q))
Where p, q = decimal payouts each side
```

**Applied to our example:**
```
Pinnacle @ -8.0:
  Odds: 1.96 / 1.96 ≈ 2.27% vigorish (SHARP, low margin)

FanDuel @ -6.5:
  Odds: 1.69 / 1.89 ≈ 4.2% vigorish (TARGET, higher margin)

DraftKings @ -7.5:
  Odds: 1.95 / 1.83 ≈ 3.1% vigorish (MIDDLE)
```

---

## Why This Matters for EV Calculation

### The Challenge:

**You can't directly compare:**
```
FanDuel -6.5 @ 1.69 vs Pinnacle -8.0 @ 1.96
```

**Because the 1.5-point difference changes the value:**
```
Option A: Bet Knicks @ -6.5 for 1.69
  - If Knicks wins by 7+: You WIN
  - If Knicks wins by exactly 6: PUSH
  - If Knicks loses by 1-5: You LOSE
  
Option B: Bet Knicks @ -8.0 for 1.96
  - If Knicks wins by 9+: You WIN
  - If Knicks wins by exactly 8: PUSH
  - If Knicks loses by 1-7: You LOSE
```

**The odds are different because the requirement is different.**

---

## Solution: Point Normalization

To compare apples-to-apples, you need to:

### Step 1: Normalize to a "Market Consensus" Point
```
Books offer:
  -6.5, -7.0, -7.5, -8.0, -8.5

Consensus range:
  -7.0 to -7.5 (most books cluster here)

Use -7.5 as standard point
```

### Step 2: Interpolate Odds to Standard Point

If FanDuel offers -6.5 @ 1.69, and Pinnacle offers -8.0 @ 1.96:

```
Adjust FanDuel odds DOWN (account for looser line)
Adjust Pinnacle odds UP (account for tighter line)

Normalize both to -7.5

This accounts for the point difference
```

### Step 3: Calculate Fair Odds from Sharp Books

```
Normalized Pinnacle -7.5: ~1.94 (adjusted)
Normalized BetRivers -8.0: ~1.87 (adjusted)

Fair odds at -7.5 = weighted average = ~1.91
```

### Step 4: Compare Target Books

```
FanDuel @ -6.5: 1.69
Adjusted to -7.5: ~1.78 (accounting for 1-point difference)

vs Fair odds: 1.91

EV = (1.78 / 1.91) - 1 = -6.8% (NEGATIVE, no bet)
```

---

## Why This Explains the Data

```
Knicks vs Hawks Example:

Pinnacle (Sharp):  -8.0 @ 1.96 ← Tightest, highest odds
BetRivers (Sharp): -8.0 @ 1.87 ← Tight, lower odds
DraftKings (Mid):  -7.5 @ 1.95 ← Middle ground
BetMGM (Mid):      -7.5 @ 1.91 ← Middle ground
FanDuel (Target):  -6.5 @ 1.69 ← Loosest, lowest odds

Pattern:
- Tighter books = higher odds (better for bettors)
- Looser books = lower odds (better for books)
- Point value tracks book type
```

---

## Implications for EV Code

### What You Need:

1. **Point Normalization Engine**
   - Map all offerings to standard point (-7.5)
   - Account for 0.5-point increments = ~0.02-0.03 odds shift

2. **Book Categorization**
   - Identify each book's tier (sharp/medium/target)
   - Sharps offer tight lines (higher points)
   - Targets offer loose lines (lower points)

3. **Fair Odds from Sharps Only**
   - Use tight-book offerings
   - Interpolate to standard point
   - Weighted average = fair line

4. **Opportunity Finding vs Targets**
   - Compare target books (loose lines) to fair odds
   - Only after normalizing to same point value

### Example Algorithm:

```python
def normalize_spread_market(event_spreads):
    """
    Input: All bookmaker lines for one spread
      - FanDuel: -6.5 @ 1.69
      - DraftKings: -7.5 @ 1.95
      - Pinnacle: -8.0 @ 1.96
    
    Step 1: Identify market consensus point (-7.5)
    Step 2: Adjust each book's odds to -7.5 point
      - FanDuel: interpolate -6.5 to -7.5 = 1.78 (worse odds)
      - DraftKings: already -7.5 = 1.95
      - Pinnacle: interpolate -8.0 to -7.5 = 1.94 (better odds)
    
    Step 3: Calculate fair odds from sharps (Pinnacle + BetRivers)
      - Fair @ -7.5 = 1.91
    
    Step 4: Find EV in target books
      - FanDuel adjusted: 1.78 vs fair 1.91 = -6.8% (no bet)
    
    Output: Normalized data ready for EV calculation
    """
```

---

## Key Takeaway

**Books offer different point values because:**
1. They manage risk differently
2. They have different customer bases
3. They adjust to balance action
4. They apply different vigorish percentages

**For EV calculation:**
- You MUST normalize to the same point before comparing
- Point value tells you about the book (sharp = tight = high point)
- Sharp books = source of true odds
- Target books = source of opportunities

---

**Research Sources:**
- Wikipedia: Vigorish article
- Industry knowledge: Sharp vs target book behaviors

**Next Step:** Build point normalization engine for spreads/totals alignment
