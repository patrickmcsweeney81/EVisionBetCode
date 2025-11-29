"""
Player props market handler - processes NBA/NFL player prop markets.

KEY RULES:
1. NO AU BOOKMAKERS in fair price calculation (Pinnacle + US books only)
2. Each player+stat+line is treated as independent Over/Under market
3. Group outcomes by player (description field) and line
4. Markets: player_points, player_rebounds, player_assists, player_threes, etc.
"""
from typing import Dict, List, Optional, Tuple
from .utils import snap_to_half, effective_back_odds_betfair
from .fair_prices import build_fair_prices_simple
from .config import AU_BOOKIES

# Sharp books for player props (Pinnacle + major US books)
SHARP_BOOKIES = ["pinnacle", "draftkings", "fanduel", "betmgm"]

LINE_TOLERANCE = 0.25  # Accept lines within 0.25 of target


def extract_player_prop_odds(
    bookmaker_data: Dict, 
    player_name: str, 
    line: float,
    market_key: str,
    betfair_commission: float = 0.06,
    include_au: bool = False
) -> Dict[str, float]:
    """
    Extract player prop odds for specific player, line, and market.
    
    Args:
        bookmaker_data: Single bookmaker dict from API
        player_name: Player name (from description field)
        line: Target line (e.g., 25.5 points)
        market_key: Specific market to extract (e.g., "player_assists", "player_blocks")
        betfair_commission: Commission for Betfair (not typically used for props)
        include_au: If True, include AU bookmakers. If False, skip them
    
    Returns:
        Dict with "Over" and/or "Under" as keys -> odds values
        Empty dict if player/line not found or (AU book and include_au=False)
    """
    bkey = bookmaker_data.get("key", "")
    
    # Skip AU bookmakers ONLY if include_au=False (for fair price calculation)
    if not include_au and bkey in AU_BOOKIES:
        return {}
    
    markets = bookmaker_data.get("markets", [])
    result = {}
    
    # Find the SPECIFIC market only (fixes bug where same player+line on multiple markets returns wrong odds)
    for market in markets:
        mkt_key = market.get("key", "")
        if mkt_key != market_key:
            continue
        
        outcomes = market.get("outcomes", [])
        
        for out in outcomes:
            description = out.get("description", "")
            if description != player_name:
                continue
            
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
            
            # Store odds (no Betfair commission adjustment for props typically)
            result[name] = price
    
    return result


def process_player_props_event(
    event: Dict,
    prop_markets: List[str] = None
) -> List[Dict]:
    """
    Process player props for an event and return list of opportunities.
    
    Args:
        event: Event dict from API
        prop_markets: List of prop market keys to process (e.g., ["player_points", "player_assists"])
    
    Returns:
        List of dicts, each containing:
        {
            "market": "player_points",
            "player": "Stephen Curry",
            "line": 25.5,
            "fair": {"over": fair_over, "under": fair_under},
            "pinnacle": {"Over": pin_over, "Under": pin_under},
            "bookmakers": {bkey: {"Over": odds_over, "Under": odds_under}, ...}
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
    
    # First pass: discover all player+line combinations from sharp books
    player_lines = {}  # {market_key: {player_name: [lines]}}
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        if bkey not in SHARP_BOOKIES:
            continue
        
        markets = bk.get("markets", [])
        for market in markets:
            market_key = market.get("key", "")
            if market_key not in prop_markets:
                continue
            
            if market_key not in player_lines:
                player_lines[market_key] = {}
            
            outcomes = market.get("outcomes", [])
            for out in outcomes:
                player = out.get("description", "")
                point = out.get("point")
                
                if not player or point is None:
                    continue
                
                snapped_point = snap_to_half(float(point))
                
                if player not in player_lines[market_key]:
                    player_lines[market_key][player] = set()
                player_lines[market_key][player].add(snapped_point)
    
    # Second pass: calculate fair prices for each player+line combination
    for market_key, players in player_lines.items():
        for player_name, lines in players.items():
            for line in lines:
                # Extract odds from all bookmakers for this player+line
                pinnacle_odds = {}
                all_book_odds = {}
                
                for bk in bookmakers:
                    bkey = bk.get("key", "")
                    
                    if bkey == "pinnacle":
                        prop_odds = extract_player_prop_odds(bk, player_name, line, market_key, include_au=False)
                        if prop_odds:
                            pinnacle_odds = prop_odds
                    elif bkey in SHARP_BOOKIES:
                        prop_odds = extract_player_prop_odds(bk, player_name, line, market_key, include_au=False)
                        if prop_odds:
                            all_book_odds[bkey] = prop_odds
                    elif bkey in AU_BOOKIES:
                        # Extract AU books for EV comparison
                        prop_odds = extract_player_prop_odds(bk, player_name, line, market_key, include_au=True)
                        if prop_odds:
                            # Debug: Check for suspicious odds (same price on different markets)
                            over_odds = prop_odds.get("Over", 0)
                            under_odds = prop_odds.get("Under", 0)
                            if over_odds > 3.0 or under_odds > 3.0:
                                # Log suspicious high odds for debugging
                                pass  # Keeping code clean, filter will catch at EV calculation
                            all_book_odds[bkey] = prop_odds
                
                if not pinnacle_odds:
                    continue  # No Pinnacle, no fair price
                
                if len(pinnacle_odds) != 2:
                    continue  # Need both Over and Under
                
                pin_over = pinnacle_odds.get("Over", 0)
                pin_under = pinnacle_odds.get("Under", 0)
                
                if pin_over <= 0 or pin_under <= 0:
                    continue
                
                # Skip unbalanced/low-liquidity markets (wide Pinnacle spreads)
                # Calculate total implied probability - should be ~105% for liquid markets
                # If > 107%, Pinnacle is unsure (trap market for bench players, injuries, etc.)
                total_implied = (1.0 / pin_over + 1.0 / pin_under) * 100
                if total_implied > 107.0:
                    # print(f"[SKIP] {player_name} {market_key} {line} - Low liquidity ({total_implied:.1f}%)")
                    continue  # Skip low-liquidity trap markets
                
                # For player props, use Pinnacle only as fair price (US books can be soft)
                # Could add other sharp books if available, but Pinnacle is most reliable
                fair_prices = build_fair_prices_simple(
                    pin_over, pin_under,
                    None, None,  # No Betfair for props typically
                    weight_pinnacle=1.0,
                    weight_betfair=0.0
                )
                
                if not fair_prices:
                    continue
                
                results.append({
                    "market": market_key,
                    "player": player_name,
                    "line": line,
                    "fair": {
                        "over": fair_prices["A"],
                        "under": fair_prices["B"]
                    },
                    "pinnacle": {
                        "Over": pin_over,
                        "Under": pin_under
                    },
                    "bookmakers": all_book_odds
                })
    
    return results
