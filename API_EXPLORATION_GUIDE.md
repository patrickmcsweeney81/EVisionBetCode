# API Exploration Guide

## Three Ways to Explore The Odds API Data

### 1. **api_explorer.py** - High-Level Overview
**Best for:** Understanding available sports, regions, bookmakers structure  
**Runs:** Quick exploration with summaries
**Output:** Console text summary

```bash
python api_explorer.py
```

Shows:
- All available sports (soccer, NBA, NFL, etc.)
- Sample event structure
- Available bookmakers for that event
- Bookmakers per region breakdown
- Tips for efficient API usage

---

### 2. **api_explorer_raw.py** - Raw JSON Output
**Best for:** Seeing exact data structure The Odds API returns  
**Runs:** Gets one event's odds, shows raw JSON
**Output:** JSON printed to console + saves `api_sample_response.json`

```bash
python api_explorer_raw.py
```

Shows:
- Raw event JSON (fields, formatting, etc.)
- Raw bookmaker JSON (how odds are nested)
- All available bookmakers
- Saves full response for inspection in VS Code

**👉 Then open `api_sample_response.json` in VS Code to browse the structure visually**

---

### 3. **api_query_builder.py** - Custom Queries
**Best for:** Testing different sports, regions, markets  
**Runs:** Fully customizable API calls
**Output:** Bookmaker table + detailed breakdown

```bash
python api_query_builder.py
```

Then edit these at the top of the file:
```python
SPORT = "basketball_nba"           # Change to basketball_nfl, etc.
REGIONS = "au,us,us2,eu"           # Test different regions
MARKETS = "h2h,spreads,totals"     # Or just "h2h"
```

Shows:
- Summary table of all bookmakers
- Detailed odds for one bookmaker
- Market coverage stats
- Saves query result to `query_result.json`

---

## API Credit Usage

**Important:** Each call costs credits!

| Action | Cost | Notes |
|--------|------|-------|
| Get events list | 1 credit | Gets all events for that sport |
| Get odds for 1 event | 1 credit | All bookmakers + markets |
| Get odds for 10 events | 10 credits | Multiply by number of events |

**Smart approach:**
- Run explorers ONCE per session
- Cache results locally
- Don't re-run same queries
- Use `api_query_builder.py` to test before coding

---

## Available Parameters

### Sports
```
basketball_nba
americanfootball_nfl
icehockey_nhl
baseball_mlb
soccer_epl (English Premier League)
... and 100+ more
```

### Regions
```
au      (Australia)
us      (United States - primary)
us2     (United States - secondary)
eu      (Europe)
uk      (United Kingdom)
br      (Brazil)
in      (India)
```

### Markets
```
h2h               (Head to head - winner)
spreads           (Point spreads)
totals            (Over/Under)
h2h_lay           (Lay bets)
player_props      (Individual player stats)
... others depend on sport
```

### Odds Format
```
decimal    (1.95, 2.10) ← Currently using
american   (-110, +110)
fractional (8/5, etc.)
```

---

## Example Usage Pattern

### To explore NFL:
```python
# Edit api_query_builder.py
SPORT = "americanfootball_nfl"
REGIONS = "us"  # Most books only US
MARKETS = "spreads,totals"  # NFL has these
```

### To check specific bookmaker availability:
```python
# Run api_explorer.py, note which books appear in each region
# Then in api_query_builder.py, test each region individually
REGIONS = "us"    # First
REGIONS = "eu"    # Then
REGIONS = "au"    # Then see differences
```

### To verify our extraction handles all markets:
```python
# Use api_query_builder.py to see what markets exist
# Compare with what extract_nba_v3.py captures
MARKETS = "h2h,spreads,totals,h2h_lay,player_props"  # Test all
```

---

## Viewing JSON Responses Efficiently

**In VS Code:**
1. Run `python api_explorer_raw.py`
2. Right-click `api_sample_response.json` in file explorer
3. Select "Open in Default Application" → VS Code
4. Use Ctrl+F to search structure
5. Fold/expand sections to explore

**The structure looks like:**
```json
{
  "success": true,
  "bookmakers": [
    {
      "key": "draftkings",
      "title": "DraftKings",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {
              "name": "Team Name",
              "price": 1.95,
              "point": null
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No events found" | Wrong region - try "us,eu,au" |
| "No bookmakers" | Wrong market - add "h2h" to MARKETS |
| API error | Check ODDS_API_KEY in .env |
| Too many bookmakers | Some books don't support your sport - normal |

---

## Next Steps

1. **Run one explorer** to understand the data:
   ```bash
   python api_explorer.py
   ```

2. **Review the JSON structure:**
   ```bash
   python api_explorer_raw.py
   ```
   Then open `api_sample_response.json`

3. **Test custom queries** for other sports:
   ```bash
   # Edit api_query_builder.py
   python api_query_builder.py
   ```

4. **Compare with our extraction** to ensure we're capturing everything

---

## Questions to Answer Using These Tools

- ✅ What bookmakers are available in each region?
- ✅ What markets does each bookmaker support?
- ✅ What does a complete API response look like?
- ✅ How many bookmakers for NFL vs NBA?
- ✅ Are player_props available for basketball?
- ✅ What's the structure of odds data?
