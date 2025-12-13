"""
Fair Prices Module - Unified interface for fair odds calculation.

This module provides the build_fair_prices_two_way() function used by all handlers
for calculating fair odds from sharp bookmakers using the book_weights system.
"""

from statistics import median
from typing import Dict, List, Optional, Tuple

from .book_weights import BOOKMAKER_RATINGS, get_sharp_books_only
from .utils import devig_two_way

# Re-export for backward compatibility
SHARP_BOOKIES = list(get_sharp_books_only())


def build_fair_prices_two_way(
    event_bookmakers: List[Dict],
    market_name: str,
    sport: Optional[str] = None,
    betfair_commission: float = 0.06,
) -> Tuple[Optional[float], Optional[float], int]:
    """
    Calculate fair odds from sharp bookmakers for a two-way market (Over/Under, Home/Away, etc).

    Uses the book_weights system to dynamically select and weight sharp bookmakers.

    Args:
        event_bookmakers: List of bookmaker dicts from API with their markets/outcomes
        market_name: Market type ('h2h', 'spreads', 'totals', etc)
        sport: Optional sport code for weight overrides
        betfair_commission: Betfair commission percentage (default 0.06)

    Returns:
        Tuple of (fair_odds_side1, fair_odds_side2, num_sharps_used)
        Returns (None, None, 0) if insufficient sharp data
    """

    # Get list of sharp books to consider
    sharp_books = get_sharp_books_only()

    if not sharp_books:
        return None, None, 0

    # Extract odds from each sharp bookmaker for this market
    sharp_odds = []

    for bm in event_bookmakers:
        bm_key = bm.get("key", "")

        if bm_key not in sharp_books:
            continue

        # Find the relevant market in this bookmaker's offerings
        market_odds = _extract_market_odds(bm, market_name, betfair_commission)

        if market_odds and len(market_odds) >= 2:
            sharp_odds.append(market_odds)

    # Need at least 2 sharp sources
    if len(sharp_odds) < 2:
        return None, None, len(sharp_odds)

    # De-vig each sharp's odds and calculate weighted fair odds
    devigged = []
    for odds_pair in sharp_odds:
        p1, p2 = devig_two_way(odds_pair[0], odds_pair[1])
        if p1 > 0 and p2 > 0:
            devigged.append((p1, p2))

    if not devigged:
        return None, None, 0

    # Take median of devigged probabilities
    side1_probs = [p1 for p1, p2 in devigged]
    side2_probs = [p2 for p1, p2 in devigged]

    fair_p1 = median(side1_probs)
    fair_p2 = median(side2_probs)

    # Convert back to odds (1/probability)
    fair_odds_1 = 1.0 / fair_p1 if fair_p1 > 0 else None
    fair_odds_2 = 1.0 / fair_p2 if fair_p2 > 0 else None

    return fair_odds_1, fair_odds_2, len(devigged)


def build_fair_prices_simple(
    event_bookmakers: List[Dict],
    market_name: str,
    sport: Optional[str] = None,
) -> Optional[float]:
    """
    Calculate simple fair odds (one-way market like h2h single outcome).
    Uses median of sharp bookmaker odds.

    Args:
        event_bookmakers: List of bookmaker dicts from API
        market_name: Market type
        sport: Optional sport code

    Returns:
        Fair odds as float, or None if insufficient data
    """
    sharp_books = get_sharp_books_only()

    if not sharp_books:
        return None

    sharp_odds = []

    for bm in event_bookmakers:
        bm_key = bm.get("key", "")
        if bm_key not in sharp_books:
            continue

        odds = _extract_single_outcome_odds(bm, market_name)
        if odds:
            sharp_odds.append(odds)

    # Need at least 2 sources
    if len(sharp_odds) < 2:
        return None

    return median(sharp_odds)


def _extract_market_odds(
    bookmaker_data: Dict,
    market_name: str,
    betfair_commission: float = 0.06,
) -> Optional[Tuple[float, float]]:
    """Extract two-way odds (e.g., Over/Under, Home/Away) from bookmaker data."""

    markets = bookmaker_data.get("markets", [])
    bm_key = bookmaker_data.get("key", "")

    for market in markets:
        if market.get("key") != market_name:
            continue

        outcomes = market.get("outcomes", [])

        # Extract first two outcomes
        odds_list = []
        for outcome in outcomes:
            price = outcome.get("price")
            if price and price > 0:
                # Adjust Betfair for commission
                if bm_key in ["betfair_ex_au", "betfair_ex_uk"]:
                    price = 1.0 + (price - 1.0) * (1.0 - betfair_commission)
                odds_list.append(price)

                if len(odds_list) >= 2:
                    return tuple(odds_list[:2])

        if len(odds_list) >= 2:
            return tuple(odds_list[:2])

    return None


def _extract_single_outcome_odds(
    bookmaker_data: Dict,
    market_name: str,
) -> Optional[float]:
    """Extract single outcome odds from bookmaker data."""

    markets = bookmaker_data.get("markets", [])

    for market in markets:
        if market.get("key") != market_name:
            continue

        outcomes = market.get("outcomes", [])

        if outcomes:
            price = outcomes[0].get("price")
            if price and price > 0:
                return price

    return None


# Legacy function names for backward compatibility
def build_fair_prices_h2h(event_bookmakers: List[Dict], sport: Optional[str] = None):
    """Legacy wrapper for h2h markets."""
    return build_fair_prices_two_way(event_bookmakers, "h2h", sport)


def build_fair_prices_spreads(event_bookmakers: List[Dict], sport: Optional[str] = None):
    """Legacy wrapper for spread markets."""
    return build_fair_prices_two_way(event_bookmakers, "spreads", sport)


def build_fair_prices_totals(event_bookmakers: List[Dict], sport: Optional[str] = None):
    """Legacy wrapper for totals markets."""
    return build_fair_prices_two_way(event_bookmakers, "totals", sport)


def master_fair_odds(
    pinnacle_odds: Optional[float],
    betfair_odds: Optional[float],
    other_sharps: List[float],
    weight_pinnacle: float = 0.6,
    weight_betfair: float = 0.25,
    weight_sharps: float = 0.15,
    betfair_commission: float = 0.06,
) -> float:
    """
    Legacy master_fair_odds function.
    Calculates weighted fair odds from sharp sources.

    Args:
        pinnacle_odds: Pinnacle odds (weight 0.6)
        betfair_odds: Betfair odds (weight 0.25)
        other_sharps: List of other sharp odds (weight 0.15, median if 2+)
        betfair_commission: Commission adjustment for Betfair

    Returns:
        Fair odds as float, or 0.0 if no valid data
    """
    from .fair_odds import _adjust_betfair

    components = []

    # Add Pinnacle
    if pinnacle_odds and pinnacle_odds > 1.0:
        components.append((pinnacle_odds, weight_pinnacle))

    # Add Betfair (with commission)
    if betfair_odds:
        betfair_adj = _adjust_betfair(betfair_odds, betfair_commission)
        if betfair_adj:
            components.append((betfair_adj, weight_betfair))

    # Add other sharps (use median if 2+)
    if other_sharps and len(other_sharps) >= 2:
        valid_sharps = [o for o in other_sharps if o and o > 1.0]
        if valid_sharps:
            components.append((median(valid_sharps), weight_sharps))

    if not components:
        return 0.0

    # Calculate weighted average
    weight_sum = sum(w for _, w in components)
    if weight_sum <= 0:
        return 0.0

    prob_sum = sum((1.0 / odds) * (weight / weight_sum) for odds, weight in components)

    return (1.0 / prob_sum) if prob_sum > 0 else 0.0
