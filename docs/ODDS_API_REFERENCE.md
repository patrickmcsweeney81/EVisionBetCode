# Odds API Integration Reference

**Last Updated:** December 26, 2025  
**API Version:** v4  
**Status:** Production  
**Repository:** https://github.com/the-odds-api/odds-api

---

## 📋 API Contract

### Service Details
- **Provider:** The Odds API
- **Base URL:** https://api.the-odds-api.com/v4
- **Version:** v4 (current stable)
- **Auth Method:** Query parameter `apiKey`
- **Response Format:** JSON
- **Rate Limit (Free):** 500 requests/month

### Rate Limit Strategy
```
Free Tier: 500/month (~16/day for daily extraction)
Our Usage: ~50-60 per daily run (NBA + NFL + future sports)
Buffer: Safe with weekly+ad-hoc runs, avoid hourly calls
```

### Environmental Variable
```python
# .env
ODDS_API_KEY=<your_api_key>

# Code usage
from os import getenv
api_key = getenv("ODDS_API_KEY")
```

---

## 🔌 Endpoints Used

### 1. `/sports` - Available Sports
```
GET /sports
Query: apiKey={key}
Response: List of all available sports with keys

Used By: src/pipeline_v2/extract_odds.py (verify sports before extraction)
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    { "key": "americanfootball_nfl", "active": true, "title": "NFL" },
    { "key": "basketball_nba", "active": true, "title": "NBA" }
  ]
}
```

### 2. `/sports/{sport}/odds` - Odds for Sport
```
GET /sports/{sport}/odds
Query: 
  - apiKey={key}
  - regions={regions}  (comma-separated: us,us2,au,etc)
  - markets={markets}  (comma-separated: h2h,spreads,totals,player_props)
  - dateFormat=unix or iso
  - oddsFormat=decimal or american

Used By: src/pipeline_v2/extract_odds.py (main extraction)
```

**Query Example:**
```
GET /sports/basketball_nba/odds
  ?apiKey=xxx
  &regions=us,us2,au
  &markets=h2h,spreads,totals,player_props
  &oddsFormat=decimal
```

**Response Structure:**
```json
{
  "success": true,
  "data": [
    {
      "id": "event_id",
      "sport_key": "basketball_nba",
      "sport_title": "NBA",
      "commence_time": 1640001600,
      "home_team": "Home Team",
      "away_team": "Away Team",
      "bookmakers": [
        {
          "key": "draftkings",
          "title": "DraftKings",
          "last_update": 1640001500,
          "markets": [
            {
              "key": "h2h",
              "outcomes": [
                { "name": "Home Team", "price": 1.95 },
                { "name": "Away Team", "price": 1.95 }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 3. `/sports/{sport}/events` - Events Only
```
GET /sports/{sport}/events
Query: apiKey={key}

Used By: Optional (to list games before fetching odds)
```

---

## 🎮 Sports Configuration

### Currently Supported (v4 API)
```
✅ Enabled:
  - americanfootball_nfl (NFL)
  - basketball_nba (NBA)

🔄 Configurable (disabled by default):
  - basketball_nba_g_league
  - americanfootball_college
  - americanfootball_nfl_super_bowl
  - soccer_epl (English Premier League)
  - etc.

Configuration: src/v3/configs/sports.py
```

### Adding New Sport
1. Enable in `sports.py` (set `enabled: true`)
2. Create fair odds class (e.g., `fair_odds_soccer.py`)
3. Create extractor (e.g., `soccer_extractor.py`)
4. Add config entries for regions, API tiers, weights

---

## 📊 Bookmakers Tracked

### Current Lineup (30+ available)

**Sharp Books (3-4 stars):**
- Pinnacle (4⭐) - Most accurate
- Betfair (4⭐) - Sharp action
- Smarkets (3⭐)

**Target Books (1⭐ for EV hunting):**
- DraftKings (1⭐) - US soft book
- FanDuel (1⭐) - US soft book
- BetMGM (1⭐) - US soft book

**Mid-Tier (2⭐):**
- Caesars (2⭐)
- PointsBet (2⭐)
- Others available

**Configuration:** `src/v3/configs/bookmakers.py`

---

## 🎯 Markets Configured

### Head-to-Head (h2h)
```
Moneyline on both teams
Used: Always
Available: All sports
```

### Spreads
```
Point spread markets (team ± points)
Used: NFL, College Football, etc.
Available: Sports with spread markets
```

### Totals
```
Over/Under markets on total points
Used: NFL, NBA, etc.
Available: Most team sports
```

### Player Props
```
Individual player statistics (points, assists, etc.)
Used: NBA, NFL
Available: Limited bookmakers, varies by sport
Cost: Tier 2 endpoint (separate API call)
```

**Markets Excluded:**
- Combination bets
- Fantasy (DFS style)
- Live in-game bets
- Prop parlays

---

## 💰 Cost Estimation

### API Cost Per Run

**Tier 1 (Base Markets):**
```
Per Sport: 1 API call to /odds endpoint
- NBA: ~1 call = 1 request
- NFL: ~1 call = 1 request
- Total: ~2 requests
```

**Tier 2 (Player Props):**
```
Per Sport: Additional /odds call with player_props market
- NBA: +1 call = 1 request
- NFL: +1 call = 1 request
- Total: +2 requests
```

**Tier 3 (Advanced/Future):**
```
Per Sport: Additional specialty markets
- Optional for future expansion
```

### Monthly Budget Example
```
Daily Extraction (Tier 1 only):
  2 requests/day × 30 days = 60 requests/month
  
Monthly Limit (Free): 500 requests
Remaining Buffer: 440 requests (88% buffer)
Risk Level: LOW - Safe for daily runs

If adding Tier 2 (Player Props):
  4 requests/day × 30 days = 120 requests/month
  Remaining: 380 requests (76% buffer)
  Risk Level: LOW - Safe for daily runs

If hourly checks (NOT recommended):
  2 requests/hour × 24 × 30 = 1,440/month
  EXCEEDS LIMIT - Would cost $$ on paid tier
```

### Upgrade Path
```
Free Tier: 500/month
Developer: $99/month (50,000 requests)
Professional: $299/month (500,000 requests)
```

**Decision:** Stay on free tier for daily runs; upgrade only if scaling to real-time or multiple extractions/day.

---

## ⚠️ Error Handling

### Common API Errors

**401 Unauthorized**
```
Cause: Missing/invalid API key
Fix: Check ODDS_API_KEY env var
Response: {"success": false, "message": "unauthorized"}
```

**404 Not Found**
```
Cause: Invalid sport key or market
Fix: Verify sport_key against /sports endpoint
Response: {"success": false, "data": null}
```

**429 Too Many Requests**
```
Cause: Rate limit exceeded
Fix: Wait 1 month (free tier monthly reset) or upgrade
Response: {"success": false, "message": "Rate limit exceeded"}
```

**400 Bad Request**
```
Cause: Invalid query parameters
Fix: Check markets, regions, dateFormat parameters
Response: {"success": false, "message": "..."}
```

### Current Fallback Strategy
```python
# In src/pipeline_v2/extract_odds.py
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"API call failed: {e}")
    # Fallback: Use cached CSV if available
    return load_from_cache("raw_odds_pure.csv")
```

---

## 📈 Monitoring & Upgrades

### Monthly Monitoring Checklist

**Week 1:**
- [ ] Check API status page (https://status.the-odds-api.com)
- [ ] Review latest releases on GitHub

**Week 2:**
- [ ] Verify daily extraction still working
- [ ] Check rate limit usage (estimate vs actual)

**Week 3:**
- [ ] Review API docs for deprecation notices
- [ ] Check for new bookmakers added

**Week 4:**
- [ ] Test with latest API changes (if any)
- [ ] Plan any config updates

### GitHub Monitoring

**Watch These:**
- Releases tab: New versions, breaking changes
- Issues tab: Known bugs, workarounds
- Discussions tab: Community questions

**Link:** https://github.com/the-odds-api/odds-api/releases

### Version Upgrade Plan

**Current:** v4  
**Policy:** Only upgrade after testing in staging

**When v5 Arrives:**
1. Create `test_v5_compat.py` in staging environment
2. Test all endpoints against v5 API
3. Document breaking changes
4. Update config if needed
5. Do NOT auto-upgrade production

---

## 🔄 Data Flow

```
Daily Extraction Schedule:
┌─────────────────────────────────────┐
│ Pipeline starts (config-driven)     │
├─────────────────────────────────────┤
│ 1. Get enabled sports from config   │
│ 2. Estimate API cost                │
│ 3. For each sport:                  │
│    a. Fetch /sports (verify active) │
│    b. Fetch /odds (Tier 1)          │
│    c. Fetch /odds (Tier 2 if enabled)│
│ 4. Merge all responses              │
│ 5. Save to raw_odds_pure.csv        │
├─────────────────────────────────────┤
│ On Error:                           │
│ - Log error with timestamp          │
│ - Use cached CSV from last run      │
│ - Alert admin if > 3 consecutive    │
└─────────────────────────────────────┘
```

---

## 🛠️ Integration Points

### Extraction (`src/pipeline_v2/extract_odds.py`)
```python
import requests
from os import getenv

api_key = getenv("ODDS_API_KEY")
base_url = "https://api.the-odds-api.com/v4"

response = requests.get(
    f"{base_url}/sports/basketball_nba/odds",
    params={
        "apiKey": api_key,
        "regions": "us,us2,au",
        "markets": "h2h,spreads,player_props",
        "oddsFormat": "decimal"
    },
    timeout=30
)
```

### Configuration (`src/v3/configs/api_tiers.py`)
```python
API_TIER_CONFIGS = {
    "basketball_nba": {
        "tier_1_enabled": True,
        "tier_1_markets": ["h2h", "spreads", "totals"],
        "tier_2_enabled": True,
        "tier_2_markets": ["player_props"],
        "estimated_cost_per_run": 50
    }
}
```

### Cost Estimation (`pipeline_v3.py`)
```python
# User can check cost before extracting
python pipeline_v3.py --estimate-cost
# Output: NBA $50 + NFL $35 = $85 (within free tier)
```

---

## 🚨 Known Limitations

### Rate Limiting
- Free tier: 500/month is strict (no hourly checks)
- No burst allowance
- Monthly reset is calendar month

### Market Coverage
- Player props available for only ~10 bookmakers
- Some sports have limited bookmaker coverage
- Regional variations (AU bookmakers differ from US)

### Data Freshness
- Odds update every 5-10 minutes typically
- Pre-game odds only (no live odds)
- Delayed by 1-2 hours if high volume

### Bookmaker Availability
- Some bookmakers inactive for certain sports
- Seasonal variations (off-season = no data)
- New bookmakers added quarterly

---

## 📞 Support & Documentation

### Official Resources
- **Docs:** https://docs.odds-api.com
- **API Status:** https://status.the-odds-api.com
- **GitHub Issues:** https://github.com/the-odds-api/odds-api/issues
- **Contact:** Support via website

### Our Implementation
- **Main Extractor:** [src/pipeline_v2/extract_odds.py](../src/pipeline_v2/extract_odds.py)
- **Config Docs:** [src/v3/configs/](../src/v3/configs/)
- **Architecture:** [docs/ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🔐 Security Notes

### API Key Protection
```python
# ✅ DO: Use environment variable
api_key = getenv("ODDS_API_KEY")

# ❌ DON'T: Hardcode in code
api_key = "abc123xyz..."

# ❌ DON'T: Commit to git
```

### .env Template
```
# .env (not in git)
ODDS_API_KEY=your_actual_key_here

# Also add to .gitignore
echo ".env" >> .gitignore
```

### Exposed Key Response
If key is exposed publicly:
1. Regenerate immediately via API dashboard
2. Rotate in all environments
3. Review usage logs for abuse

---

## 📊 Quick Reference Table

| Item | Value | Notes |
|------|-------|-------|
| **API Version** | v4 | Current, stable |
| **Base URL** | api.the-odds-api.com/v4 | HTTPS required |
| **Free Rate Limit** | 500/month | Calendar month reset |
| **Auth Method** | apiKey (query param) | Env variable |
| **Main Markets** | h2h, spreads, totals, props | All 4 supported |
| **Sports Enabled** | NBA, NFL | 2 primary |
| **Cost Per Run** | ~$85/month | Safe within free tier |
| **Fallback** | Cached CSV | If API fails |
| **Monitoring** | GitHub releases | Watch for v5 |
| **Documentation** | https://docs.odds-api.com | Official docs |

---

## ✅ Checklist: API Integration Health

- [ ] API key set in `.env`
- [ ] Daily extraction running without errors
- [ ] Cost estimation accurate (match API calls)
- [ ] Cached CSV fallback in place
- [ ] GitHub releases page bookmarked
- [ ] Monitoring schedule established
- [ ] Rate limit usage tracked (optional dashboard)
- [ ] Error logging configured
- [ ] Timeout set to 30 seconds (prevents hanging)
- [ ] Monthly budget review scheduled

---

**Last Reviewed:** December 26, 2025  
**Next Review:** January 26, 2026  
**Version:** 1.0
