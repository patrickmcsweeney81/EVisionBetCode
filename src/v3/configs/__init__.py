"""
Config module initialization.

Import all configurations here for easy access.
"""

from .sports import SPORTS_CONFIG, get_enabled_sports, get_sport_config, is_sport_enabled
from .bookmakers import BOOKMAKER_RATINGS, get_sharp_books, get_target_books, get_books_by_region
from .weights import SPORT_WEIGHT_PROFILES, get_weights_for_sport
from .fair_odds import FAIR_ODDS_CONFIGS, get_fair_odds_config
from .regions import REGION_CONFIGS, get_regions_for_sport
from .api_tiers import API_TIER_CONFIGS, get_api_config_for_sport, get_total_estimated_cost

__all__ = [
    'SPORTS_CONFIG',
    'get_enabled_sports',
    'get_sport_config',
    'is_sport_enabled',
    'BOOKMAKER_RATINGS',
    'get_sharp_books',
    'get_target_books',
    'get_books_by_region',
    'SPORT_WEIGHT_PROFILES',
    'get_weights_for_sport',
    'FAIR_ODDS_CONFIGS',
    'get_fair_odds_config',
    'REGION_CONFIGS',
    'get_regions_for_sport',
    'API_TIER_CONFIGS',
    'get_api_config_for_sport',
    'get_total_estimated_cost',
]
