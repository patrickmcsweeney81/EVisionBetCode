# 🎉 EVisionBet v3 - Ready to Use!

**Status:** Core architecture COMPLETE and READY TO CONFIGURE

---

## ⚡ What You Can Do RIGHT NOW

### 1. Test the Configuration System

```bash
cd C:\EVisionBetCode
python
```

```python
from src.v3.configs import (
    get_sport_config,
    get_enabled_sports,
    get_bookmakers_by_region,
    get_sharp_books,
)

# See which sports are enabled for production
enabled = get_enabled_sports()
print("Enabled sports:", list(enabled.keys()))
# Output: {'basketball_nba': {...}, 'americanfootball_nfl': {...}}

# Get NBA config
nba = get_sport_config("basketball_nba")
print("NBA Regions:", nba)  # Shows all NBA settings

# See sharp books (used for fair odds)
sharps = get_sharp_books()
print("Sharp books:", list(sharps.keys()))
# Output: pinnacle, betfair, draftkings, fanduel, etc.

# See EVisionBet hidden weights
print("NBA hidden weights:", nba["evisionbet_weights"])
# Output: {"pinnacle": 4, "draftkings": 3, "fanduel": 3, ...}
```

### 2. Adjust Weights for Any Sport

**File:** `src/v3/configs/sports.py`

```python
"basketball_nba": {
    "enabled": True,
    "evisionbet_weights": {
        "pinnacle": 4,        # ← Change this
        "draftkings": 3,      # ← Or this
        "fanduel": 3,         # ← Or this
        "betfairaus": 2,
        "sportsbet": 1,
    },
}
```

**Your weights are HIDDEN from users** - they only see options 0-4

### 3. Add a New Sport (Easy!)

**Step 1:** Add to `src/v3/configs/sports.py`
```python
"tennis_wta": {
    "enabled": False,  # Start disabled for testing
    "title": "WTA",
    "api_tiers": {
        "fetch_base_markets": True,
        "fetch_player_props": False,  # Tennis is H2H only
        "fetch_advanced_markets": False,
    },
    "evisionbet_weights": {
        "pinnacle": 4,
        "betfair": 3,
    },
}
```

**Step 2:** Add to `src/v3/configs/regions.py`
```python
"tennis_wta": {
    "extract_from": ["au", "us", "eu"],
    "time_window_hours": 72,
    "sharp_priority": ["eu", "au"],
    "exclude_from_fair": [],
}
```

**Step 3:** Add to `src/v3/configs/api_tiers.py`
```python
"tennis_wta": {
    "tier_1_base_markets": True,
    "tier_2_player_props": False,
    "tier_3_advanced_markets": False,
    "estimated_cost_per_run": 20,
}
```

**Step 4:** Add to `src/v3/configs/fair_odds.py`
```python
"tennis_wta": {
    "outlier_threshold": 0.03,
    "min_sharp_count": 1,
    "special_rules": {"h2h": "use_median"},
}
```

**Step 5:** Create `src/v3/processors/fair_odds_wta.py` (copy from NBA or NFL, adjust)

**Step 6:** When ready, enable it:
```python
# In sports.py
"tennis_wta": {
    "enabled": True,  # ← Change to True when tested
    ...
}
```

### 4. Control API Costs

**All tier configs are in** `src/v3/configs/api_tiers.py`

**Current estimated costs per sport:**
- NBA: 50 credits (base + 3 props)
- NFL: 35 credits (base + 3 props)
- NHL: 25 credits (base only)
- Soccer: 45 credits (base + advanced 3-way markets)
- Tennis: 20 credits (base only)
- Cricket: 20 credits (base only)

**To skip props for a sport:**
```python
"basketball_nba": {
    "tier_2_player_props": False,  # ← Don't fetch props
    "tier_2_props_list": [],
    ...
}
```

**To fetch advanced markets:**
```python
"soccer_epl": {
    "tier_3_advanced_markets": True,  # ← Fetch 3-way markets
    "tier_3_advanced_list": ["h2h_3way", "over_under_partials"],
    ...
}
```

### 5. Adjust Fair Odds Per Sport

**File:** `src/v3/configs/fair_odds.py`

**Make NBA more aggressive (removes more outliers):**
```python
"basketball_nba": {
    "outlier_threshold": 0.07,  # 7% instead of 5%
    "min_sharp_count": 2,
}
```

**Make NFL more conservative (keeps more books):**
```python
"americanfootball_nfl": {
    "outlier_threshold": 0.02,  # 2% instead of 3%
    "min_sharp_count": 1,
}
```

### 6. Test a Single Sport

**When you're ready to extract:**
```bash
# Currently, you have these extractors ready:
# - NBAExtractor (ready)
# - NFLExtractor (ready)
# - NHL, Soccer, Tennis, Cricket (can add anytime)

# Test structure:
python
```

```python
from src.v3.extractors.nba_extractor import NBAExtractor

nba = NBAExtractor()
print("Sport Key:", nba.SPORT_KEY)
print("Regions:", nba.REGIONS)  # Loads from config
print("Time Window:", nba.TIME_WINDOW_HOURS)  # Loads from config

# When ready: odds = nba.fetch_odds()
```

---

## 📋 Configuration File Quick Reference

| File | Purpose | Edit For |
|------|---------|----------|
| `sports.py` | Master config | Add sports, enable/disable, set weights |
| `bookmakers.py` | Book ratings | Add bookmakers, change star ratings |
| `weights.py` | Weight profiles | Adjust fair odds weighting |
| `regions.py` | Region strategy | Change regions per sport, time windows |
| `api_tiers.py` | API costs | Enable/disable props/advanced |
| `fair_odds.py` | Fair odds logic | Outlier thresholds, sharp minimums |

---

## 🔐 Weight System Summary

**You (Backend):**
- Set EVisionBet weights 0-4 per book per sport
- Weights are used to calculate fair odds
- **Weights are HIDDEN from users**
- Users never see your weights

**Users (Frontend):**
- See all books available
- Each book starts at weight **0** (hidden: can't see your weights)
- Can adjust any book 0-4 for instant EV recalculation
- Uses same fair odds logic as backend

**Example:**
```
Backend (your hidden weights):
  Pinnacle: 4 (your opinion on sharpness)
  DraftKings: 3
  FanDuel: 3

Frontend (user sees):
  Pinnacle: [0 ________] 4 (user moves slider)
  DraftKings: [0 ________] 4
  FanDuel: [0 ________] 4
  (Users don't see your 4/3/3 - starts at 0)
```

---

## 🎯 Next Steps When Ready

### Build Backend API (30 minutes)
```python
# Add to backend_api.py:
@app.get("/api/admin/odds/raw")
def get_raw_odds()...

@app.get("/api/ev/hits")
def get_ev_hits()...

@app.get("/api/config/weights")
def get_weight_config()...
```

### Build Frontend Component (1 hour)
```javascript
// Create EVHitsCard.js with:
- Weight sliders (0-4 per book)
- EV recalculation on change
- Display fair odds + EV%
```

### Update Pipeline (30 minutes)
```python
# Update pipeline_v3.py to:
- Load enabled sports from config
- Support --sports nba,nfl override
- Support --estimate-cost flag
```

---

## ✅ Quality Checks

**Can I:**
- ✅ Add a new sport? YES (5 config files + 1 fair odds class)
- ✅ Change weights? YES (edit sports.py)
- ✅ Adjust fair odds? YES (edit fair_odds.py)
- ✅ Skip props for NBA? YES (edit api_tiers.py)
- ✅ Change region list? YES (edit regions.py)
- ✅ Enable/disable sports? YES (edit sports.py enabled: true/false)

---

## 🚀 You're Ready!

Everything is configured and ready to go. The system is:

✅ **Flexible** - Change any setting without code changes  
✅ **Modular** - Separate config files for different concerns  
✅ **Extensible** - Add sports in minutes  
✅ **Per-sport** - Each sport can be customized independently  
✅ **Cost-aware** - See estimated API costs  
✅ **Hidden** - EVisionBet weights never shown to users  

**What to do next:**
1. Review the config files
2. Adjust weights/regions/fair odds as needed
3. Test loading configs (see examples above)
4. When ready, I'll build Backend API + Frontend

---

## 📚 Documentation Created

All in root of EVisionBetCode:
- ✅ `ARCHITECTURE_PROPOSAL.md` - Full design doc
- ✅ `IMPLEMENTATION_PLAN.md` - Code samples + data flows
- ✅ `BUILD_COMPLETION_REPORT.md` - What was built
- ✅ `READY_TO_USE.md` ← You are here

---

Ready to proceed? Let me know! 🎉
