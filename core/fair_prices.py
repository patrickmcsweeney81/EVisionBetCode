"""
Fair price calculation using sharp bookmakers (Pinnacle, Betfair, other sharps).
NO AU BOOKMAKERS in fair price calculation - they are targets only.

Weights: Pinnacle 60%, Betfair 25%, Other sharps 15%
Sharp books: pinnacle, betfair_ex_eu, betfair_ex_au, betonlineag, bovada, 
             betus, lowvig, mybookieag, marathonbet, matchbook
"""
from typing import Dict, Optional, List
from statistics import median
from .utils import devig_two_way
from .config import SHARP_BOOKIES, WEIGHT_PINNACLE, WEIGHT_BETFAIR, WEIGHT_OTHER_SHARPS


def master_fair_odds(
    pinnacle_odds: Optional[float],
    betfair_odds: Optional[float],
    other_sharps_odds: List[float],
    weight_pinnacle: float = WEIGHT_PINNACLE,
    weight_betfair: float = WEIGHT_BETFAIR,
    weight_sharps: float = WEIGHT_OTHER_SHARPS
) -> float:
    """
    Combine Pinnacle, Betfair, and other sharps into single fair price.
    Uses WEIGHTED probabilities.
    
    Args:
        pinnacle_odds: Pinnacle fair odds (or None)
        betfair_odds: Betfair commission-adjusted odds (or None)
        other_sharps_odds: List of other sharp book odds
        weight_pinnacle: Weight for Pinnacle (default 60%)
        weight_betfair: Weight for Betfair (default 25%)
        weight_sharps: Weight for other sharps (default 15%)
    
    Returns:
        Final fair odds (or 0.0 if no valid inputs)
    """
    components = []
    
    if pinnacle_odds and pinnacle_odds > 0:
        components.append((pinnacle_odds, weight_pinnacle))
    
    if betfair_odds and betfair_odds > 0:
        components.append((betfair_odds, weight_betfair))
    
    # Calculate median of other sharps if we have at least 2
    if other_sharps_odds and len(other_sharps_odds) >= 2:
        valid_sharps = [o for o in other_sharps_odds if o > 0]
        if valid_sharps:
            median_odds = median(valid_sharps)
            components.append((median_odds, weight_sharps))
    
    if not components:
        return 0.0
    
    # Normalize weights
    w_sum = sum(w for _, w in components)
    if w_sum <= 0:
        # Fallback to simple average
        probs = [1.0 / o for (o, _) in components if o > 0]
        if not probs:
            return 0.0
        p_star = sum(probs) / len(probs)
        return (1.0 / p_star) if p_star > 0 else 0.0
    
    # Weighted probability average
    p_star = 0.0
    for odds_i, w_i in components:
        if odds_i <= 0:
            continue
        p_i = 1.0 / odds_i
        p_star += p_i * (w_i / w_sum)
    
    return (1.0 / p_star) if p_star > 0 else 0.0


def build_fair_prices_simple(
    pin_odds_a: Optional[float],
    pin_odds_b: Optional[float],
    bf_odds_a: Optional[float],
    bf_odds_b: Optional[float],
    other_sharps_a: Optional[List[float]] = None,
    other_sharps_b: Optional[List[float]] = None,
    weight_pinnacle: float = WEIGHT_PINNACLE,
    weight_betfair: float = WEIGHT_BETFAIR,
    weight_sharps: float = WEIGHT_OTHER_SHARPS
) -> Dict[str, float]:
    """
    Fair price calculation for 2-way markets using Pinnacle + other sharps.
    REQUIRES PINNACLE - will return empty dict if no Pinnacle odds.
    
    Args:
        pin_odds_a: Pinnacle odds for outcome A (REQUIRED)
        pin_odds_b: Pinnacle odds for outcome B (REQUIRED)
        bf_odds_a: Betfair odds for outcome A (IGNORED - not used)
        bf_odds_b: Betfair odds for outcome B (IGNORED - not used)
        other_sharps_a: List of other sharp book odds for outcome A
        other_sharps_b: List of other sharp book odds for outcome B
        weight_pinnacle: Pinnacle weight (default 75%)
        weight_betfair: Betfair weight (default 0% - not used)
        weight_sharps: Other sharps weight (default 25%)
    
    Returns:
        {"A": fair_a, "B": fair_b} or empty dict if no Pinnacle
    """
    # REQUIRE Pinnacle - no Pinnacle = no fair price
    if not pin_odds_a or not pin_odds_b or pin_odds_a <= 0 or pin_odds_b <= 0:
        return {}
    
    fair_a_components = {}
    fair_b_components = {}
    
    # Pinnacle devig (REQUIRED)
    p_a, p_b = devig_two_way(pin_odds_a, pin_odds_b)
    if p_a > 0:
        fair_a_components["pinnacle"] = 1.0 / p_a
    if p_b > 0:
        fair_b_components["pinnacle"] = 1.0 / p_b
    
    # Betfair - SKIP (not used per user request)
    
    # Other sharps - use median if we have at least 2
    other_sharps_a = other_sharps_a or []
    other_sharps_b = other_sharps_b or []
    
    if len(other_sharps_a) >= 2:
        valid_a = [o for o in other_sharps_a if o > 0]
        if valid_a:
            fair_a_components["other_sharps"] = median(valid_a)
    
    if len(other_sharps_b) >= 2:
        valid_b = [o for o in other_sharps_b if o > 0]
        if valid_b:
            fair_b_components["other_sharps"] = median(valid_b)
    
    # Combine components: Weighted average of ALREADY DEVIGGED fair odds
    fair_a = 0.0
    fair_b = 0.0
    
    pin_a = fair_a_components.get("pinnacle")
    pin_b = fair_b_components.get("pinnacle")
    sharps_a = fair_a_components.get("other_sharps")
    sharps_b = fair_b_components.get("other_sharps")
    
    # Calculate fair_a: 75% Pinnacle + 25% other sharps median
    components_a = []
    if pin_a:
        components_a.append((pin_a, weight_pinnacle))
    if sharps_a:
        components_a.append((sharps_a, weight_sharps))
    
    if components_a:
        total_weight = sum(w for _, w in components_a)
        fair_a = sum(odds * w for odds, w in components_a) / total_weight
    
    # Calculate fair_b: 75% Pinnacle + 25% other sharps median
    components_b = []
    if pin_b:
        components_b.append((pin_b, weight_pinnacle))
    if sharps_b:
        components_b.append((sharps_b, weight_sharps))
    
    if components_b:
        total_weight = sum(w for _, w in components_b)
        fair_b = sum(odds * w for odds, w in components_b) / total_weight
    
    if fair_a > 0 and fair_b > 0:
        return {"A": fair_a, "B": fair_b}
    
    return {}
