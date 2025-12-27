"""
Per-sport fair odds configurations.

Each sport can have custom:
- outlier_threshold: How aggressive to remove outliers
- min_sharp_count: Minimum sharps needed
- special_rules: Market-specific handling
"""

FAIR_ODDS_CONFIGS = {
    "basketball_nba": {
        "outlier_threshold": 0.05,  # Aggressive (sparse props)
        "min_sharp_count": 2,
        "special_rules": {
            "player_props": "ignore_au_books",  # AU books are 1-star for props
            "h2h": "use_all_books",
        },
        "notes": "NBA has many props, AU books weak for props"
    },
    
    "americanfootball_nfl": {
        "outlier_threshold": 0.03,  # Conservative (weekly events)
        "min_sharp_count": 1,
        "special_rules": {
            "h2h": "require_both_sides",
            "spreads": "require_both_sides",
        },
        "notes": "NFL weekly, need all available books"
    },
    
    "ice_hockey_nhl": {
        "outlier_threshold": 0.04,
        "min_sharp_count": 2,
        "special_rules": {},
        "notes": "Hockey midway through season"
    },
    
    "soccer_epl": {
        "outlier_threshold": 0.04,
        "min_sharp_count": 1,
        "special_rules": {
            "h2h": "include_3way_draw",  # Soccer has draws
        },
        "notes": "Soccer European focus, Pinnacle-weighted"
    },
    
    "tennis_atp": {
        "outlier_threshold": 0.03,  # Tight consensus
        "min_sharp_count": 1,
        "special_rules": {
            "h2h": "use_median",  # Tight consensus
        },
        "notes": "Tennis H2H only, sharp consensus"
    },
    
    "cricket_big_bash": {
        "outlier_threshold": 0.05,
        "min_sharp_count": 1,
        "special_rules": {},
        "notes": "Cricket AU-focused"
    },
}


def get_fair_odds_config(sport_key):
    """Get fair odds config for sport"""
    return FAIR_ODDS_CONFIGS.get(sport_key, {
        "outlier_threshold": 0.05,
        "min_sharp_count": 2,
        "special_rules": {},
    })
