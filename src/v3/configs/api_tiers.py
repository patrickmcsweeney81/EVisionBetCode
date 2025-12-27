"""
API tier configurations per sport.

Each sport specifies:
- Tier 1: Base markets (h2h, spreads, totals) - ALWAYS
- Tier 2: Player props (if enabled)
- Tier 3: Advanced markets (3-way, partials) - future analytics
"""

API_TIER_CONFIGS = {
    "basketball_nba": {
        "tier_1_base_markets": True,
        "tier_2_player_props": True,
        "tier_2_props_list": [
            "player_points",
            "player_rebounds",
            "player_assists",
        ],
        "tier_3_advanced_markets": False,
        "estimated_cost_per_run": 50,
        "notes": "NBA: Base + top 3 props"
    },
    
    "americanfootball_nfl": {
        "tier_1_base_markets": True,
        "tier_2_player_props": True,
        "tier_2_props_list": [
            "player_pass_yds",
            "player_rush_yds",
            "player_pass_tds",
        ],
        "tier_3_advanced_markets": False,
        "estimated_cost_per_run": 35,
        "notes": "NFL: Base + pass/rush yards + TDs"
    },
    
    "ice_hockey_nhl": {
        "tier_1_base_markets": True,
        "tier_2_player_props": False,  # Props sparse
        "tier_2_props_list": [],
        "tier_3_advanced_markets": False,
        "estimated_cost_per_run": 25,
        "notes": "NHL: Base markets only"
    },
    
    "soccer_epl": {
        "tier_1_base_markets": True,
        "tier_2_player_props": False,  # Props minimal
        "tier_2_props_list": [],
        "tier_3_advanced_markets": True,  # Track 3-way, partials
        "tier_3_advanced_list": ["h2h_3way", "over_under_partials"],
        "estimated_cost_per_run": 45,
        "notes": "Soccer: Base + advanced (3-way) for analytics"
    },
    
    "tennis_atp": {
        "tier_1_base_markets": True,
        "tier_2_player_props": False,  # Tennis H2H only
        "tier_2_props_list": [],
        "tier_3_advanced_markets": False,
        "estimated_cost_per_run": 20,
        "notes": "Tennis: H2H only"
    },
    
    "cricket_big_bash": {
        "tier_1_base_markets": True,
        "tier_2_player_props": False,
        "tier_2_props_list": [],
        "tier_3_advanced_markets": False,
        "estimated_cost_per_run": 20,
        "notes": "Cricket: Base markets only"
    },
}


def get_api_config_for_sport(sport_key):
    """Get API tier config for sport"""
    return API_TIER_CONFIGS.get(sport_key, {
        "tier_1_base_markets": True,
        "tier_2_player_props": False,
        "tier_2_props_list": [],
        "tier_3_advanced_markets": False,
        "estimated_cost_per_run": 25,
    })


def get_total_estimated_cost(sports_list):
    """Calculate total API cost for sports"""
    total = 0
    for sport_key in sports_list:
        config = get_api_config_for_sport(sport_key)
        total += config.get("estimated_cost_per_run", 25)
    return total
