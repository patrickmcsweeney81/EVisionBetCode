"""
Display all available lines for player props in a table format.
Similar to how Sportsbet shows 15+, 20+, 25+, 30+, 40+ with odds for each line.
"""
import json
from typing import Dict, List, Tuple
from collections import defaultdict

def extract_all_player_lines(event: Dict, market_key: str) -> Dict[str, Dict[float, Dict[str, float]]]:
    """
    Extract ALL lines available for each player in a given market.
    
    Args:
        event: Event dict from API with bookmakers data
        market_key: Market to extract (e.g., "player_pass_yds")
    
    Returns:
        {
            "Player Name": {
                line_value: {
                    "bookmaker_key": {"Over": odds, "Under": odds}
                }
            }
        }
        
    Example:
        {
            "Josh Allen": {
                250.5: {
                    "pinnacle": {"Over": 1.95, "Under": 1.95},
                    "fanduel": {"Over": 1.91, "Under": 1.99}
                },
                275.5: {
                    "pinnacle": {"Over": 2.20, "Under": 1.75}
                }
            }
        }
    """
    player_data = defaultdict(lambda: defaultdict(dict))
    
    bookmakers = event.get("bookmakers", [])
    
    for bk in bookmakers:
        bkey = bk.get("key", "")
        markets = bk.get("markets", [])
        
        for market in markets:
            if market.get("key") != market_key:
                continue
            
            outcomes = market.get("outcomes", [])
            
            # Group outcomes by player and line
            for out in outcomes:
                player_name = out.get("description", "")
                outcome_type = out.get("name", "")  # "Over" or "Under"
                line = out.get("point")
                price = out.get("price")
                
                if not all([player_name, outcome_type, line is not None, price]):
                    continue
                
                line = float(line)
                
                # Initialize bookmaker dict if not exists
                if bkey not in player_data[player_name][line]:
                    player_data[player_name][line][bkey] = {}
                
                player_data[player_name][line][bkey][outcome_type] = price
    
    # Convert defaultdict to regular dict for cleaner output
    return {
        player: {
            line: dict(books) 
            for line, books in lines.items()
        }
        for player, lines in player_data.items()
    }


def display_player_lines_table(
    player_name: str,
    lines_data: Dict[float, Dict[str, Dict[str, float]]],
    bookmaker: str = "pinnacle"
):
    """
    Display all lines for a player in a table format like Sportsbet.
    
    Args:
        player_name: Name of the player
        lines_data: Dict of {line: {bookmaker: {Over: odds, Under: odds}}}
        bookmaker: Which bookmaker's odds to display
    """
    print(f"\n{'='*80}")
    print(f"{player_name} - All Available Lines ({bookmaker})")
    print(f"{'='*80}")
    
    # Sort lines ascending
    sorted_lines = sorted(lines_data.keys())
    
    if not sorted_lines:
        print("No lines available")
        return
    
    # Header
    print(f"{'Line':<10} {'Over':<10} {'Under':<10}")
    print(f"{'-'*30}")
    
    # Data rows
    for line in sorted_lines:
        books = lines_data[line]
        
        if bookmaker not in books:
            continue
        
        odds = books[bookmaker]
        over_odds = odds.get("Over", "N/A")
        under_odds = odds.get("Under", "N/A")
        
        # Format line as integer if whole number, otherwise with decimal
        line_str = f"{int(line)}" if line == int(line) else f"{line:.1f}"
        
        # Format odds
        over_str = f"{over_odds:.2f}" if isinstance(over_odds, float) else over_odds
        under_str = f"{under_odds:.2f}" if isinstance(under_odds, float) else under_odds
        
        print(f"{line_str+'+':<10} {over_str:<10} {under_str:<10}")


def display_all_bookmakers_comparison(
    player_name: str,
    line: float,
    lines_data: Dict[float, Dict[str, Dict[str, float]]]
):
    """
    Show all bookmakers' odds for a specific line (for comparison).
    
    Args:
        player_name: Name of the player
        line: Specific line to compare
        lines_data: Dict of {line: {bookmaker: {Over: odds, Under: odds}}}
    """
    print(f"\n{'='*80}")
    print(f"{player_name} - O/U {line} - All Bookmakers")
    print(f"{'='*80}")
    
    if line not in lines_data:
        print(f"Line {line} not found")
        return
    
    books = lines_data[line]
    
    # Header
    print(f"{'Bookmaker':<20} {'Over':<10} {'Under':<10}")
    print(f"{'-'*40}")
    
    # Sort bookmakers by Over odds (descending)
    sorted_books = sorted(
        books.items(),
        key=lambda x: x[1].get("Over", 0),
        reverse=True
    )
    
    for bkey, odds in sorted_books:
        over_odds = odds.get("Over", "N/A")
        under_odds = odds.get("Under", "N/A")
        
        over_str = f"{over_odds:.2f}" if isinstance(over_odds, float) else over_odds
        under_str = f"{under_odds:.2f}" if isinstance(under_odds, float) else under_odds
        
        print(f"{bkey:<20} {over_str:<10} {under_str:<10}")


def find_best_lines(lines_data: Dict[float, Dict[str, Dict[str, float]]]) -> Tuple[float, str, float, str]:
    """
    Find best Over and Under odds across all lines and bookmakers.
    
    Returns:
        (best_over_line, best_over_bookie, best_under_line, best_under_bookie)
    """
    best_over = (None, None, 0)  # (line, bookie, odds)
    best_under = (None, None, 0)
    
    for line, books in lines_data.items():
        for bkey, odds in books.items():
            over = odds.get("Over", 0)
            under = odds.get("Under", 0)
            
            if over > best_over[2]:
                best_over = (line, bkey, over)
            
            if under > best_under[2]:
                best_under = (line, bkey, under)
    
    return best_over, best_under


if __name__ == "__main__":
    # Example: Load event data and display
    import requests
    from core.config import load_env
    
    config = load_env()
    api_key = config.get("ODDS_API_KEY")
    
    # Get NFL events
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "h2h"
    }
    
    response = requests.get(url, params=params)
    events = response.json()
    
    if events:
        event = events[0]  # First event
        event_id = event["id"]
        
        # Get player props for this event
        props_url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events/{event_id}/odds"
        props_params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": "player_pass_yds,player_rush_yds,player_receptions"
        }
        
        props_response = requests.get(props_url, params=props_params)
        props_event = props_response.json()
        
        # Extract pass yards data
        pass_yds_data = extract_all_player_lines(props_event, "player_pass_yds")
        
        # Display for each player
        for player_name, lines_data in pass_yds_data.items():
            display_player_lines_table(player_name, lines_data, "pinnacle")
            
            # Show best lines
            best_over, best_under = find_best_lines(lines_data)
            print(f"\nBest Over: {best_over[0]:+} @ {best_over[1]} ({best_over[2]:.2f})")
            print(f"Best Under: {best_under[0]:+} @ {best_under[1]} ({best_under[2]:.2f})")
