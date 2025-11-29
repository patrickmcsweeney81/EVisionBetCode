# Future Enhancement Ideas

This file contains ideas for potential future improvements to the EV bot. These are not currently implemented but could be valuable additions.

---

## 1. Time-Based Odds Filtering

**Concept:** Skip odds that are older than X minutes to avoid stale data.

**Implementation Approach:**
- The Odds API provides `last_update` timestamp for each bookmaker
- Could add `MAX_ODDS_AGE_MINUTES` config (e.g., 5 minutes)
- Filter bookmakers where `now - last_update > MAX_ODDS_AGE_MINUTES`
- This would ensure fair price calculations only use fresh odds

**Benefits:**
- Reduces impact of stale/suspended bookmakers
- More accurate fair prices
- Better reflects current market conditions

**Considerations:**
- Some sharp books (Pinnacle) update less frequently but are still accurate
- May reduce number of bookmakers available for fair price calculation
- Need to balance freshness vs. sample size

**Config Example:**
```properties
MAX_ODDS_AGE_MINUTES=5  # Skip bookmaker odds older than 5 minutes
EXEMPT_BOOKMAKERS=pinnacle,betfair_ex_au  # Always include these (sharps)
```

---

## 2. Track Bookmaker Outlier Frequency

**Concept:** Monitor which bookmakers are frequently identified as outliers.

**Implementation Approach:**
- Keep rolling statistics for each bookmaker
- Track: times_included, times_outlier, outlier_rate
- Store in JSON file: `data/bookmaker_stats.json`
- Could auto-exclude bookmakers with high outlier rates (>30%)

**Benefits:**
- Identify consistently unreliable bookmakers
- Auto-filter problematic data sources
- Provide visibility into bookmaker quality

**Data Structure:**
```json
{
  "marathonbet": {
    "times_included": 1000,
    "times_outlier": 45,
    "outlier_rate": 0.045,
    "last_updated": "2025-11-11T12:00:00Z"
  },
  "pinnacle": {
    "times_included": 950,
    "times_outlier": 2,
    "outlier_rate": 0.002
  }
}
```

**Config Example:**
```properties
TRACK_OUTLIER_STATS=1  # Enable tracking
AUTO_EXCLUDE_OUTLIER_RATE=0.30  # Auto-exclude if >30% outlier rate
MIN_SAMPLES_FOR_EXCLUSION=100  # Need at least 100 samples before excluding
```

---

## 3. Fair Price Change Alerts

**Concept:** Alert when fair price changes significantly between consecutive runs.

**Implementation Approach:**
- Store previous run's fair prices in memory or temp file
- Compare current fair price to previous for same event/market
- Alert if change exceeds threshold (e.g., 5% or 10%)
- Could indicate market movement or data issues

**Benefits:**
- Catch rapid market movements (injury news, lineup changes)
- Identify potential data quality issues
- Validate fair price calculation consistency

**Alert Example:**
```
⚠️ FAIR PRICE ALERT
Event: Dallas Mavericks vs Milwaukee Bucks
Market: H2H - Dallas Mavericks
Previous Fair: $2.13
Current Fair: $2.42 (+13.6%)
Possible cause: Market movement or data issue
```

**Config Example:**
```properties
FAIR_PRICE_CHANGE_ALERTS=1  # Enable alerts
FAIR_PRICE_CHANGE_THRESHOLD=0.10  # Alert if >10% change
TELEGRAM_PRICE_CHANGE_ALERTS=1  # Send to Telegram
```

---

## 4. Bookmaker Bet Limit Tracking

**Concept:** Manually track which bookmakers have limited your account.

**Implementation Approach:**
- Simple JSON file: `data/bookmaker_limits.json`
- Record bookmaker, date limited, estimated max stake
- Bot can warn or auto-skip limited bookmakers

**Data Structure:**
```json
{
  "sportsbet": {
    "limited": true,
    "date_limited": "2025-10-15",
    "max_stake_estimate": 50,
    "notes": "Limited after 20 winning bets"
  },
  "pointsbetau": {
    "limited": false,
    "max_stake_estimate": 500
  }
}
```

**Config Example:**
```properties
SKIP_LIMITED_BOOKMAKERS=1  # Don't log bets on limited accounts
WARN_LIMITED_BOOKMAKERS=1  # Show warning in output
```

---

## 5. Historical Hit Success Tracking

**Concept:** Track actual outcomes of placed bets to measure performance.

**Implementation Approach:**
- Add "result" column to CSV (win/loss/push/pending)
- Calculate actual ROI vs. expected EV
- Validate fair price calculation accuracy
- Identify which bookmakers/markets perform best

**Benefits:**
- Measure real-world performance
- Verify fair price calculation methodology
- Optimize bookmaker/market selection
- Build confidence in system

**Extended CSV:**
```csv
timestamp_perth,sport,event,result,actual_profit,expected_profit,...
2025-11-11 14:30:00,basketball_nba,Lakers vs Celtics,win,$52.30,$48.20
```

---

## 6. Dynamic Fair Price Weighting

**Concept:** Adjust Pinnacle/Betfair/Median weights based on market type or sport.

**Current:** Fixed 50%/30%/20% weights
**Enhanced:** Sport-specific or market-specific weights

**Example:**
```properties
# Basketball weights (Pinnacle very sharp on NBA)
FAIR_WEIGHT_PINNACLE_BASKETBALL=0.60
FAIR_WEIGHT_BETFAIR_BASKETBALL=0.25
FAIR_WEIGHT_SHARPS_BASKETBALL=0.15

# Soccer weights (exchange liquidity is better)
FAIR_WEIGHT_PINNACLE_SOCCER=0.40
FAIR_WEIGHT_BETFAIR_SOCCER=0.40
FAIR_WEIGHT_SHARPS_SOCCER=0.20
```

---

## 7. Multi-Sport Optimization

**Concept:** Different thresholds/settings per sport.

**Example:**
```properties
# NBA (liquid, many games)
EV_MIN_EDGE_BASKETBALL_NBA=0.03
MIN_PROB_BASKETBALL_NBA=0.25

# NHL (less liquid, fewer games)
EV_MIN_EDGE_ICEHOCKEY_NHL=0.04
MIN_PROB_ICEHOCKEY_NHL=0.20

# MLB (high variance)
EV_MIN_EDGE_BASEBALL_MLB=0.05
MIN_PROB_BASEBALL_MLB=0.30
```

---

## 8. Event Urgency Escalation

**Concept:** Different handling for games starting very soon.

**Current:** Just filters by MIN_TIME_TO_START_MINUTES
**Enhanced:** Escalate urgency alerts for games <30 minutes

**Example Alert:**
```
🚨 URGENT: Game starts in 18 minutes!
Dallas Mavericks vs Milwaukee Bucks
EV: 4.2% | Betfair $2.16 | Fair: $2.07
Place bet NOW!
```

---

## Priority Ranking

If implementing these, suggested order:

1. **Fair Price Change Alerts** (Quick win, high value for validation)
2. **Bookmaker Outlier Tracking** (Improves data quality visibility)
3. **Time-Based Odds Filtering** (Improves fair price accuracy)
4. **Bookmaker Limit Tracking** (Practical for long-term use)
5. **Historical Success Tracking** (Requires manual result entry)
6. **Dynamic Weighting** (Advanced, requires testing)
7. **Multi-Sport Optimization** (Nice-to-have after more data)
8. **Event Urgency** (Low priority, already have time filters)

---

## Notes

- Most of these would add <50 lines of code each
- Could be toggled on/off via .env configuration
- Would require minimal changes to core logic
- Focus should remain on accuracy and simplicity first
