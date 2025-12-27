"""
Configuration for sport-specific odds extraction pipeline.
Modular settings for bookmakers, weights, regions, and fair odds calculation.
"""

from typing import Dict, List

# ============================================================================
# API CONFIGURATION
# ============================================================================

# The Odds API endpoint
ODDS_API_HOST = "https://api.the-odds-api.com"

# Regions to fetch (more regions = more bookmakers but higher cost)
# Options: au, us, eu, uk, us2
DEFAULT_REGIONS = "au,us,eu"

# Odds format (always use decimal for calculations)
ODDS_FORMAT = "decimal"

# Event time window (optimize credit usage)
EVENT_MIN_MINUTES = 5      # Don't fetch events starting <5 min from now
EVENT_MAX_HOURS = 48       # Don't fetch events >48 hrs from now

# ============================================================================
# SPORT DEFINITIONS
# ============================================================================

SPORT_CONFIGS = {
    "NFL": {
        "sport_key": "americanfootball_nfl",
        "base_markets": ["h2h", "spreads", "totals"],
        "player_props": [
            "player_pass_yds",
            "player_rush_yds",
            "player_reception_yds",
            "player_anytime_td",
            "player_pass_tds",
            "player_pass_completions",
            "player_pass_attempts",
            "player_pass_interceptions",
            "player_rush_attempts",
            "player_receptions",
        ],
        "enable_props": True,
    },
    "NBA": {
        "sport_key": "basketball_nba",
        "base_markets": ["h2h", "spreads", "totals"],
        "player_props": [
            "player_points",
            "player_rebounds",
            "player_assists",
            "player_threes",
            "player_blocks",
            "player_steals",
            "player_turnovers",
            "player_points_rebounds_assists",
            "player_points_assists",
            "player_points_rebounds",
            "player_rebounds_assists",
            "player_blocks_steals",
            "player_double_double",
            "player_first_basket",
        ],
        "enable_props": True,
    },
    "MLB": {
        "sport_key": "baseball_mlb",
        "base_markets": ["h2h", "spreads", "totals"],
        "player_props": [
            "batter_hits",
            "batter_total_bases",
            "batter_rbis",
            "batter_runs_scored",
            "batter_home_runs",
            "pitcher_strikeouts",
            "pitcher_hits_allowed",
            "pitcher_walks",
            "pitcher_earned_runs",
        ],
        "enable_props": True,
    },
    "NHL": {
        "sport_key": "icehockey_nhl",
        "base_markets": ["h2h", "spreads", "totals"],
        "player_props": [
            "player_points",
            "player_assists",
            "player_goals",
            "player_shots_on_goal",
            "goalie_saves",
        ],
        "enable_props": True,
    },
    "NCAAF": {
        "sport_key": "americanfootball_ncaaf",
        "base_markets": ["h2h", "spreads", "totals"],
        "player_props": [],
        "enable_props": False,  # Limited props for college sports
    },
}

# ============================================================================
# BOOKMAKER RATINGS & WEIGHTS
# ============================================================================

# Bookmaker ratings (1-4 stars)
# 4⭐ = Sharp (for fair odds), 3⭐ = Sharp (for fair odds), 2⭐ = Secondary, 1⭐ = Target (for EV)
BOOKMAKER_RATINGS = {
    # 4⭐ - GOLD STANDARD (for fair odds)
    "pinnacle": 4,
    "betfair": 4,          # Generic betfair key
    "betfair_ex_eu": 4,
    "draftkings": 4,
    "fanduel": 4,
    
    # 3⭐ - MAJOR SHARPS (for fair odds)
    "betfair_ex_au": 3,
    "betfair_ex_uk": 3,
    "betmgm": 3,
    "betrivers": 3,
    "betonlineag": 3,
    "bovada": 3,
    "lowvig": 3,
    "mybookieag": 3,
    
    # 2⭐ - SECONDARY SOURCES
    "marathonbet": 2,
    "betsson": 2,
    "nordicbet": 2,
    
    # 1⭐ - TARGET BOOKS (for EV opportunities)
    "sport316": 1,       # Sportsbet
    "pointsbetau": 1,
    "tab": 1,
    "tabtouch": 1,
    "unibet": 1,
    "unibet_au": 1,
    "ladbrokes_au": 1,
    "neds": 1,
    "betr_au": 1,
    "boombet_au": 1,
    "williamhill_us": 1,
    "superbook": 1,       # SBK
    "fanatics": 1,
    "barstool": 1,        # Now ESPNBet
    "ballybet": 1,
    "betparx": 1,
    "fliff": 1,
    "hardrockbet": 1,
}

# Weight configuration for fair odds calculation
# Sharp books (3⭐ and 4⭐) are used for fair odds, targets (1⭐) for EV hits
SHARP_BOOK_RATINGS = [3, 4]  # Only these ratings used for fair odds
TARGET_BOOK_RATINGS = [1]     # Only these ratings used as EV targets

# Minimum sharp books required to establish fair odds
MIN_SHARP_BOOKS = 2

# ============================================================================
# EV CALCULATION SETTINGS
# ============================================================================

# Minimum edge threshold for EV opportunities
EV_MIN_EDGE = 0.01  # 1% minimum edge

# Bankroll and Kelly Criterion settings
DEFAULT_BANKROLL = 1000
DEFAULT_KELLY_FRACTION = 0.25

# Markets to exclude from EV calculation
EXCLUDE_MARKETS = {"spreads_lay", "totals_lay"}

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

# CSV file paths (relative to data/ directory)
RAW_ODDS_FILES = {
    "NFL": "raw_NFL.csv",
    "NBA": "raw_NBA.csv",
    "MLB": "raw_MLB.csv",
    "NHL": "raw_NHL.csv",
    "NCAAF": "raw_NCAAF.csv",
}

MERGED_RAW_ODDS = "all_raw_odds.csv"
EV_HITS_FILE = "all_ev_hits.csv"

# CSV output columns
METADATA_COLUMNS = [
    "timestamp",
    "sport",
    "event_id",
    "commence_time",
    "teams",
    "market",
    "line",
    "selection",
    "player",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sharp_books() -> List[str]:
    """Get list of sharp bookmaker keys (3⭐ and 4⭐)."""
    return [
        book for book, rating in BOOKMAKER_RATINGS.items()
        if rating in SHARP_BOOK_RATINGS
    ]


def get_target_books() -> List[str]:
    """Get list of target bookmaker keys (1⭐)."""
    return [
        book for book, rating in BOOKMAKER_RATINGS.items()
        if rating in TARGET_BOOK_RATINGS
    ]


def get_book_rating(bookmaker_key: str) -> int:
    """Get rating for a bookmaker (0 if not found)."""
    return BOOKMAKER_RATINGS.get(bookmaker_key.lower(), 0)


def is_sharp_book(bookmaker_key: str) -> bool:
    """Check if bookmaker is a sharp book (3⭐ or 4⭐)."""
    return get_book_rating(bookmaker_key) in SHARP_BOOK_RATINGS


def is_target_book(bookmaker_key: str) -> bool:
    """Check if bookmaker is a target book (1⭐)."""
    return get_book_rating(bookmaker_key) in TARGET_BOOK_RATINGS
