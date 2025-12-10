"""
Unified fair price calculation module.

SINGLE SOURCE OF TRUTH (v2): `core/book_weights.py`
- Uses 0–4 integer weights per bookmaker, sport, and market_type.
- Fair odds derived via weighted median of devigged sharp odds.
- All active handlers (H2H, spreads, totals, props) use v2 functions.

LEGACY (deprecated - pending removal): Percentage-based functions retained temporarily:
  - master_fair_odds() - for old tests/scripts
  - build_fair_prices_simple() - for backward compatibility
These will be removed after validation window. All new code uses:
  - build_fair_price_from_books()
  - build_fair_prices_two_way()

AU bookmakers are NEVER included in fair price construction; they are only EV targets.
"""
from typing import Dict, Optional, List
from statistics import median
from .utils import devig_two_way
from .config import SHARP_BOOKIES, WEIGHT_PINNACLE, WEIGHT_BETFAIR, WEIGHT_OTHER_SHARPS  # legacy defaults (deprecated)

# NEW: Import book_weights system for v2.0 fair price calculation
try:
    from .utils import weighted_median, get_sharp_books_by_weight
    from .book_weights import get_book_weight
    BOOK_WEIGHTS_AVAILABLE = True
except ImportError:
    BOOK_WEIGHTS_AVAILABLE = False


def build_fair_price_from_books(
    bookmaker_odds: Dict[str, float],
    market_type: str = "main",
    sport: Optional[str] = None,
    min_weight: int = 3
) -> float:
    """
    NEW (v2.0): Calculate fair odds using book_weights system (0-4 scale).
    
    Args:
        bookmaker_odds: Dict of {book_key: odds} (already devigged if 2-way)
        market_type: "main" (h2h/spreads/totals) or "props"
        sport: Optional sport code for overrides (e.g., "NBA", "NFL", "MMA")
        min_weight: Minimum weight to include (default 3 = strong sharps only)
    
    Returns:
        Fair odds using weighted median, or 0.0 if insufficient sharp data
    """
    if not BOOK_WEIGHTS_AVAILABLE or not bookmaker_odds:
        return 0.0
    
    # Get sharp books with their weights
    sharp_books = get_sharp_books_by_weight(bookmaker_odds, market_type, sport, min_weight)
    
    if not sharp_books:
        return 0.0
    
    # Require at least 2 sharp books (weight >= 3)
    if len(sharp_books) < 2:
        return 0.0

    # If only Betfair is present, skip (do not use Betfair-only fair prices)
    if len(sharp_books) == 1:
        book_key = sharp_books[0][0]
        if book_key.startswith("betfair_ex_"):
            return 0.0

    # If exactly 2 sharp books and both are Betfair (e.g., AU and EU), skip
    if len(sharp_books) == 2:
        book_keys = [bk[0] for bk in sharp_books]
        if all(k.startswith("betfair_ex_") for k in book_keys):
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
    NEW (v2.0): Calculate fair prices for 2-way market using book_weights system.
    
    Args:
        bookmaker_odds_a: Dict of {book_key: odds} for outcome A (already devigged)
        bookmaker_odds_b: Dict of {book_key: odds} for outcome B (already devigged)
        market_type: "main" or "props"
        sport: Optional sport code
    
    Returns:
        {"A": fair_a, "B": fair_b} or empty dict if insufficient data
    """
    if not BOOK_WEIGHTS_AVAILABLE:
        return {}
    
    fair_a = build_fair_price_from_books(bookmaker_odds_a, market_type, sport)
    fair_b = build_fair_price_from_books(bookmaker_odds_b, market_type, sport)
    
    if fair_a > 0 and fair_b > 0:
        return {"A": fair_a, "B": fair_b}
    
    return {}


def master_fair_odds(
    pinnacle_odds: Optional[float],
    betfair_odds: Optional[float],
    other_sharps_odds: List[float],
    weight_pinnacle: float = WEIGHT_PINNACLE,
    weight_betfair: float = WEIGHT_BETFAIR,
    weight_sharps: float = WEIGHT_OTHER_SHARPS
) -> float:
    """
    DEPRECATED: Old percentage-based fair odds calculation.
    Retained for compatibility with legacy handlers/tests.
    Prefer build_fair_price_from_books() (v2 weighted median system).
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
    DEPRECATED: Old percentage-based 2-way fair price calculation.
    Requires Pinnacle. Returns empty dict if missing.
    Use build_fair_prices_two_way() for the unified v2 system.
    
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
