"""Fair odds utilities.

Note: These helpers do not strip bookmaker vig/overround because only single-sided
prices are available per outcome when invoked. To de-vig, you need both sides of a
market for the same bookmaker.
"""
from statistics import median
from typing import List, Optional


def _adjust_betfair(odds: Optional[float], commission: float) -> Optional[float]:
    if odds is None or odds <= 1.0:
        return None
    return 1 + (odds - 1) * (1 - commission)


def calculate_fair_odds(
    pinnacle_odds: Optional[float],
    betfair_odds: Optional[float],
    other_sharps_odds: List[float],
    weight_pinnacle: float = 0.6,
    weight_betfair: float = 0.25,
    weight_sharps: float = 0.15,
    betfair_commission: float = 0.06,
) -> float:
    """Weighted fair odds from sharp prices (no vig removal).

    - Pinnacle and Betfair are included if > 1.0.
    - Betfair is adjusted for commission.
    - Other sharps use median if 2+ valid prices.
    """
    components = []

    if pinnacle_odds and pinnacle_odds > 1.0:
        components.append((pinnacle_odds, weight_pinnacle))

    betfair_adj = _adjust_betfair(betfair_odds, betfair_commission)
    if betfair_adj:
        components.append((betfair_adj, weight_betfair))

    if other_sharps_odds and len(other_sharps_odds) >= 2:
        valid_sharps = [o for o in other_sharps_odds if o and o > 1.0]
        if valid_sharps:
            components.append((median(valid_sharps), weight_sharps))

    if not components:
        return 0.0

    weight_sum = sum(w for _, w in components)
    if weight_sum <= 0:
        return 0.0

    prob_star = 0.0
    for odds_val, w_val in components:
        if odds_val <= 1.0:
            continue
        prob_star += (1.0 / odds_val) * (w_val / weight_sum)

    return (1.0 / prob_star) if prob_star > 0 else 0.0
