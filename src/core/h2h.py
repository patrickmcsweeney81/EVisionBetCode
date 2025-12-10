"""
Head-to-Head (h2h) market handler - processes moneyline/match winner markets.

KEY RULES:
1. NO AU BOOKMAKERS in fair price calculation (uses Pinnacle, Betfair, and other sharps)
2. Simpler than spreads - no line matching needed
3. Two outcomes: home team win, away team win
"""
from typing import Dict, Optional, List
from .utils import effective_back_odds_betfair
from .fair_prices import build_fair_prices_simple, build_fair_prices_two_way
from .config import AU_BOOKIES

# Try to import book_weights system (v2.0)
try:
    from .book_weights import get_book_weight
    from .utils import devig_two_way
    BOOK_WEIGHTS_AVAILABLE = True
except ImportError:
    BOOK_WEIGHTS_AVAILABLE = False


def extract_h2h_odds_for_book(
    bookmaker_data: Dict,
    betfair_commission: float = 0.06,
    market_type: str = "main",
    sport: Optional[str] = None,
    min_weight: int = 3
) -> Dict[str, float]:
    """
    Extract h2h odds from single bookmaker (with book_weights filtering).
    
    Args:
        bookmaker_data: Single bookmaker dict from API
        betfair_commission: Commission for Betfair (default 0.06)
        market_type: "main" or "props" (h2h is always "main")
        sport: Optional sport code for weight overrides
        min_weight: Minimum weight to include (default 3 = strong sharps only)
    
    Returns:
        Dict with team names as keys -> odds values
        Empty dict if h2h market not found
    """
    bkey = bookmaker_data.get("key", "")
    
    # Skip AU bookmakers (they are targets, not for fair calc)
    if bkey in AU_BOOKIES:
        return {}
    
    # Check weight if book_weights available
    if BOOK_WEIGHTS_AVAILABLE:
        weight = get_book_weight(bkey, market_type, sport)
        if weight < min_weight:
            return {}
    
    markets = bookmaker_data.get("markets", [])
    h2h_market = None
    
    for mkt in markets:
        if mkt.get("key") == "h2h":
            h2h_market = mkt
            break
    
    if not h2h_market:
        return {}
    
    outcomes = h2h_market.get("outcomes", [])
    result = {}
    
    for out in outcomes:
        name = out.get("name", "")
        price = out.get("price")
        
        if not name or price is None:
            continue
        
        # Adjust Betfair for commission
        if bkey in ["betfair_ex_au", "betfair_ex_uk"]:
            odds = effective_back_odds_betfair(price, betfair_commission)
        else:
            odds = price
        
        result[name] = odds
    
    return result


def extract_h2h_odds(bookmaker_data: Dict, betfair_commission: float = 0.06, for_fair_calc: bool = True) -> Dict[str, float]:
    """
    LEGACY: Old extraction method. Use extract_h2h_odds_for_book() for new code.
    Kept for backward compatibility.
    """
    from .fair_prices import SHARP_BOOKIES
    bkey = bookmaker_data.get("key", "")
    
    if for_fair_calc:
        if bkey in AU_BOOKIES:
            return {}
        if bkey not in SHARP_BOOKIES:
            return {}
    
    markets = bookmaker_data.get("markets", [])
    h2h_market = None
    
    for mkt in markets:
        if mkt.get("key") == "h2h":
            h2h_market = mkt
            break
    
    if not h2h_market:
        return {}
    
    outcomes = h2h_market.get("outcomes", [])
    result = {}
    
    for out in outcomes:
        name = out.get("name", "")
        price = out.get("price")
        
        if not name or price is None:
            continue
        
        if bkey in ["betfair_ex_au", "betfair_ex_uk"]:
            odds = effective_back_odds_betfair(price, betfair_commission)
        else:
            odds = price
        
        result[name] = odds
    
    return result


def process_h2h_event_v2(
    event: Dict,
    home_team: str,
    away_team: str,
    sport: Optional[str] = None,
    betfair_commission: float = 0.06
) -> Dict:
    """
    NEW (v2.0): Process h2h event using book_weights system.
    
    Args:
        event: Event dict from API
        home_team: Home team name
        away_team: Away team name
        sport: Sport code for weight overrides (e.g., "NBA", "NFL")
        betfair_commission: Betfair commission rate
    
    Returns:
        Dict with fair prices and bookmaker odds
    """
    bookmakers = event.get("bookmakers", [])
    
    # Collect sharp bookmaker odds (weight >= 3)
    sharp_odds_home = {}
    sharp_odds_away = {}
    all_book_odds = {}  # For AU books
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        
        # Extract sharp bookmaker odds
        h2h_odds = extract_h2h_odds_for_book(bk, betfair_commission, "main", sport, min_weight=3)
        
        if h2h_odds:
            # Store odds for both outcomes
            if home_team in h2h_odds:
                sharp_odds_home[bkey] = h2h_odds[home_team]
            if away_team in h2h_odds:
                sharp_odds_away[bkey] = h2h_odds[away_team]
        
        # Also extract AU bookmakers for EV comparison
        if bkey in AU_BOOKIES:
            au_odds = extract_h2h_odds_for_book(bk, betfair_commission, "main", sport, min_weight=0)
            if au_odds:
                all_book_odds[bkey] = au_odds
    
    # Require at least 1 sharp bookmaker
    if not sharp_odds_home or not sharp_odds_away:
        return {}
    
    # Devig each sharp bookmaker's odds independently
    devigged_home = {}
    devigged_away = {}
    
    for bkey in sharp_odds_home:
        if bkey in sharp_odds_away:
            home_raw = sharp_odds_home[bkey]
            away_raw = sharp_odds_away[bkey]
            
            # Devig this bookmaker's odds
            p_home, p_away = devig_two_way(home_raw, away_raw)
            
            if p_home > 0:
                devigged_home[bkey] = 1.0 / p_home
            if p_away > 0:
                devigged_away[bkey] = 1.0 / p_away
    
    # Calculate fair prices using weighted median
    fair_prices = build_fair_prices_two_way(devigged_home, devigged_away, "main", sport)
    
    if not fair_prices:
        return {}
    
    # Extract Pinnacle/Betfair for logging
    pin_home = sharp_odds_home.get("pinnacle", 0)
    pin_away = sharp_odds_away.get("pinnacle", 0)
    bf_home = sharp_odds_home.get("betfair_ex_au", sharp_odds_home.get("betfair_ex_eu", 0))
    bf_away = sharp_odds_away.get("betfair_ex_au", sharp_odds_away.get("betfair_ex_eu", 0))
    
    return {
        "fair": {
            "home": fair_prices["A"],
            "away": fair_prices["B"]
        },
        "pinnacle": {
            "home": pin_home,
            "away": pin_away
        },
        "betfair": {
            "home": bf_home,
            "away": bf_away
        },
        "bookmakers": all_book_odds
    }


def process_h2h_event(
    event: Dict,
    home_team: str,
    away_team: str,
    betfair_commission: float = 0.06
) -> Dict:
    """
    LEGACY: Process h2h event using old percentage-based weights.
    Use process_h2h_event_v2() for new code with book_weights system.
    
    Args:
        event: Event dict from API
        home_team: Home team name
        away_team: Away team name
        betfair_commission: Betfair commission rate
    
    Returns:
        Dict with fair prices and bookmaker odds:
        {
            "fair": {"home": fair_home, "away": fair_away},
            "pinnacle": {"home": pin_home, "away": pin_away},
            "betfair": {"home": bf_home, "away": bf_away},
            "bookmakers": {bkey: {"home": odds_home, "away": odds_away}, ...}
        }
    """
    from .fair_prices import SHARP_BOOKIES
    
    bookmakers = event.get("bookmakers", [])
    
    # Extract odds from all sharp bookmakers
    pinnacle_odds = {}
    betfair_odds = {}  # For logging only (not used in fair calc)
    other_sharps_odds = {}  # Dict of bkey -> {home: odds, away: odds}
    all_book_odds = {}
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        
        # Extract for fair calculation (only sharp books, excludes AU books)
        h2h_odds_fair = extract_h2h_odds(bk, betfair_commission, for_fair_calc=True)
        
        if h2h_odds_fair:
            if bkey == "pinnacle":
                pinnacle_odds = h2h_odds_fair
            elif bkey in ["betfair_ex_au", "betfair_ex_eu"]:
                # Extract Betfair for LOGGING only (not used in fair calc)
                betfair_odds = h2h_odds_fair
            else:
                # Other sharp bookmaker (excluding Betfair per user request)
                other_sharps_odds[bkey] = h2h_odds_fair
        
        # Also extract ALL bookmakers (including AU) for EV comparison
        if bkey in AU_BOOKIES:
            h2h_odds_all = extract_h2h_odds(bk, betfair_commission, for_fair_calc=False)
            if h2h_odds_all:
                all_book_odds[bkey] = h2h_odds_all
    
    # REQUIRE Pinnacle - no Pinnacle = no fair price (per user request)
    if not pinnacle_odds:
        return {}
    
    # Get home/away odds from Pinnacle (REQUIRED)
    pin_home = pinnacle_odds.get(home_team)
    pin_away = pinnacle_odds.get(away_team)
    
    if not pin_home or not pin_away:
        return {}
    
    # Collect other sharp books odds for home/away
    other_sharps_home = []
    other_sharps_away = []
    for bkey, odds_dict in other_sharps_odds.items():
        if home_team in odds_dict:
            other_sharps_home.append(odds_dict[home_team])
        if away_team in odds_dict:
            other_sharps_away.append(odds_dict[away_team])
    
    # Calculate fair prices: 75% Pinnacle + 25% other sharps (no Betfair)
    fair_prices = build_fair_prices_simple(
        pin_home, pin_away,
        None, None,  # Betfair not used
        other_sharps_a=other_sharps_home,
        other_sharps_b=other_sharps_away
    )
    
    if not fair_prices:
        return {}
    
    # Extract Betfair odds for logging (not used in fair calc)
    bf_home = betfair_odds.get(home_team, 0)
    bf_away = betfair_odds.get(away_team, 0)
    
    return {
        "fair": {
            "home": fair_prices["A"],
            "away": fair_prices["B"]
        },
        "pinnacle": {
            "home": pin_home or 0,
            "away": pin_away or 0
        },
        "betfair": {
            "home": bf_home or 0,
            "away": bf_away or 0
        },
        "bookmakers": all_book_odds
    }
