"""
Totals (over/under) market handler.

KEY RULES:
1. NO AU BOOKMAKERS in fair price calculation (Pinnacle + Betfair only)
2. Similar to spreads - requires line matching
3. Two outcomes: Over, Under
"""
from typing import Dict, Optional
from .utils import snap_to_half, effective_back_odds_betfair
from .fair_prices import build_fair_prices_simple


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
    betfair_commission: float = 0.06
) -> Dict:
    """
    Process single totals event and calculate fair prices.
    
    Args:
        event: Event dict from API
        target_line: Target total line (e.g., 215.5)
        betfair_commission: Betfair commission rate
    
    Returns:
        Dict with fair prices and bookmaker odds:
        {
            "fair": {"over": fair_over, "under": fair_under},
            "pinnacle": {"over": pin_over, "under": pin_under},
            "bookmakers": {bkey: {"over": odds_over, "under": odds_under}, ...}
        }
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
    
    # Calculate fair prices
    fair_prices = build_fair_prices_simple(
        pin_over, pin_under,
        bf_over, bf_under,
        weight_pinnacle=0.7,
        weight_betfair=0.3
    )
    
    if not fair_prices:
        return {}
    
    return {
        "fair": {
            "over": fair_prices["A"],
            "under": fair_prices["B"]
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
