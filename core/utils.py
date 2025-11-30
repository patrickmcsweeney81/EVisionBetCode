"""
Utility functions for EV Bot.
Extracted from ev_arb_bot.py for modularity.
"""
from typing import Tuple, List, Dict
from statistics import median


def devig_two_way(odds1: float, odds2: float) -> Tuple[float, float]:
    """
    Remove bookmaker margin using multiplicative method.
    Returns true probabilities (p1, p2) that sum to 1.0.
    """
    if odds1 <= 0 or odds2 <= 0:
        return (0.0, 0.0)
    
    p1_raw = 1.0 / odds1
    p2_raw = 1.0 / odds2
    total = p1_raw + p2_raw
    
    if total <= 0:
        return (0.0, 0.0)
    
    # Normalize to sum to 1.0
    return (p1_raw / total, p2_raw / total)


def snap_to_half(x: float) -> float:
    """Round to nearest 0.5 (half-point)."""
    return round(x * 2) / 2


def effective_back_odds_betfair(raw_odds: float, commission: float) -> float:
    """
    Adjust Betfair odds for commission.
    Effective odds = 1 + (raw_odds - 1) * (1 - commission)
    """
    if raw_odds <= 1:
        return raw_odds
    return 1.0 + (raw_odds - 1.0) * (1.0 - commission)


def calculate_margin(odds1: float, odds2: float) -> float:
    """Calculate bookmaker margin as percentage."""
    if odds1 <= 0 or odds2 <= 0:
        return 100.0
    return ((1.0 / odds1 + 1.0 / odds2) - 1.0) * 100.0


def kelly_stake(bankroll: float, fair_odds: float, market_odds: float, kelly_fraction: float = 0.25) -> float:
    """
    Calculate Kelly Criterion stake.
    
    Args:
        bankroll: Total bankroll
        fair_odds: Fair (true) odds
        market_odds: Bookmaker odds
        kelly_fraction: Fraction of full Kelly (default 0.25 = quarter Kelly)
    
    Returns:
        Recommended stake amount
    """
    if fair_odds <= 0 or market_odds <= 0:
        return 0.0
    
    # Edge = (fair_prob * market_odds - 1)
    fair_prob = 1.0 / fair_odds
    edge = fair_prob * market_odds - 1.0
    
    if edge <= 0:
        return 0.0
    
    # Kelly = edge / (market_odds - 1)
    kelly_pct = edge / (market_odds - 1.0)
    
    # Apply fraction and bankroll
    stake = bankroll * kelly_pct * kelly_fraction
    
    return max(0.0, stake)


def weighted_median(values_with_weights: List[Tuple[float, int]]) -> float:
    """
    Calculate weighted median using book weights (0-4 scale).
    
    Args:
        values_with_weights: List of (value, weight) tuples
    
    Returns:
        Weighted median value, or 0.0 if no valid values
    
    Examples:
        >>> weighted_median([(2.0, 4), (2.1, 3), (2.2, 1)])
        2.0  # Weight 4 dominates
        >>> weighted_median([(2.0, 2), (2.1, 2), (2.2, 2)])
        2.1  # Simple median when equal weights
    """
    if not values_with_weights:
        return 0.0
    
    # Filter out zero/negative values and weights
    valid = [(v, w) for v, w in values_with_weights if v > 0 and w > 0]
    if not valid:
        return 0.0
    
    # For weights >= 3 (strong sharps), use simple median of those
    # This prioritizes tier-1 sharps without over-complicating
    tier1_values = [v for v, w in valid if w >= 3]
    if tier1_values:
        return median(tier1_values)
    
    # Otherwise use all values (weight 1-2 books)
    all_values = [v for v, w in valid]
    return median(all_values) if all_values else 0.0


def get_sharp_books_by_weight(
    bookmaker_odds: Dict[str, float],
    market_type: str = "main",
    sport: str = None,
    min_weight: int = 3
) -> List[Tuple[str, float, int]]:
    """
    Filter bookmakers by weight threshold and return (book_key, odds, weight).
    
    Args:
        bookmaker_odds: Dict of {book_key: odds}
        market_type: "main" or "props"
        sport: Optional sport code for overrides
        min_weight: Minimum weight to include (default 3 = strong sharps only)
    
    Returns:
        List of (book_key, odds, weight) tuples for books >= min_weight
    """
    from .book_weights import get_book_weight
    
    result = []
    for book_key, odds in bookmaker_odds.items():
        if odds <= 0:
            continue
        weight = get_book_weight(book_key, market_type, sport)
        if weight >= min_weight:
            result.append((book_key, odds, weight))
    
    return result
