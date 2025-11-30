"""
Spreads market handler - processes NBA/NFL spreads with Pinnacle as source of truth.

KEY RULES:
1. NO AU BOOKMAKERS in fair price calculation (Pinnacle + Betfair only)
2. Pinnacle determines canonical spread keys (e.g., "Team_-6.5")
3. Other books must match Pinnacle's line within tolerance
4. Sign convention: Use Pinnacle's signs as truth
"""
from typing import Dict, List, Optional, Tuple
from .utils import snap_to_half, effective_back_odds_betfair
from .fair_prices import build_fair_prices_two_way  # unified v2 fair prices
from .utils import devig_two_way


# Import AU bookmaker list from config
from .config import AU_BOOKIES

# Sharp books for fair prices (NO AU BOOKS)
SHARP_BOOKIES = ["pinnacle", "betfair_ex_au", "betfair_ex_uk"]

LINE_TOLERANCE = 0.25  # Accept lines within 0.25 of target


def extract_spread_odds(bookmaker_data: Dict, line: float, betfair_commission: float = 0.06, include_au: bool = False) -> Dict[str, Dict[str, float]]:
    """
    Extract spread odds from bookmaker data for specific line.
    
    Args:
        bookmaker_data: Single bookmaker dict from API
        line: Target spread line (e.g., -6.5)
        betfair_commission: Commission for Betfair (default 0.06)
        include_au: If True, include AU bookmakers (for EV comparison). If False, skip them (for fair calc)
    
    Returns:
        Dict with keys like "TeamName_-6.5" -> odds value
        Empty dict if line not found or (AU book and include_au=False)
    """
    bkey = bookmaker_data.get("key", "")
    
    # Skip AU bookmakers ONLY if include_au=False (for fair price calculation)
    if not include_au and bkey in AU_BOOKIES:
        return {}
    
    markets = bookmaker_data.get("markets", [])
    spread_market = None
    
    for mkt in markets:
        if mkt.get("key") == "spreads":
            spread_market = mkt
            break
    
    if not spread_market:
        return {}
    
    outcomes = spread_market.get("outcomes", [])
    result = {}
    
    for out in outcomes:
        name = out.get("name", "")
        point = out.get("point")
        price = out.get("price")
        
        if point is None or price is None:
            continue
        
        # Snap to half-point
        snapped_point = snap_to_half(float(point))
        
        # For spreads, opposite sides have opposite signs but SAME absolute value
        # E.g., Home -6.5, Away +6.5 - both match line=6.5
        # Check if within tolerance of target line (absolute value)
        if abs(abs(snapped_point) - abs(line)) > LINE_TOLERANCE:
            continue
        
        # Build outcome key: "TeamName_point"
        out_key = f"{name}_{snapped_point}"
        
        # Adjust Betfair for commission
        if bkey in ["betfair_ex_au", "betfair_ex_uk"]:
            odds = effective_back_odds_betfair(price, betfair_commission)
        else:
            odds = price
        
        result[out_key] = odds
    
    return result


def canonicalize_spread_key(key: str, home_team: str) -> str:
    """
    Ensure consistent spread key format: home team gets negative, away gets positive.
    
    Args:
        key: Outcome key like "Cleveland Cavaliers_-6.5"
        home_team: Home team name
    
    Returns:
        Canonical key (home negative, away positive)
    """
    if "_" not in key:
        return key
    
    team, point_str = key.rsplit("_", 1)
    point = float(point_str)
    
    # If this is home team and point is positive, flip sign
    if team == home_team and point > 0:
        return f"{team}_{-point}"
    
    # If this is away team and point is negative, flip sign
    if team != home_team and point < 0:
        return f"{team}_{-point}"
    
    return key


def process_spread_event(
    event: Dict,
    target_line: float,
    home_team: str,
    away_team: str,
    betfair_commission: float = 0.06,
    sport: Optional[str] = None
) -> Dict:
    """
    Process single spread event and calculate fair prices (v2 unified).

    Uses weighted median of devigged sharp odds via book_weights system.
    Pinnacle still required as line anchor; AU books excluded from fair calc.
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
            spread_odds = extract_spread_odds(bk, target_line, betfair_commission, include_au=False)
            if spread_odds:
                pinnacle_odds = spread_odds
        elif bkey in ["betfair_ex_au", "betfair_ex_uk"]:
            spread_odds = extract_spread_odds(bk, target_line, betfair_commission, include_au=False)
            if spread_odds:
                betfair_odds = spread_odds
        elif bkey in AU_BOOKIES:
            # Extract AU books for EV comparison (include_au=True)
            spread_odds = extract_spread_odds(bk, target_line, betfair_commission, include_au=True)
            if spread_odds:
                all_book_odds[bkey] = spread_odds
    
    if not pinnacle_odds:
        return {}  # No Pinnacle, no fair price
    
    # Pinnacle should have exactly 2 outcomes for spreads
    if len(pinnacle_odds) != 2:
        return {}
    
    # Get Pinnacle keys (canonical keys)
    pin_keys = list(pinnacle_odds.keys())
    
    # Determine which key is home vs away
    home_key = None
    away_key = None
    
    for key in pin_keys:
        team = key.rsplit("_", 1)[0]
        if team == home_team:
            home_key = key
        elif team == away_team:
            away_key = key
    
    if not home_key or not away_key:
        return {}
    
    # Extract odds values
    pin_home = pinnacle_odds[home_key]
    pin_away = pinnacle_odds[away_key]
    
    # Betfair odds (optional)
    bf_home = betfair_odds.get(home_key)
    bf_away = betfair_odds.get(away_key)
    
    # Build devigged sharp odds dicts for home/away sides
    bookmaker_odds_home: Dict[str, float] = {}
    bookmaker_odds_away: Dict[str, float] = {}

    # Devig Pinnacle
    p_home_prob, p_away_prob = devig_two_way(pin_home, pin_away)
    if p_home_prob > 0 and p_away_prob > 0:
        bookmaker_odds_home["pinnacle"] = 1.0 / p_home_prob
        bookmaker_odds_away["pinnacle"] = 1.0 / p_away_prob

    # Devig Betfair if present (side-specific odds)
    if bf_home and bf_away:
        bf_home_prob, bf_away_prob = devig_two_way(bf_home, bf_away)
        if bf_home_prob > 0 and bf_away_prob > 0:
            # Preserve original betfair key used for weights
            # Choose whichever betfair key present in event extraction
            bf_key = "betfair_ex_au" if "betfair_ex_au" in [bk.get("key") for bk in bookmakers] else "betfair_ex_uk"
            bookmaker_odds_home[bf_key] = 1.0 / bf_home_prob
            bookmaker_odds_away[bf_key] = 1.0 / bf_away_prob

    fair_prices_v2 = build_fair_prices_two_way(
        bookmaker_odds_home,
        bookmaker_odds_away,
        market_type="main",
        sport=sport
    )

    if not fair_prices_v2:
        return {}
    
    return {
        "fair": {
            "home": fair_prices_v2["A"],
            "away": fair_prices_v2["B"]
        },
        "pinnacle": {
            "home": pin_home,
            "away": pin_away
        },
        "betfair": {
            "home": bf_home,
            "away": bf_away
        },
        "bookmakers": all_book_odds,
        "keys": {
            "home": home_key,
            "away": away_key
        }
    }
