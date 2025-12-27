"""
EVisionBet weight profiles per sport.

Weight profiles are DYNAMICALLY BUILT from bookmakers.py star ratings.

How it works:
1. Only books rated 3⭐ or 4⭐ are used for fair odds
2. Each sharp book has a weight_nba, weight_nfl, etc.
3. Weights sum to 1.0 per sport (normalized)

These weights are:
- Used for fair odds calculation in backend
- NEVER shown to users directly
- Users can adjust weights 0-4 per bookmaker for recalculation
"""

from src.v3.configs.bookmakers import BOOKMAKER_RATINGS, get_sharp_books, get_weight_for_sport

# ============================================================================
# DYNAMIC WEIGHT GENERATION from bookmakers.py
# ============================================================================

# Placeholder - actual weights are built dynamically
SPORT_WEIGHT_PROFILES = {}

def get_weights_for_sport(sport_key):
    """
    Get weight profile for a sport from sharp books (3-4⭐)
    
    Returns dict of {bookmaker: weight} where weights sum to 1.0
    
    Example for NBA:
    {
        "pinnacle": 0.35,
        "draftkings": 0.30,
        "fanduel": 0.30,
        "betfair_ex_eu": 0.05,
    }
    """
    sharps = get_sharp_books()
    weights = {}
    total_weight = 0.0
    
    # Collect weights for this sport
    for book, info in sharps.items():
        weight = get_weight_for_sport(book, sport_key)
        if weight > 0:
            weights[book] = weight
            total_weight += weight
    
    # Normalize to sum to 1.0
    if total_weight > 0:
        for book in weights:
            weights[book] = weights[book] / total_weight
    
    return weights
