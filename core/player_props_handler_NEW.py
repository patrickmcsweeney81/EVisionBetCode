"""
REBUILT Player Props Handler - Clean implementation from scratch

Core principle: Extract ONLY the specific market's odds for each bookmaker
No cross-market contamination, no mixed data
"""
from typing import Dict, List
from .utils import snap_to_half
from .fair_prices import build_fair_prices_two_way
from .utils import devig_two_way
from .config import AU_BOOKIES

SHARP_BOOKIES = ["pinnacle", "draftkings", "fanduel", "betmgm"]
LINE_TOLERANCE = 0.25


def get_bookmaker_odds_for_market(
    bookmaker: Dict,
    market_key: str,
    player_name: str,
    line: float
) -> Dict[str, float]:
    """
    Extract Over/Under odds for ONE specific market from ONE bookmaker.
    
    Returns: {"Over": 1.90, "Under": 1.95} or {} if not found
    """
    bk_key = bookmaker.get("key", "")
    markets = bookmaker.get("markets", [])
    
    # Find the exact market
    for market in markets:
        if market.get("key") != market_key:
            continue
        
        # Found the market - now find the player
        outcomes = market.get("outcomes", [])
        result = {}
        
        for outcome in outcomes:
            if outcome.get("description") != player_name:
                continue
            
            point = outcome.get("point")
            if point is None:
                continue
            
            # Check if line matches
            snapped = snap_to_half(float(point))
            if abs(snapped - line) > LINE_TOLERANCE:
                continue
            
            # Store the odds
            side = outcome.get("name", "")  # "Over" or "Under"
            price = outcome.get("price")
            
            if side and price:
                result[side] = price
        
        # Return what we found for this market
        return result
    
    return {}


def find_all_player_lines(event: Dict, prop_markets: List[str]) -> Dict:
    """
    Scan Pinnacle to find all player+line combinations.
    
    Returns: {market_key: {player_name: [line1, line2, ...]}}
    """
    player_lines = {}
    bookmakers = event.get("bookmakers", [])
    
    # Find Pinnacle only
    pinnacle = None
    for bk in bookmakers:
        if bk.get("key") == "pinnacle":
            pinnacle = bk
            break
    
    if not pinnacle:
        return {}
    
    # Scan Pinnacle's markets
    markets = pinnacle.get("markets", [])
    for market in markets:
        market_key = market.get("key", "")
        if market_key not in prop_markets:
            continue
        
        if market_key not in player_lines:
            player_lines[market_key] = {}
        
        outcomes = market.get("outcomes", [])
        for outcome in outcomes:
            player = outcome.get("description", "")
            point = outcome.get("point")
            
            if not player or point is None:
                continue
            
            snapped = snap_to_half(float(point))
            
            if player not in player_lines[market_key]:
                player_lines[market_key][player] = []
            
            if snapped not in player_lines[market_key][player]:
                player_lines[market_key][player].append(snapped)
    
    return player_lines


def process_player_props_event(event: Dict, prop_markets: List[str] = None) -> List[Dict]:
    """
    Process player props - returns clean data structure.
    
    Returns list of:
    {
        "market": "player_points",
        "player": "LeBron James",
        "line": 25.5,
        "pinnacle": {"Over": 1.90, "Under": 1.95},
        "fair_over": 1.92,
        "fair_under": 1.93,
        "bookmakers": {
            "sportsbet": {"Over": 2.00, "Under": 1.85},
            "tab": {"Over": 1.95, "Under": 1.90},
            ...
        }
    }
    """
    if prop_markets is None:
        prop_markets = [
            "player_points", "player_rebounds", "player_assists", "player_threes",
            "player_blocks", "player_steals", "player_turnovers",
            "player_points_rebounds_assists", "player_points_assists",
            "player_points_rebounds", "player_assists_rebounds",
            "player_double_double", "player_first_basket"
        ]
    
    bookmakers = event.get("bookmakers", [])
    results = []
    
    # Step 1: Find all player+line combinations from Pinnacle
    player_lines = find_all_player_lines(event, prop_markets)
    
    # Step 2: For each player+line, extract odds from all bookmakers
    for market_key, players in player_lines.items():
        for player_name, lines in players.items():
            for line in lines:
                
                # Get Pinnacle odds for fair price
                pinnacle_odds = None
                for bk in bookmakers:
                    if bk.get("key") == "pinnacle":
                        pinnacle_odds = get_bookmaker_odds_for_market(bk, market_key, player_name, line)
                        break
                
                if not pinnacle_odds or len(pinnacle_odds) != 2:
                    continue
                
                pin_over = pinnacle_odds.get("Over", 0)
                pin_under = pinnacle_odds.get("Under", 0)
                
                if pin_over <= 0 or pin_under <= 0:
                    continue
                
                # Liquidity check
                total_implied = (1.0 / pin_over + 1.0 / pin_under) * 100
                if total_implied > 107.0:
                    continue
                
                # Build devigged odds dictionaries across sharp books (including Pinnacle)
                bookmaker_odds_over: Dict[str, float] = {}
                bookmaker_odds_under: Dict[str, float] = {}

                for bk in bookmakers:
                    bk_key = bk.get("key", "")
                    if bk_key not in SHARP_BOOKIES:
                        continue
                    bk_odds = get_bookmaker_odds_for_market(bk, market_key, player_name, line)
                    over_o = bk_odds.get("Over") if bk_odds else None
                    under_o = bk_odds.get("Under") if bk_odds else None
                    if over_o and under_o and over_o > 0 and under_o > 0:
                        p_over_prob, p_under_prob = devig_two_way(over_o, under_o)
                        if p_over_prob > 0 and p_under_prob > 0:
                            bookmaker_odds_over[bk_key] = 1.0 / p_over_prob
                            bookmaker_odds_under[bk_key] = 1.0 / p_under_prob

                fair_prices_v2 = build_fair_prices_two_way(
                    bookmaker_odds_over,
                    bookmaker_odds_under,
                    market_type="props",
                    sport=event.get("sport_key")
                )

                if not fair_prices_v2:
                    continue
                
                # Get odds from all other bookmakers
                all_bookmaker_odds = {}
                
                for bk in bookmakers:
                    bk_key = bk.get("key", "")
                    
                    # Skip Pinnacle (already have it)
                    if bk_key == "pinnacle":
                        continue
                    
                    # Skip non-AU books unless they're sharp books
                    if bk_key not in AU_BOOKIES and bk_key not in SHARP_BOOKIES:
                        continue
                    
                    bk_odds = get_bookmaker_odds_for_market(bk, market_key, player_name, line)
                    if bk_odds:
                        all_bookmaker_odds[bk_key] = bk_odds
                
                # Build result
                results.append({
                    "market": market_key,
                    "player": player_name,
                    "line": line,
                    "pinnacle": pinnacle_odds,
                    "fair_over": fair_prices_v2["A"],
                    "fair_under": fair_prices_v2["B"],
                    "bookmakers": all_bookmaker_odds
                })
    
    return results
