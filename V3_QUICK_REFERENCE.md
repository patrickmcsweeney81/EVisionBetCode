# EVisionBet v3 - Quick Reference Card

**Print this or keep it in a terminal window!**

---

## 🚀 Fastest Start (Copy & Paste)

```bash
cd C:\EVisionBetCode
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
echo ODDS_API_KEY=your_key > .env
python pipeline_v3.py --sports basketball_nba
head data/v3/extracts/nba_raw.csv
```

---

## 📂 Key Directories

```
src/v3/                         ← All new code
├── config.py                   ← Change bookmakers, weights, sports
├── base_extractor.py           ← Don't edit, just inherit
├── extractors/nba_extractor.py ← Copy to create new sport
└── processors/fair_odds_v2.py  ← Fair odds math

data/v3/extracts/               ← Individual sport CSVs
data/v3/merged/                 ← Combined output
```

---

## 🎮 Common Commands

```bash
# Run all enabled sports
python pipeline_v3.py

# Run one sport only
python pipeline_v3.py --sports basketball_nba

# Run multiple sports
python pipeline_v3.py --sports basketball_nba americanfootball_nfl icehockey_nhl

# Merge existing data (no API calls)
python pipeline_v3.py --merge-only

# View extracted data
head -5 data/v3/extracts/nba_raw.csv
wc -l data/v3/merged/all_raw_odds.csv

# Test code quality
pytest tests/
black src/
pylint src/
```

---

## ⚙️ Configuration Changes (Edit `src/v3/config.py`)

### Enable/Disable Sports
```python
"baseball_mlb": {"enabled": False, ...}  # Disable
"basketball_nba": {"enabled": True, ...}  # Enable
```

### Change Bookmaker Rating
```python
BOOKMAKER_RATINGS = {
    "sportsbet": {"stars": 1, "category": "target"},
    # stars: 1-4, category: "sharp" or "target"
}
```

### Adjust Weight Profile
```python
SPORT_WEIGHT_PROFILES = {
    "basketball_nba": {
        "pinnacle": 0.50,      # Increase Pinnacle weight
        "draftkings": 0.30,
        "fanduel": 0.20,
    }
}
```

### Change EV Threshold
```python
EV_CONFIG = {
    "min_ev_percent": 1.5,  # Lower for more hits
}
```

---

## 🏗️ Add New Sport (Copy-Paste)

### Step 1: Create Extractor
```bash
cp src/v3/extractors/nba_extractor.py src/v3/extractors/hockey_extractor.py
```

### Step 2: Edit File
```python
class HockeyExtractor(BaseExtractor):
    SPORT_KEY = "icehockey_nhl"  # Change this
    SPORT_NAME = "NHL"             # Change this
    PLAYER_PROPS = ["player_goals", "player_assists"]  # Customize
    TIME_WINDOW_HOURS = 48         # Adjust if needed
    
    # Keep fetch_odds() similar or customize as needed
```

### Step 3: Register It
```python
# In pipeline_v3.py, add:
from src.v3.extractors.hockey_extractor import HockeyExtractor

EXTRACTORS = {
    "basketball_nba": NBAExtractor,
    "icehockey_nhl": HockeyExtractor,  # ADD THIS
}
```

### Step 4: Run It
```bash
python pipeline_v3.py --sports icehockey_nhl
```

---

## 🐛 Troubleshooting

### "ODDS_API_KEY not set"
```bash
# Add to .env
echo ODDS_API_KEY=your_real_key > .env
```

### "No events found"
- Check if sport has active events (off-season?)
- Check time window setting in config.py
- Check API key has remaining credits

### "CSV is empty"
- Check logs for validation errors
- Verify API returned valid data
- Check column headers match expected format

### "Module not found"
```bash
# Reinstall package
pip install -e ".[dev]"
```

---

## 📊 CSV Format (17 Columns)

```
extracted_at
sport
league
event_id
event_name
commence_time
market_type      ← h2h, spreads, totals
point            ← Line for spreads/totals
selection        ← Team/Player name
player_name      ← Blank unless player prop
bookmaker        ← Book name (sportsbet, pinnacle, etc)
stars_rating     ← 1-4
odds_decimal     ← 1.90, 2.05, etc
implied_prob     ← 0.5263, etc
is_sharp         ← true/false
is_target        ← true/false
notes            ← For debugging
```

---

## 🔧 Common Edits

### Disable AU Books (Keep Only Sharps)
```python
# In config.py, comment out AU books:
# "sportsbet": {"stars": 1, ...},
# "tab": {"stars": 1, ...},
```

### Increase API Calls (More Props)
```python
# In nba_extractor.py:
PLAYER_PROPS = [
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_threes",
    "player_blocks",
    "player_steals",
    "player_turnovers",
    "player_double_double",  # ADD
    "player_triple_double",  # ADD
]
```

### Reduce Time Window (Closer Games)
```python
# In config.py:
"basketball_nba": {
    "time_window_hours": 24,  # Was 48
}
```

### Change Outlier Threshold
```python
# In config.py:
EV_CONFIG = {
    "outlier_threshold": 0.10,  # Was 0.05, more lenient
}
```

---

## 📈 Next After Extract

### 1. Test Output
```bash
python pipeline_v3.py --sports basketball_nba
# Check: data/v3/extracts/nba_raw.csv
```

### 2. Merge Multiple Sports
```bash
python pipeline_v3.py --sports basketball_nba americanfootball_nfl
# Check: data/v3/merged/all_raw_odds.csv
```

### 3. Calculate EV (TODO)
```bash
python src/v3/processors/ev_calculator.py
# Will read: data/v3/merged/all_raw_odds.csv
# Will write: data/v3/merged/all_ev_hits.csv
```

### 4. Run Backend
```bash
uvicorn backend_api:app --reload
# Will read: data/v3/merged/
```

---

## 📚 Documentation

| Document | When to Read |
|----------|-------------|
| `V3_BUILD_SUMMARY.md` | Overview of what was built |
| `V3_MIGRATION_GUIDE.md` | Setup on new machine |
| `src/v3/README.md` | Deep architecture dive |
| `src/v3/config.py` | Understanding configuration |
| `src/v3/base_extractor.py` | How extraction works |
| `src/v3/extractors/nba_extractor.py` | Example to copy |

---

## 🎯 Your Next Tasks (In Order)

1. **Test on new machine** (5 min)
   ```bash
   python pipeline_v3.py --sports basketball_nba
   ```

2. **Fine-tune NBA** (30 min)
   - Add/remove player props
   - Adjust time window
   - Change regions

3. **Fine-tune NFL** (30 min)
   - Similar as NBA

4. **Implement EV calculator** (2 hours)
   - Create: `src/v3/processors/ev_calculator.py`
   - Use: `FairOddsCalculatorV2` from fair_odds_v2.py
   - Read: `data/v3/merged/all_raw_odds.csv`
   - Write: `data/v3/merged/all_ev_hits.csv`

5. **Add more sports** (4 hours)
   - Hockey, Soccer, Tennis, Cricket, etc.
   - Just copy-paste NBA/NFL pattern

6. **Unit tests** (2 hours)
   - Test each extractor
   - Test fair odds math
   - Test edge cases

---

## 💾 Backup/Migration

### Copy Everything
```bash
# Backup v3 to external drive
xcopy C:\EVisionBetCode\src\v3 D:\Backup\src\v3 /E /I
xcopy C:\EVisionBetCode\data\v3 D:\Backup\data\v3 /E /I
xcopy C:\EVisionBetCode\pipeline_v3.py D:\Backup\
```

### Transfer to New Machine
```bash
xcopy D:\Backup\src\v3 C:\EVisionBetCode\src\v3 /E /I
xcopy D:\Backup\data\v3 C:\EVisionBetCode\data\v3 /E /I
copy D:\Backup\pipeline_v3.py C:\EVisionBetCode\
```

---

**Last Updated:** December 25, 2025  
**Version:** 3.0.0  
**Status:** 🟢 Ready to Go
