"""
Fair price calculation using book_weights system (0-4 scale).

NEW SYSTEM (v2.0):
- Uses book_weights.py for flexible 0-4 weight scale
- Weight 4 = Primary sharps (Pinnacle, Circa, CRIS)
- Weight 3 = Strong sharps (BetOnline, DraftKings, FanDuel, Betfair exchanges)
- Weight 2-1 = Secondary books (followers)
- Weight 0 = Ignore (not used in fair calc)

Sport-specific overrides supported (MMA, NBA, NFL, NHL).
NO AU BOOKMAKERS in fair price calculation - they are targets only.
"""
from typing import Dict, Optional, List
from statistics import median
from .utils import devig_two_way, weighted_median, get_sharp_books_by_weight
from .book_weights import get_book_weight


def build_fair_price_from_books(
    bookmaker_odds: Dict[str, float],
    market_type: str = "main",
    sport: Optional[str] = None,
    min_weight: int = 3
) -> float:
    """
    Calculate fair odds using book_weights system.
    
    Args:
        bookmaker_odds: Dict of {book_key: odds} (already devigged if 2-way)
        market_type: "main" (h2h/spreads/totals) or "props"
        sport: Optional sport code for overrides (e.g., "NBA", "NFL", "MMA")
        min_weight: Minimum weight to include (default 3 = strong sharps only)
    
    Returns:
        Fair odds using weighted median, or 0.0 if insufficient sharp data
    """
    if not bookmaker_odds:
        return 0.0
    
    # Get sharp books with their weights
    sharp_books = get_sharp_books_by_weight(bookmaker_odds, market_type, sport, min_weight)
    
    if not sharp_books:
        return 0.0
    
    # Require at least 1 tier-1 sharp (weight >= 4) OR 2+ tier-2 sharps (weight >= 3)
    tier1_count = sum(1 for _, _, w in sharp_books if w >= 4)
    tier2_count = sum(1 for _, _, w in sharp_books if w >= 3)
    
    if tier1_count < 1 and tier2_count < 2:
        return 0.0
    
    # Use weighted median (prioritizes weight 4/3 books)
    values_with_weights = [(odds, weight) for _, odds, weight in sharp_books]
    return weighted_median(values_with_weights)


def build_fair_prices_two_way(
    bookmaker_odds_a: Dict[str, float],
    bookmaker_odds_b: Dict[str, float],
    market_type: str = "main",
    sport: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate fair prices for 2-way market using book_weights system.
    
    Args:
        bookmaker_odds_a: Dict of {book_key: odds} for outcome A (already devigged)
        bookmaker_odds_b: Dict of {book_key: odds} for outcome B (already devigged)
        market_type: "main" or "props"
        sport: Optional sport code
    
    Returns:
        {"A": fair_a, "B": fair_b} or empty dict if insufficient data
    """
    fair_a = build_fair_price_from_books(bookmaker_odds_a, market_type, sport)
    fair_b = build_fair_price_from_books(bookmaker_odds_b, market_type, sport)
    
    if fair_a > 0 and fair_b > 0:
        return {"A": fair_a, "B": fair_b}
    
    return {}


def collect_sharp_odds_by_outcome(
    event: Dict,
    outcome_keys: List[str],
    market_key: str,
    betfair_commission: float = 0.06,
    market_type: str = "main",
    sport: Optional[str] = None
) -> Dict[str, Dict[str, float]]:
    """
    Collect odds from sharp bookmakers for specific outcomes.
    Returns dict of {outcome_key: {book_key: odds}}.
    
    Args:
        event: Event dict from API
        outcome_keys: List of outcome keys to collect (e.g., ["home_team", "away_team"])
        market_key: Market key (e.g., "h2h", "spreads", "totals")
        betfair_commission: Commission for Betfair adjustment
        market_type: "main" or "props"
        sport: Optional sport code
    
    Returns:
        Dict of {outcome_key: {book_key: odds}}
    """
    from .utils import effective_back_odds_betfair
    
    result = {key: {} for key in outcome_keys}
    bookmakers = event.get("bookmakers", [])
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        
        # Check if this bookmaker has sufficient weight
        weight = get_book_weight(bkey, market_type, sport)
        if weight < 3:  # Only use strong sharps (weight >= 3)
            continue
        
        markets = bk.get("markets", [])
        for mkt in markets:
            if mkt.get("key") != market_key:
                continue
            
            outcomes = mkt.get("outcomes", [])
            for out in outcomes:
                name = out.get("name", "")
                price = out.get("price")
                
                if price is None or price <= 0:
                    continue
                
                # Adjust Betfair for commission
                if bkey in ["betfair_ex_au", "betfair_ex_eu"]:
                    odds = effective_back_odds_betfair(price, betfair_commission)
                else:
                    odds = price
                
                # Store odds for matching outcome
                for outcome_key in outcome_keys:
                    if name == outcome_key or outcome_key in name:
                        result[outcome_key][bkey] = odds
    
    return result
