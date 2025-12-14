# 🤖 AI Agent Coding Guide - EVisionBetCode

**For: GitHub Copilot, Claude, and other AI coding agents**

This guide helps AI agents contribute effectively to EVisionBetCode projects while maintaining code quality and architectural consistency.

---

## 🏗️ Architecture Overview

### Two Repository Structure
- **EVisionBetCode** (Backend)
  - Python 3.11+ with FastAPI
  - Two-stage pipeline: extract → calculate
  - Located: `C:\EVisionBetCode`
  - Files: `backend_api.py`, `src/pipeline_v2/`

- **EVisionBetSite** (Frontend)
  - React 19 with TypeScript
  - Vite build system (hot reload)
  - Located: `C:\EVisionBetSite`
  - Files: `frontend/src/components/`

### Key Architectural Patterns

#### Data Pipeline (Backend)
```
extract_odds.py → raw_odds_pure.csv → calculate_opportunities.py → ev_opportunities.csv
```
- **Stage 1 (Extract):** Parallel fetch from 12 sports using The Odds API
  - Input: API credentials, sports list, regions
  - Output: `data/raw_odds_pure.csv` (wide format, one row = one bookmaker/market/selection)
  - Key function: `_extract_sport()` - runs in parallel ThreadPoolExecutor

- **Stage 2 (Calculate):** EV opportunities from raw odds
  - Input: `raw_odds_pure.csv`
  - Output: `data/ev_opportunities.csv` + optional PostgreSQL
  - Key functions: `fair_from_sharps()`, `group_rows_wide()`, `extract_sides()`

#### Frontend Display (React)
```
API /api/odds/raw → RawOddsTable (6-filter multi-select) → User
                  → EV Opportunities (best-book highlights)
```
- Components follow container/presentation pattern
- State management: React hooks (useState, useEffect, useMemo)
- Styling: CSS modules with split-table layout

---

## 🔑 Critical Patterns to Maintain

### 1. File Path Handling
**❌ NEVER DO:**
```python
path = "/data/raw_odds_pure.csv"  # Hardcoded path
df = pd.read_csv(path)
```

**✅ ALWAYS DO:**
```python
from src.pipeline_v2.calculate_opportunities import get_data_dir

data_dir = get_data_dir()  # Handles Render's /src/src duplicate
csv_path = data_dir / "raw_odds_pure.csv"
df = pd.read_csv(csv_path)
```

**Why:** Render deployment adds `/src/` prefix. Function handles both local dev and production.

---

### 2. Fair Odds Calculation (Critical Logic)
**Rule:** Only use 4⭐ and 3⭐ books (sharps) - NEVER include 1⭐/2⭐ books

```python
def fair_from_sharps(over_prices, under_prices, sport, ratings_dict):
    """
    Calculate fair odds from sharp books only.
    
    CRITICAL: Maintain separate weight totals for Over/Under
    Formula: fair = 1.0 / ((sum(1/price * rating * weight) / weight_total))
    
    Args:
        over_prices: dict {bookmaker: price}
        under_prices: dict {bookmaker: price}
        sport: str (e.g., "NBA")
        ratings_dict: dict from ratings.py
    
    Returns:
        (fair_over, fair_under, sharp_count)
    
    Raises:
        ValueError: If sharp_count < 2
    """
    
    # ✅ CORRECT: Separate weight totals per side
    over_weight_total = sum(
        ratings_dict[book]['star'] * weight_for_sport(book, sport)
        for book in over_prices if is_sharp_book(book, ratings_dict)
    )
    under_weight_total = sum(
        ratings_dict[book]['star'] * weight_for_sport(book, sport)
        for book in under_prices if is_sharp_book(book, ratings_dict)
    )
    
    # ❌ WRONG: Shared weight total
    # weight_total = sum(...)  # <-- NO! Uses wrong denominator
```

**Key Rules:**
- Skip if `sharp_count < 2`
- Use only 3⭐/4⭐ books from `ratings.py`
- Apply sport-specific weights (see `ratings.py` for each sport)
- Remove outliers: 5% tolerance from median when sharps conflict
- Separate weight totals for Over/Under (not shared)

See: [docs/BUGFIX_FAIR_ODDS_DEC10_2025.md](docs/BUGFIX_FAIR_ODDS_DEC10_2025.md)

---

### 3. Player Props Grouping (Important)
**Rule:** Group by 5-tuple: `(sport, event_id, market, point, player_name)`
**NOT just:** `(market, point)` - This breaks player-by-player analysis

```python
# ✅ CORRECT: Extract player name from selection
def _player_key(selection, market):
    """Extract player name from 'Player Name Over' or 'Player Name Under'"""
    if market in ["Player Totals Over", "Player Props Over"]:
        return selection.replace(" Over", "")
    elif market in ["Player Totals Under", "Player Props Under"]:
        return selection.replace(" Under", "")
    else:
        return ""  # Non-player market

# Group by full 5-tuple
grouped = df.groupby(['sport', 'event_id', 'market', 'point', 'player_name'])

# ❌ WRONG: Group only by (market, point)
# grouped = df.groupby(['market', 'point'])  # Loses player context
```

**Why:** Different players in same market have different odds and fair values. Must group separately to calculate per-player EV.

---

### 4. Market Exclusions
**Rule:** Skip these markets (in `EXCLUDE_MARKETS` list):
- Exchange-only: "Betfair", "Matchbook"
- In-play: "In-play", "Live"
- Invalid: "Specials", blank, null
- Props-only not in scope: Various sport-specific exclusions

```python
EXCLUDE_MARKETS = [
    "Betfair", "Matchbook", "In-play", "Live", "Specials", 
    "Outrights", "Starting Pitchers", ...
]

# Check before processing
if market in EXCLUDE_MARKETS:
    continue  # Skip this market
```

---

### 5. Error Handling
**Rule:** Never crash on invalid data - gracefully skip and log

```python
# ✅ CORRECT: Validation + skip
try:
    odds = float(row['best_odds'])
    if odds <= 0 or odds > 1000:
        logger.warning(f"Invalid odds {odds} in {row}")
        continue
except (ValueError, TypeError):
    logger.warning(f"Could not parse odds: {row}")
    continue

# ❌ WRONG: Crash on bad data
# odds = float(row['best_odds'])  # Crashes if non-numeric
```

**Logging:** Use `logger.warning()` for skipped rows, `logger.error()` for failures

---

## 📝 Code Style & Standards

### Python (Backend)

**Format & Lint:**
```bash
make pre-commit  # Runs all checks
make format      # Black + isort
make lint        # Flake8 + pylint
make type-check  # Mypy
```

**Type Hints (Required for new functions):**
```python
def calculate_ev(
    odds: float,
    fair_odds: float,
    min_edge: float = 0.01
) -> float:
    """
    Calculate expected value percentage.
    
    Args:
        odds: Decimal odds (e.g., 2.5)
        fair_odds: Fair value calculated from sharps
        min_edge: Minimum edge threshold (default 1%)
    
    Returns:
        EV percentage (e.g., 0.05 for 5% edge)
    
    Raises:
        ValueError: If odds or fair_odds invalid
    """
    if odds <= 0 or fair_odds <= 0:
        raise ValueError(f"Invalid odds: {odds}, {fair_odds}")
    
    return (odds / fair_odds) - 1.0
```

**Docstring Style:** Google-style (see example above)

**Import Order:**
```python
# Standard library
import json
from datetime import datetime

# Third-party
import pandas as pd
import numpy as np
from fastapi import FastAPI

# Local
from src.pipeline_v2.ratings import get_book_rating
from src.pipeline_v2.calculate_opportunities import get_data_dir
```

### JavaScript/React (Frontend)

**Format & Lint:**
```bash
npm run format    # Prettier
npm run lint      # ESLint
npm test          # Jest
```

**Component Pattern:**
```javascript
// ✅ CORRECT: Functional component with hooks
const RawOddsTable = ({ data, onFilter }) => {
  const [filters, setFilters] = useState({});
  const [sortColumn, setSortColumn] = useState('sport');
  
  const filteredData = useMemo(() => {
    // Heavy computation here
    return data.filter(...).sort(...);
  }, [data, filters, sortColumn]);
  
  return (
    <div className="raw-odds-table">
      {/* JSX here */}
    </div>
  );
};

export default RawOddsTable;
```

**Naming Convention:**
- Components: PascalCase (`RawOddsTable.js`)
- Files: PascalCase for components, camelCase for utilities
- Props: camelCase (`onFilterChange`, `isLoading`)
- State: camelCase (`filterValue`, `currentPage`)

---

## 🔄 Common Development Tasks

### Adding a New Filter to RawOddsTable

1. **Identify the data field** (e.g., "bookmaker")
2. **Add to filter state:**
   ```javascript
   const [filters, setFilters] = useState({
     sport: new Set(),
     bookmaker: new Set(),  // <-- NEW
   });
   ```

3. **Extract filter options:**
   ```javascript
   const bookmakerOptions = useMemo(() => {
     const options = new Set();
     data?.forEach(row => {
       // Dynamically extract from columns
       Object.keys(row).forEach(key => {
         if (!baseColumns.includes(key)) {
           options.add(key);  // Bookmaker column names
         }
       });
     });
     return Array.from(options).sort();
   }, [data]);
   ```

4. **Apply filter in useMemo:**
   ```javascript
   const filteredData = useMemo(() => {
     let result = data || [];
     
     // Apply all filters
     if (filters.bookmaker.size > 0) {
       result = result.filter(row =>
         Array.from(filters.bookmaker).some(bm => row[bm] > 0)
       );
     }
     
     return result;
   }, [data, filters]);
   ```

5. **Render filter UI:**
   ```javascript
   <select multiple value={Array.from(filters.bookmaker)}>
     {bookmakerOptions.map(option => (
       <option key={option} value={option}>
         {option}
       </option>
     ))}
   </select>
   ```

6. **Add to RESET button:**
   ```javascript
   const handleReset = () => {
     setFilters({
       sport: new Set(),
       bookmaker: new Set(),  // <-- Include here
     });
   };
   ```

---

### Adding an API Endpoint

**Backend (backend_api.py):**
```python
@app.get("/api/new-endpoint")
async def get_new_data(
    limit: int = 50,
    sport: str = None,
    min_ev: float = 0.01
) -> dict:
    """
    Get new data with optional filtering.
    
    Query Parameters:
        limit: Max rows to return (default 50)
        sport: Filter by sport (optional)
        min_ev: Minimum EV threshold (default 1%)
    
    Returns:
        {"data": [...], "count": N, "timestamp": ISO-8601}
    """
    df = pd.read_csv(get_data_dir() / "ev_opportunities.csv")
    
    if sport:
        df = df[df['sport'].str.upper() == sport.upper()]
    
    if min_ev:
        df = df[df['ev_percent'] >= min_ev]
    
    return {
        "data": df.head(limit).to_dict(orient='records'),
        "count": len(df),
        "timestamp": datetime.now().isoformat()
    }
```

**Frontend (fetch):**
```javascript
const [data, setData] = useState([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
  setLoading(true);
  fetch(`http://localhost:8000/api/new-endpoint?limit=50&sport=NBA`)
    .then(res => res.json())
    .then(json => setData(json.data))
    .catch(err => console.error(err))
    .finally(() => setLoading(false));
}, []);
```

---

### Running Tests

**Python (pytest):**
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_book_weights.py -v

# Run with coverage
pytest tests/ --cov=src/

# Run one test function
pytest tests/test_book_weights.py::test_rating_extraction -v
```

**JavaScript (Jest):**
```bash
# Run all tests
npm test

# Run specific test
npm test RawOddsTable.test.js

# Watch mode
npm test -- --watch
```

---

## 🐛 Debugging Tips

### Python (Backend)

**Print debugging:**
```python
import json
logger = logging.getLogger(__name__)

# Inspect data
logger.debug(f"DataFrame shape: {df.shape}")
logger.debug(f"Columns: {df.columns.tolist()}")
logger.debug(f"Sample row: {df.iloc[0].to_dict()}")
```

**Interactive debugging (pdb):**
```python
import pdb; pdb.set_trace()  # Breakpoint

# In pdb prompt:
# n: next line
# s: step into function
# c: continue
# p variable: print variable
# l: list code
# w: show stack
```

**Check API responses:**
```bash
# Using curl
curl "http://localhost:8000/api/odds/raw?limit=10"

# Using Thunder Client (VS Code extension)
# GET http://localhost:8000/docs
```

### JavaScript/React (Frontend)

**Console debugging:**
```javascript
console.log("Variable:", myVar);
console.table(arrayOfObjects);  // Pretty table
console.error("Error message");
console.warn("Warning message");
```

**React DevTools:**
1. Install extension (VS Code: ESLint + Debugger)
2. Open DevTools (F12)
3. Go to "React" tab
4. Inspect component state/props

**Network debugging:**
1. DevTools (F12) → Network tab
2. Check API responses
3. Inspect headers and payload

---

## 📋 Checklist Before Submitting Code

- [ ] Code follows style guide (run `make pre-commit` for Python, `npm run lint` for JS)
- [ ] All tests pass (`pytest` or `npm test`)
- [ ] No console errors in DevTools (F12)
- [ ] CORS configured if adding new endpoint
- [ ] Error handling in place (no uncaught exceptions)
- [ ] Type hints added (Python) / PropTypes checked (JavaScript)
- [ ] Docstrings/comments explain complex logic
- [ ] Git message is descriptive: `feat:`, `fix:`, `docs:`, etc.
- [ ] Tested in both development and production build
- [ ] No hardcoded paths or API keys (use .env)

---

## 🚀 Deployment Workflow

1. **Make changes** on feature branch
2. **Run quality checks:** `make pre-commit` (Python) or `npm run lint` (JS)
3. **Test thoroughly:** `pytest` or `npm test`
4. **Commit with message:** `git commit -m "feat: Clear description"`
5. **Push:** `git push origin main`
6. **Render auto-deploys** (check https://dashboard.render.com/)

---

## 📚 Key Files Reference

| File | Purpose | When to Edit |
|------|---------|--------------|
| `backend_api.py` | FastAPI server | Add endpoints, CORS, health checks |
| `src/pipeline_v2/extract_odds.py` | Data extraction | Change sports, add filters, optimize API calls |
| `src/pipeline_v2/calculate_opportunities.py` | EV calculation | Change fair odds logic, grouping, output format |
| `src/pipeline_v2/ratings.py` | Bookmaker ratings | Update star ratings, sport weights |
| `frontend/src/components/RawOddsTable.js` | Raw odds display | Add filters, columns, formatting |
| `frontend/src/App.js` | Router & routes | Add new pages, change navigation |
| `tests/test_book_weights.py` | Python tests | Validate rating logic |
| `.env` | Configuration | API keys, database URL, admin password |

---

## 🎓 Learning Context

This project implements a **smart betting expected value finder**:
- **EV** = Expected Value = (odds / fair_odds) - 1.0
- **Fair odds** = calculated from sharp books (4⭐/3⭐ only)
- **Edge** = % difference between actual and fair (if positive = profit opportunity)
- **Kelly stake** = bankroll × edge × (odds - 1) / (odds - 1)

**Example:**
- Actual odds: 2.5 (implied prob 40%)
- Fair odds: 2.2 (implied prob 45.5%)
- EV: (2.5 / 2.2) - 1 = 0.136 = **13.6% edge**
- On $100 bet: Expected profit = $100 × 0.136 = $13.60

---

## 🤝 Contributing Guidelines

When contributing to this project:

1. **Read this guide** - Understand architectural patterns
2. **Follow existing code style** - Consistency matters
3. **Test thoroughly** - No production bugs
4. **Document changes** - Comments and docstrings
5. **Commit cleanly** - One feature per commit
6. **Ask questions** - Check existing issues/PRs first

**Respect these constraints:**
- Never skip player prop 5-tuple grouping
- Never use 1⭐ books in fair odds calculation
- Never hardcode file paths
- Always include error handling
- Always validate input data

---

## ❓ FAQ for AI Agents

**Q: Can I modify the fair_from_sharps() function?**
A: Only if you fully understand the separate weight totals rule and test extensively. This is critical logic. See [docs/BUGFIX_FAIR_ODDS_DEC10_2025.md](docs/BUGFIX_FAIR_ODDS_DEC10_2025.md).

**Q: Should I use PostgreSQL or CSV?**
A: CSV is the fallback. Always ensure CSV output works. Database is optional (DATABASE_URL env var).

**Q: Can I add a new sport?**
A: Yes! Update `SPORTS` env var in .env, add to extract_odds.py's sport list, add to SPORTS dict with props if applicable. Test with real API data.

**Q: How do I handle API rate limits?**
A: The Odds API has rate limits. Extract-odds.py includes exponential backoff retry logic. Check extract_odds.py for details.

**Q: Can I deploy to environments other than Render?**
A: Yes, but ensure: (1) Python 3.11+, (2) PostgreSQL optional, (3) /src/src path handling works, (4) CORS configured for your domain.

---

## 🎯 Success Metrics

Good PRs have:
- ✅ Code that passes all tests
- ✅ Clear commit messages
- ✅ Comments explaining complex logic
- ✅ No new warnings/errors
- ✅ Maintains architectural patterns
- ✅ Works in both dev and production

Bad PRs:
- ❌ Hardcoded paths or API keys
- ❌ Skip error handling
- ❌ Ignore type hints
- ❌ Break existing functionality
- ❌ No tests or failing tests

---

**Last Updated:** December 14, 2025  
**Maintained By:** Development Team  
**Version:** 1.0

