"""
Totals (over/under) market handler.

KEY RULES:
1. NO AU BOOKMAKERS in fair price calculation (Pinnacle + Betfair only)
2. Similar to spreads - requires line matching
3. Two outcomes: Over, Under
"""
from typing import Dict, Optional
from .utils import snap_to_half, effective_back_odds_betfair
from .fair_prices import build_fair_prices_two_way  # unified v2 fair prices
from .utils import devig_two_way


# Import AU bookmaker list from config
from .config import AU_BOOKIES

# Sharp books for fair prices (NO AU BOOKS)
SHARP_BOOKIES = ["pinnacle", "betfair_ex_au", "betfair_ex_uk"]

LINE_TOLERANCE = 0.25  # Accept lines within 0.25 of target


def extract_totals_odds(bookmaker_data: Dict, line: float, betfair_commission: float = 0.06, include_au: bool = False) -> Dict[str, float]:
    """
    Extract totals odds from bookmaker data for specific line.
    
    Args:
        bookmaker_data: Single bookmaker dict from API
        line: Target total line (e.g., 215.5)
        betfair_commission: Commission for Betfair (default 0.06)
        include_au: If True, include AU bookmakers (for EV comparison). If False, skip them (for fair calc)
    
    Returns:
        Dict with "Over" and/or "Under" as keys -> odds values
        Empty dict if line not found or (AU book and include_au=False)
    """
    bkey = bookmaker_data.get("key", "")
    
    # Skip AU bookmakers ONLY if include_au=False (for fair price calculation)
    if not include_au and bkey in AU_BOOKIES:
        return {}
    
    markets = bookmaker_data.get("markets", [])
    totals_market = None
    
    for mkt in markets:
        if mkt.get("key") == "totals":
            totals_market = mkt
            break
    
    if not totals_market:
        return {}
    
    outcomes = totals_market.get("outcomes", [])
    result = {}
    
    for out in outcomes:
        name = out.get("name", "")  # "Over" or "Under"
        point = out.get("point")
        price = out.get("price")
        
        if point is None or price is None:
            continue
        
        # Snap to half-point
        snapped_point = snap_to_half(float(point))
        
        # Check if within tolerance of target line
        if abs(snapped_point - line) > LINE_TOLERANCE:
            continue
        
        # Adjust Betfair for commission
        if bkey in ["betfair_ex_au", "betfair_ex_uk"]:
            odds = effective_back_odds_betfair(price, betfair_commission)
        else:
            odds = price
        
        result[name] = odds
    
    return result


def process_totals_event(
    event: Dict,
    target_line: float,
    betfair_commission: float = 0.06,
    sport: Optional[str] = None
) -> Dict:
    """
    Process single totals (over/under) event and calculate fair prices (v2 unified).

    Uses weighted median of devigged sharp odds via book_weights system.
    Pinnacle required as line anchor; AU books excluded from fair calc.
    """
    bookmakers = event.get("bookmakers", [])
    
    # Extract Pinnacle odds first (source of truth)
    pinnacle_odds = {}
    betfair_odds = {}
    all_book_odds = {}
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        
        # Extract for fair calculation (excludes AU books)
        if bkey == "pinnacle":
            totals_odds = extract_totals_odds(bk, target_line, betfair_commission, include_au=False)
            if totals_odds:
                pinnacle_odds = totals_odds
        elif bkey in ["betfair_ex_au", "betfair_ex_uk"]:
            totals_odds = extract_totals_odds(bk, target_line, betfair_commission, include_au=False)
            if totals_odds:
                betfair_odds = totals_odds
        elif bkey in AU_BOOKIES:
            # Extract AU books for EV comparison (include_au=True)
            totals_odds = extract_totals_odds(bk, target_line, betfair_commission, include_au=True)
            if totals_odds:
                all_book_odds[bkey] = totals_odds
    
    if not pinnacle_odds:
        return {}  # No Pinnacle, no fair price
    
    # Pinnacle should have exactly 2 outcomes for totals (Over/Under)
    if len(pinnacle_odds) != 2:
        return {}
    
    # Get Over/Under odds
    pin_over = pinnacle_odds.get("Over")
    pin_under = pinnacle_odds.get("Under")
    
    if not pin_over or not pin_under:
        return {}
    
    # Betfair odds (optional)
    bf_over = betfair_odds.get("Over")
    bf_under = betfair_odds.get("Under")
    
    # Build devigged sharp odds dicts for over/under
    bookmaker_odds_over: Dict[str, float] = {}
    bookmaker_odds_under: Dict[str, float] = {}

    p_over_prob, p_under_prob = devig_two_way(pin_over, pin_under)
    if p_over_prob > 0 and p_under_prob > 0:
        bookmaker_odds_over["pinnacle"] = 1.0 / p_over_prob
        bookmaker_odds_under["pinnacle"] = 1.0 / p_under_prob

    if bf_over and bf_under:
        bf_over_prob, bf_under_prob = devig_two_way(bf_over, bf_under)
        if bf_over_prob > 0 and bf_under_prob > 0:
            bf_key = "betfair_ex_au" if "betfair_ex_au" in [bk.get("key") for bk in bookmakers] else "betfair_ex_uk"
            bookmaker_odds_over[bf_key] = 1.0 / bf_over_prob
            bookmaker_odds_under[bf_key] = 1.0 / bf_under_prob

    fair_prices_v2 = build_fair_prices_two_way(
        bookmaker_odds_over,
        bookmaker_odds_under,
        market_type="main",
        sport=sport
    )

    if not fair_prices_v2:
        return {}
    
    return {
        "fair": {
            "over": fair_prices_v2["A"],
            "under": fair_prices_v2["B"]
        },
        "pinnacle": {
            "over": pin_over,
            "under": pin_under
        },
        "betfair": {
            "over": bf_over,
            "under": bf_under
        },
        "bookmakers": all_book_odds,
        "line": target_line
    }
