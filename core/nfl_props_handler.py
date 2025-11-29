"""
NFL Player Props Handler - Dedicated handler for NFL/NCAAF player prop markets.

Handles all NFL player prop markets from The Odds API including:
- Passing props (yards, TDs, completions, attempts, interceptions)
- Rushing props (yards, TDs, attempts)
- Receiving props (receptions, yards, TDs)
- Combo props (rush+rec yards, etc.)
- Defense/Special teams (tackles, sacks, kicking)
- Touchdown scorer markets (1st TD, anytime TD, last TD)
- All alternate markets
"""
from typing import Dict, List, Optional, Tuple
from .utils import snap_to_half
from .fair_prices import build_fair_prices_simple
from .config import AU_BOOKIES

# Sharp books for NFL props (US books + Pinnacle)
SHARP_BOOKIES = ["pinnacle", "draftkings", "fanduel", "betmgm"]

LINE_TOLERANCE = 0.25  # Accept lines within 0.25 of target

# All NFL player prop markets (Over/Under)
NFL_OVERUNDER_MARKETS = [
    # Passing
    "player_pass_yds",
    "player_pass_tds", 
    "player_pass_completions",
    "player_pass_attempts",
    "player_pass_interceptions",
    "player_pass_longest_completion",
    # Rushing
    "player_rush_yds",
    "player_rush_tds",
    "player_rush_attempts",
    "player_rush_longest",
    # Receiving
    "player_receptions",
    "player_reception_yds",
    "player_reception_tds",
    "player_reception_longest",
    # Combo stats
    "player_pass_rush_yds",
    "player_rush_reception_yds",
    "player_pass_rush_reception_yds",
    "player_rush_reception_tds",
    "player_pass_rush_reception_tds",
    # Defense/Special teams
    "player_tackles_assists",
    "player_sacks",
    "player_solo_tackles",
    "player_defensive_interceptions",
    "player_kicking_points",
    "player_field_goals",
    "player_pats",
    # Other
    "player_assists",
]

# Alternate markets (same as above with _alternate suffix)
NFL_ALTERNATE_MARKETS = [market + "_alternate" for market in NFL_OVERUNDER_MARKETS]

# Yes/No touchdown markets
NFL_TD_MARKETS = [
    "player_1st_td",
    "player_anytime_td", 
    "player_last_td",
]

# All NFL markets combined
ALL_NFL_MARKETS = NFL_OVERUNDER_MARKETS + NFL_ALTERNATE_MARKETS + NFL_TD_MARKETS


def extract_nfl_prop_odds(
    bookmaker_data: Dict,
    player_name: str,
    market_key: str,
    line: Optional[float] = None,
    include_au: bool = False
) -> Dict[str, float]:
    """
    Extract NFL player prop odds for specific player and line.
    
    Args:
        bookmaker_data: Single bookmaker dict from API
        player_name: Player name (from description field)
        market_key: Market key (e.g., "player_pass_yds")
        line: Target line (e.g., 250.5 yards) - None for Yes/No markets
        include_au: If True, include AU bookmakers. If False, skip them
    
    Returns:
        Dict with outcomes as keys -> odds values
        For Over/Under markets: {"Over": 1.90, "Under": 1.90}
        For Yes/No markets: {"Yes": 3.50, "No": 1.30}
        Empty dict if not found
    """
    bkey = bookmaker_data.get("key", "")
    
    # Skip AU bookmakers for fair price calculation
    if not include_au and bkey in AU_BOOKIES:
        return {}
    
    markets = bookmaker_data.get("markets", [])
    result = {}
    
    for market in markets:
        if market.get("key") != market_key:
            continue
        
        outcomes = market.get("outcomes", [])
        
        for out in outcomes:
            description = out.get("description", "")
            if description != player_name:
                continue
            
            name = out.get("name", "")  # "Over"/"Under" or "Yes"/"No"
            price = out.get("price")
            
            if price is None:
                continue
            
            # For Yes/No markets (TD scorers), no line check needed
            if market_key in NFL_TD_MARKETS:
                result[name] = price
                continue
            
            # For Over/Under markets, check line
            point = out.get("point")
            if point is None:
                continue
            
            if line is not None:
                snapped_point = snap_to_half(float(point))
                if abs(snapped_point - line) > LINE_TOLERANCE:
                    continue
            
            result[name] = price
    
    return result


def process_nfl_props_event(
    event: Dict,
    prop_markets: List[str] = None
) -> List[Dict]:
    """
    Process NFL player props for an event and return list of opportunities.
    
    Args:
        event: Event dict from API
        prop_markets: List of prop market keys to process
    
    Returns:
        List of dicts, each containing:
        {
            "market": "player_pass_yds",
            "player": "Josh Allen",
            "line": 250.5,  # None for Yes/No markets
            "fair": {"over": 2.05, "under": 1.95},  # or {"yes": 3.0, "no": 1.4}
            "pinnacle": {"Over": 2.00, "Under": 2.00},
            "bookmakers": {
                "fanduel": {"Over": 1.90, "Under": 1.95},
                "draftkings": {"Over": 1.91, "Under": 1.94}
            }
        }
    """
    if prop_markets is None:
        prop_markets = NFL_OVERUNDER_MARKETS  # Default to standard markets
    
    bookmakers = event.get("bookmakers", [])
    results = []
    
    # Separate Over/Under markets from Yes/No markets
    overunder_markets = [m for m in prop_markets if m not in NFL_TD_MARKETS]
    yesno_markets = [m for m in prop_markets if m in NFL_TD_MARKETS]
    
    # ========================================================================
    # PROCESS OVER/UNDER MARKETS
    # ========================================================================
    
    # First pass: discover all player+line combinations from sharp books
    player_lines = {}  # {market_key: {player_name: set(lines)}}
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        if bkey not in SHARP_BOOKIES:
            continue
        
        markets = bk.get("markets", [])
        for market in markets:
            market_key = market.get("key", "")
            if market_key not in overunder_markets:
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
                # Extract odds from sharp bookmakers for this player+line
                pinnacle_odds = {}
                sharp_odds_list = []
                
                for bk in bookmakers:
                    bkey = bk.get("key", "")
                    
                    if bkey == "pinnacle":
                        pinnacle_odds = extract_nfl_prop_odds(bk, player_name, market_key, line, include_au=False)
                    
                    if bkey in SHARP_BOOKIES:
                        odds = extract_nfl_prop_odds(bk, player_name, market_key, line, include_au=False)
                        if odds:
                            sharp_odds_list.append(odds)
                
                if not sharp_odds_list:
                    continue
                
                # Calculate fair prices using Pinnacle only (100% weight)
                fair_over = pinnacle_odds.get("Over", 0) if pinnacle_odds else 0
                fair_under = pinnacle_odds.get("Under", 0) if pinnacle_odds else 0
                
                if fair_over <= 0 or fair_under <= 0:
                    continue
                
                # Skip unbalanced/low-liquidity markets (wide Pinnacle spreads)
                # Total implied probability should be ~105% for liquid markets
                # If > 107%, Pinnacle is unsure (trap market)
                total_implied = (1.0 / fair_over + 1.0 / fair_under) * 100
                if total_implied > 107.0:
                    continue  # Skip low-liquidity trap markets
                
                # Collect odds from ALL bookmakers (including AU books)
                all_book_odds = {}
                for bk in bookmakers:
                    bkey = bk.get("key", "")
                    odds = extract_nfl_prop_odds(bk, player_name, market_key, line, include_au=True)
                    if odds:
                        all_book_odds[bkey] = odds
                
                results.append({
                    "market": market_key,
                    "player": player_name,
                    "line": line,
                    "fair": {"over": fair_over, "under": fair_under},
                    "pinnacle": pinnacle_odds,
                    "bookmakers": all_book_odds
                })
    
    # ========================================================================
    # PROCESS YES/NO MARKETS (TD SCORERS)
    # ========================================================================
    
    # First pass: discover all players from sharp books
    player_markets = {}  # {market_key: set(player_names)}
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        if bkey not in SHARP_BOOKIES:
            continue
        
        markets = bk.get("markets", [])
        for market in markets:
            market_key = market.get("key", "")
            if market_key not in yesno_markets:
                continue
            
            if market_key not in player_markets:
                player_markets[market_key] = set()
            
            outcomes = market.get("outcomes", [])
            for out in outcomes:
                player = out.get("description", "")
                if player:
                    player_markets[market_key].add(player)
    
    # Second pass: calculate fair prices for each player
    for market_key, players in player_markets.items():
        for player_name in players:
            # Extract odds from sharp bookmakers for this player
            pinnacle_odds = {}
            sharp_odds_list = []
            
            for bk in bookmakers:
                bkey = bk.get("key", "")
                
                if bkey == "pinnacle":
                    pinnacle_odds = extract_nfl_prop_odds(bk, player_name, market_key, line=None, include_au=False)
                
                if bkey in SHARP_BOOKIES:
                    odds = extract_nfl_prop_odds(bk, player_name, market_key, line=None, include_au=False)
                    if odds:
                        sharp_odds_list.append(odds)
            
            if not sharp_odds_list:
                continue
            
            # Calculate fair prices using Pinnacle only
            fair_yes = pinnacle_odds.get("Yes", 0) if pinnacle_odds else 0
            fair_no = pinnacle_odds.get("No", 0) if pinnacle_odds else 0
            
            if fair_yes <= 0:
                continue  # Yes/No markets must have at least Yes odds
            
            # Collect odds from ALL bookmakers
            all_book_odds = {}
            for bk in bookmakers:
                bkey = bk.get("key", "")
                odds = extract_nfl_prop_odds(bk, player_name, market_key, line=None, include_au=True)
                if odds:
                    all_book_odds[bkey] = odds
            
            results.append({
                "market": market_key,
                "player": player_name,
                "line": None,  # No line for Yes/No markets
                "fair": {"yes": fair_yes, "no": fair_no} if fair_no > 0 else {"yes": fair_yes},
                "pinnacle": pinnacle_odds,
                "bookmakers": all_book_odds
            })
    
    return results
