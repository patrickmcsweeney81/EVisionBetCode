"""
Master sports configuration.

All sports defined here with:
- enabled: True/False (enable/disable for production)
- API tier settings
- Regions to extract
- Fair odds strategy
- EVisionBet hidden weights (0-4 per bookmaker)
"""

SPORTS_CONFIG = {
    # ============ BASKETBALL ============
    "basketball_nba": {
        "enabled": True,
        "title": "NBA",
        "group": "Basketball",
        "description": "US Basketball",
        
        # API TIER STRATEGY (per-sport customization)
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": True,
            "player_props_list": [
                "player_points",
                "player_rebounds",
                "player_assists",
            ],
            "fetch_advanced_markets": False,
        },
        
        # EVISIONBET HIDDEN WEIGHTS (0-4 per book)
        # Users see 0, cannot see your actual weights
        "evisionbet_weights": {
            "pinnacle": 4,
            "betfair": 3,
            "draftkings": 3,
            "fanduel": 3,
            "betfairaus": 2,
            "sportsbet": 1,
        },
    },
    
    # ============ AMERICAN FOOTBALL ============
    "americanfootball_nfl": {
        "enabled": True,
        "title": "NFL",
        "group": "American Football",
        "description": "US Football",
        
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": True,
            "player_props_list": [
                "player_pass_yds",
                "player_rush_yds",
                "player_pass_tds",
            ],
            "fetch_advanced_markets": False,
        },
        
        "evisionbet_weights": {
            "pinnacle": 4,
            "draftkings": 4,
            "fanduel": 3,
            "betfair": 2,
        },
    },
    
    # ============ ICE HOCKEY ============
    "ice_hockey_nhl": {
        "enabled": False,  # Will enable after testing
        "title": "NHL",
        "group": "Ice Hockey",
        "description": "US Ice Hockey",
        
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": False,
            "player_props_list": [],
            "fetch_advanced_markets": False,
        },
        
        "evisionbet_weights": {
            "pinnacle": 4,
            "draftkings": 3,
            "fanduel": 3,
        },
    },
    
    # ============ SOCCER ============
    "soccer_epl": {
        "enabled": False,  # Will enable after testing
        "title": "EPL",
        "group": "Soccer",
        "description": "English Premier League",
        
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": False,
            "fetch_advanced_markets": True,  # Track 3-way
        },
        
        "evisionbet_weights": {
            "pinnacle": 4,
            "betfair": 3,
        },
    },
    
    # ============ TENNIS ============
    "tennis_atp": {
        "enabled": False,  # Will enable after testing
        "title": "ATP",
        "group": "Tennis",
        "description": "Men's Professional Tennis",
        
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": False,
            "fetch_advanced_markets": False,
        },
        
        "evisionbet_weights": {
            "pinnacle": 4,
            "betfair": 3,
        },
    },
    
    # ============ CRICKET ============
    "cricket_big_bash": {
        "enabled": False,  # Will enable after testing
        "title": "Big Bash League",
        "group": "Cricket",
        "description": "Australian Cricket",
        
        "api_tiers": {
            "fetch_base_markets": True,
            "fetch_player_props": False,
            "fetch_advanced_markets": False,
        },
        
        "evisionbet_weights": {
            "pinnacle": 4,
            "betfairaus": 3,
        },
    },
}


def get_enabled_sports():
    """Get all enabled sports"""
    return {k: v for k, v in SPORTS_CONFIG.items() if v.get("enabled", True)}


def get_sport_config(sport_key):
    """Get config for specific sport"""
    return SPORTS_CONFIG.get(sport_key, {})


def is_sport_enabled(sport_key):
    """Check if sport is enabled"""
    return SPORTS_CONFIG.get(sport_key, {}).get("enabled", False)
