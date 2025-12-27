"""
Per-sport region configurations.

Each sport specifies:
- extract_from: Which regions to fetch from API
- time_window_hours: How far ahead to fetch
- sharp_priority: Order for fair odds weighting
- exclude_from_fair: Regions to skip in fair odds
"""

REGION_CONFIGS = {
    "basketball_nba": {
        "extract_from": ["au", "us", "us2", "eu"],
        "time_window_hours": 24,
        "sharp_priority": ["us", "eu", "au"],
        "exclude_from_fair": ["au"],  # AU only 1-star
        "notes": "NBA global, but AU weak"
    },
    
    "americanfootball_nfl": {
        "extract_from": ["us", "us2", "au"],
        "time_window_hours": 24,
        "sharp_priority": ["us"],
        "exclude_from_fair": [],
        "notes": "NFL US-focused, weekly"
    },
    
    "ice_hockey_nhl": {
        "extract_from": ["us", "us2", "au"],
        "time_window_hours": 48,
        "sharp_priority": ["us"],
        "exclude_from_fair": ["au"],
        "notes": "NHL US-focused"
    },
    
    "soccer_epl": {
        "extract_from": ["eu", "au", "us"],
        "time_window_hours": 72,
        "sharp_priority": ["eu", "us"],
        "exclude_from_fair": [],
        "notes": "Soccer EU-focused"
    },
    
    "tennis_atp": {
        "extract_from": ["au", "us", "eu"],
        "time_window_hours": 72,
        "sharp_priority": ["eu", "au"],
        "exclude_from_fair": [],
        "notes": "Tennis global"
    },
    
    "cricket_big_bash": {
        "extract_from": ["au"],
        "time_window_hours": 48,
        "sharp_priority": ["au"],
        "exclude_from_fair": [],
        "notes": "Cricket AU-only"
    },
}


def get_regions_for_sport(sport_key):
    """Get region config for sport"""
    return REGION_CONFIGS.get(sport_key, {
        "extract_from": ["au", "us"],
        "time_window_hours": 48,
        "sharp_priority": ["au", "us"],
        "exclude_from_fair": [],
    })
