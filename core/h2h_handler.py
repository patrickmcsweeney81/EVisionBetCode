"""
Head-to-Head (h2h) market handler - processes moneyline/match winner markets.

KEY RULES:
1. NO AU BOOKMAKERS in fair price calculation (uses Pinnacle, Betfair, and other sharps)
2. Simpler than spreads - no line matching needed
3. Two outcomes: home team win, away team win
"""
from typing import Dict, Optional, List
from .utils import effective_back_odds_betfair
from .fair_prices import build_fair_prices_simple, SHARP_BOOKIES
from .config import AU_BOOKIES


def extract_h2h_odds(bookmaker_data: Dict, betfair_commission: float = 0.06, for_fair_calc: bool = True) -> Dict[str, float]:
    """
    Extract h2h odds from bookmaker data.
    
    Args:
        bookmaker_data: Single bookmaker dict from API
        betfair_commission: Commission for Betfair (default 0.06)
        for_fair_calc: If True, skip AU books and non-sharp books. If False, include all books.
    
    Returns:
        Dict with team names as keys -> odds values
        Empty dict if h2h market not found
    """
    bkey = bookmaker_data.get("key", "")
    
    # For fair calculation: only use sharp bookmakers (NO AU BOOKS!)
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
        
        # Adjust Betfair for commission
        if bkey in ["betfair_ex_au", "betfair_ex_uk"]:
            odds = effective_back_odds_betfair(price, betfair_commission)
        else:
            odds = price
        
        result[name] = odds
    
    return result


def process_h2h_event(
    event: Dict,
    home_team: str,
    away_team: str,
    betfair_commission: float = 0.06
) -> Dict:
    """
    Process single h2h event and calculate fair prices using multiple sharp books.
    
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
