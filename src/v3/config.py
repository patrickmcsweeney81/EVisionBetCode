"""
v3 Configuration - Sport specs, markets, props, and extraction rules
"""

from typing import Dict, List

# ============================================================================
# SPORTS CONFIGURATION
# ============================================================================

SPORTS_CONFIG = {
    "basketball_nba": {
        "name": "NBA",
        "league": "NBA",
        "regions": ["au", "us", "eu"],  # Pinnacle in EU
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": True,
        "player_props": [
            "player_points",
            "player_rebounds",
            "player_assists",
            "player_threes",
            "player_blocks",
            "player_steals",
            "player_turnovers",
        ],
        "time_window_hours": 48,
        "min_events": 1,
        "notes": "AU books often sparse on props, rely on sharps",
    },
    "basketball_nbl": {
        "name": "NBL",
        "league": "NBL",
        "regions": ["au"],
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": True,
        "player_props": ["player_points", "player_rebounds", "player_assists"],
        "time_window_hours": 48,
        "min_events": 1,
        "notes": "AU-only league",
    },
    "americanfootball_nfl": {
        "name": "NFL",
        "league": "NFL",
        "regions": ["au", "us", "eu"],
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": True,
        "player_props": [
            "player_pass_yds",
            "player_rush_yds",
            "player_reception_yds",
            "player_anytime_td",
        ],
        "time_window_hours": 168,  # Week ahead
        "min_events": 1,
        "notes": "Seasonal - inactive outside season",
    },
    "americanfootball_ncaaf": {
        "name": "NCAAF",
        "league": "NCAAF",
        "regions": ["us"],
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": False,  # Disabled for now
        "player_props": [],
        "time_window_hours": 168,
        "min_events": 0,
        "notes": "Seasonal - disabled until props available",
    },
    "icehockey_nhl": {
        "name": "NHL",
        "league": "NHL",
        "regions": ["au", "us", "eu"],
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": True,
        "player_props": [
            "player_goals",
            "player_assists",
            "player_points",
        ],
        "time_window_hours": 48,
        "min_events": 1,
        "notes": "Canadian/US focus",
    },
    "soccer_epl": {
        "name": "EPL",
        "league": "EPL",
        "regions": ["au", "us", "eu"],
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": True,
        "player_props": [
            "player_goals",
            "player_assists",
            "player_shots",
        ],
        "time_window_hours": 48,
        "min_events": 1,
        "notes": "English Premier League",
    },
    "soccer_uefa_champs_league": {
        "name": "Champions League",
        "league": "Champions League",
        "regions": ["au", "us", "eu"],
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": True,
        "player_props": [
            "player_goals",
            "player_assists",
        ],
        "time_window_hours": 72,
        "min_events": 0,
        "notes": "Seasonal - UEFA competition",
    },
    "tennis_atp": {
        "name": "ATP",
        "league": "Tennis",
        "regions": ["au", "us", "eu"],
        "base_markets": ["h2h"],  # Most tennis is h2h only
        "enabled": True,
        "player_props": ["player_sets", "player_games"],
        "time_window_hours": 48,
        "min_events": 1,
        "notes": "ATP Tour",
    },
    "tennis_wta": {
        "name": "WTA",
        "league": "Tennis",
        "regions": ["au", "us", "eu"],
        "base_markets": ["h2h"],
        "enabled": True,
        "player_props": ["player_sets", "player_games"],
        "time_window_hours": 48,
        "min_events": 1,
        "notes": "WTA Tour",
    },
    "cricket_big_bash": {
        "name": "Big Bash",
        "league": "Big Bash",
        "regions": ["au"],
        "base_markets": ["h2h", "totals"],
        "enabled": True,
        "player_props": [
            "player_runs",
            "player_wickets",
        ],
        "time_window_hours": 24,
        "min_events": 1,
        "notes": "Australian cricket - AU-only books",
    },
    "cricket_ipl": {
        "name": "IPL",
        "league": "IPL",
        "regions": ["au", "us", "eu"],
        "base_markets": ["h2h", "totals"],
        "enabled": True,
        "player_props": [
            "player_runs",
            "player_wickets",
        ],
        "time_window_hours": 24,
        "min_events": 1,
        "notes": "Indian Premier League",
    },
    "baseball_mlb": {
        "name": "MLB",
        "league": "MLB",
        "regions": ["au", "us"],
        "base_markets": ["h2h", "spreads", "totals"],
        "enabled": True,
        "player_props": [
            "player_home_runs",
            "player_rbis",
            "player_hits",
        ],
        "time_window_hours": 48,
        "min_events": 1,
        "notes": "Seasonal - active March-October",
    },
}

# ============================================================================
# BOOKMAKER RATINGS & WEIGHTING
# ============================================================================

BOOKMAKER_RATINGS = {
    # Sharp Books (Used for Fair Odds Calculation)
    "pinnacle": {"stars": 4, "category": "sharp", "region": ["eu"]},
    "betfair": {"stars": 4, "category": "sharp", "region": ["au", "eu"]},
    "betfair_au": {"stars": 4, "category": "sharp", "region": ["au"]},
    "draftkings": {"stars": 3, "category": "sharp", "region": ["us"]},
    "fanduel": {"stars": 3, "category": "sharp", "region": ["us"]},
    "betmgm": {"stars": 3, "category": "sharp", "region": ["us"]},

    # Target Books (For EV Detection)
    "sportsbet": {"stars": 1, "category": "target", "region": ["au"]},
    "tab": {"stars": 1, "category": "target", "region": ["au"]},
    "neds": {"stars": 1, "category": "target", "region": ["au"]},
    "pointsbet": {"stars": 1, "category": "target", "region": ["au", "us"]},
    "betright": {"stars": 1, "category": "target", "region": ["au"]},
    "dabble": {"stars": 1, "category": "target", "region": ["au"]},
    "unibet": {"stars": 1, "category": "target", "region": ["au", "eu"]},
    "ladbrokes": {"stars": 2, "category": "target", "region": ["au"]},
    "playup": {"stars": 1, "category": "target", "region": ["au"]},
    "betr": {"stars": 1, "category": "target", "region": ["au"]},
    "boombet": {"stars": 1, "category": "target", "region": ["au"]},

    # US Books
    "caesars": {"stars": 2, "category": "target", "region": ["us"]},
    "betrivers": {"stars": 2, "category": "target", "region": ["us"]},
    "williamhill": {"stars": 2, "category": "target", "region": ["us"]},
}

# Weight profiles per sport (how much each sharp contributes)
SPORT_WEIGHT_PROFILES = {
    "basketball_nba": {
        "pinnacle": 0.40,
        "draftkings": 0.35,
        "fanduel": 0.25,
    },
    "americanfootball_nfl": {
        "pinnacle": 0.40,
        "draftkings": 0.30,
        "fanduel": 0.30,
    },
    "icehockey_nhl": {
        "pinnacle": 0.40,
        "draftkings": 0.35,
        "fanduel": 0.25,
    },
    "soccer_epl": {
        "pinnacle": 0.50,
        "betfair": 0.50,
    },
    "soccer_uefa_champs_league": {
        "pinnacle": 0.50,
        "betfair": 0.50,
    },
    "tennis_atp": {
        "pinnacle": 1.0,
    },
    "tennis_wta": {
        "pinnacle": 1.0,
    },
    "cricket_ipl": {
        "pinnacle": 0.50,
        "betfair": 0.50,
    },
    "cricket_big_bash": {
        "betfair_au": 1.0,
    },
    "baseball_mlb": {
        "pinnacle": 0.40,
        "draftkings": 0.30,
        "fanduel": 0.30,
    },
}

# ============================================================================
# EV DETECTION THRESHOLDS
# ============================================================================

EV_CONFIG = {
    "min_ev_percent": 2.0,  # Only flag opportunities >2% edge
    "min_sharp_count": 2,   # Require at least 2 sharp books for fair odds
    "outlier_threshold": 0.05,  # Remove outliers >5% away from median
    "kelly_fraction": 0.25,  # Conservative Kelly criterion
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_enabled_sports() -> List[str]:
    """Get list of enabled sport keys"""
    return [k for k, v in SPORTS_CONFIG.items() if v["enabled"]]


def get_sport_regions(sport_key: str) -> List[str]:
    """Get regions for a specific sport"""
    return SPORTS_CONFIG.get(sport_key, {}).get("regions", ["au", "us"])


def get_sport_name(sport_key: str) -> str:
    """Get human-readable sport name"""
    return SPORTS_CONFIG.get(sport_key, {}).get("name", sport_key)


def is_sharp_book(bookmaker: str) -> bool:
    """Check if bookmaker is rated as 'sharp'"""
    return BOOKMAKER_RATINGS.get(bookmaker.lower(), {}).get("category") == "sharp"


def get_sharp_books() -> List[str]:
    """Get all sharp bookmaker names"""
    return [k for k, v in BOOKMAKER_RATINGS.items() if v["category"] == "sharp"]


def get_weight(sport_key: str, bookmaker: str) -> float:
    """Get weight for bookmaker in specific sport"""
    profile = SPORT_WEIGHT_PROFILES.get(sport_key, {})
    return profile.get(bookmaker.lower(), 0.0)
