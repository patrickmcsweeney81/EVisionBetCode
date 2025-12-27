"""
V3 Configuration - Centralized settings for all extractors
"""

import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load .env first
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # src/v3 -> root/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

# ============================================================================
# BOOKMAKERS & RATINGS
# ============================================================================

# Bookmaker ratings: 1⭐ (target), 3⭐/4⭐ (sharp), others (secondary)
BOOKMAKERS = {
    # TARGET BOOKS (1⭐) - High margin, good for EV detection
    "draftkings": {"rating": 1, "region": "US", "weight": 1.0},
    "fanduel": {"rating": 1, "region": "US", "weight": 1.0},
    "betmgm": {"rating": 1, "region": "US", "weight": 1.0},
    
    # SHARP BOOKS (3⭐/4⭐) - Low margin, use for fair odds
    "pinnacle": {"rating": 4, "region": "EU", "weight": 1.5},
    "betfair_eu": {"rating": 3, "region": "EU", "weight": 1.0},
    "betfair_au": {"rating": 3, "region": "AU", "weight": 1.0},
    
    # SECONDARY BOOKS (2⭐) - Good coverage
    "betonline": {"rating": 2, "region": "US", "weight": 0.8},
    "bovada": {"rating": 2, "region": "US", "weight": 0.8},
    "lowvig": {"rating": 2, "region": "US", "weight": 0.8},
}

# Abbreviations for CSV columns
BOOK_ABBREVIATIONS = {
    "pinnacle": "Pinnacle",
    "betfair_eu": "Betfair_EU",
    "betfair_au": "Betfair_AU",
    "draftkings": "Draftkings",
    "fanduel": "Fanduel",
    "betmgm": "Betmgm",
    "betonline": "Betonline",
    "bovada": "Bovada",
    "lowvig": "Lowvig",
}

# ============================================================================
# SPORTS & MARKETS
# ============================================================================

SPORTS = {
    "basketball_nba": {
        "name": "NBA",
        "markets": ["h2h", "spreads", "totals"],
        "player_props": ["player_points", "player_rebounds", "player_assists"],
        "regions": ["au", "us", "eu"],
    },
    "americanfootball_nfl": {
        "name": "NFL",
        "markets": ["h2h", "spreads", "totals"],
        "player_props": ["player_pass_yds", "player_pass_tds", "player_rush_yds"],
        "regions": ["au", "us"],
    },
}

# ============================================================================
# API SETTINGS
# ============================================================================

ODDS_API_HOST = "https://api.the-odds-api.com"
API_KEY = os.getenv("ODDS_API_KEY", "")

# Time filters (in minutes/hours)
EVENT_MIN_MINUTES = 5  # Don't fetch events starting <5 min from now
EVENT_MAX_HOURS = 24  # Don't fetch events >24 hrs from now

# ============================================================================
# DATA PATHS
# ============================================================================

def get_data_dir():
    """Get data directory - robust for local and Render deployments."""
    cwd = Path.cwd()
    cwd_str = str(cwd).replace("\\src\\src", "\\src").replace("/src/src", "/src")
    cwd = Path(cwd_str)
    
    # Priority 1: cwd/data
    data_path = cwd / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    if data_path.exists():
        return data_path
    
    # Priority 2: parent/data if cwd is src
    if cwd.name == "src":
        data_path = cwd.parent / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path
    
    return cwd / "data"

DATA_DIR = get_data_dir()
V3_DATA_DIR = DATA_DIR / "v3"
V3_EXTRACTS_DIR = V3_DATA_DIR / "extracts"

# Create directories
V3_EXTRACTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# EXTRACTION SETTINGS
# ============================================================================

# CSV Column order (universal for all sports)
CSV_COLUMNS = [
    "timestamp",
    "sport",
    "event_id",
    "away_team",
    "home_team",
    "commence_time",
    "market",
    "point",
    "selection",
] + [BOOK_ABBREVIATIONS.get(k, k.title()) for k in sorted(BOOKMAKERS.keys())]

# ============================================================================
# QUALITY FILTERS
# ============================================================================

# Require 2-way pairs
REQUIRE_TWO_WAY = True

# Markets to exclude
EXCLUDE_MARKETS = ["h2h_lay", "draw", "parlay"]

# Minimum bookmaker coverage for valid line
MIN_BOOK_COUNT = 2

# Remove outlier odds (e.g., >5% deviation from median)
OUTLIER_THRESHOLD = 0.05

# ============================================================================
# FAIR ODDS SETTINGS
# ============================================================================

# Sharp books to use for fair odds
SHARP_BOOKS = ["pinnacle", "betfair_eu", "betfair_au"]

# Minimum sharp books required for fair odds
MIN_SHARP_COUNT = 2

# Remove outliers when calculating fair odds
REMOVE_OUTLIERS = True
OUTLIER_PERCENTILE = 2.5  # Remove bottom 2.5% and top 2.5%

# ============================================================================
# LINE NORMALIZATION (NEW FOR V3)
# ============================================================================

# Books that use whole numbers (convert to .5)
BOOKS_TO_NORMALIZE = {
    "betmgm",  # May use whole numbers on some lines
    "fanduel",  # Occasionally uses whole
}

# How to normalize: add 0.5 to spread/total lines
NORMALIZE_AMOUNT = 0.5

# Markets to normalize (spreads and totals)
NORMALIZE_MARKETS = ["spreads", "totals"]
