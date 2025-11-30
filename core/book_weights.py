"""
Bookmaker Weighting System for Fair Price Calculation.

This module provides a flexible weighting system for bookmakers that:
- Treats sharp books as anchors for fair price
- Differentiates between main markets (H2H, spreads, totals) and player props
- Allows sport-specific overrides (MMA, NBA, NFL)
- Provides a single helper function for weight lookup

Weight Scale (0-4):
    4 = Primary sharp anchor (Pinnacle, Circa, CRIS, etc.)
    3 = Strong market-setter (BetOnline, DK/FD in some contexts)
    2 = Decent, moves with market but not leading
    1 = Follower / soft rec book (Bovada, Kambi clones)
    0 = Ignore / don't use in fair price

ANOMALY ANALYSIS vs. Current Setup:
====================================
The existing ev_arb_bot.py and core/config.py use different approaches:

1. ev_arb_bot.py: Uses percentage weights (Pinnacle 70%, Betfair 20%, Sharps 10%)
   SHARP_BOOKIES = ['pinnacle', 'betfair_ex_au', 'matchbook']
   
2. core/config.py: Uses a broader sharp list with Pinnacle 75%, Betfair 0%, Sharps 25%
   Includes: draftkings, fanduel, betmgm, betonlineag, bovada, etc.

Key Differences from this module:
---------------------------------
- Betfair exchanges are weight 3 here (strong) vs. being a dedicated 20% weight
  in ev_arb_bot.py. This reflects that Betfair is a strong price source.
  
- Bovada, BetUS, MyBookie are weight 1 (soft/follower) here, but are listed
  in core/config.py SHARP_BOOKIES. This is INTENTIONAL - those books are
  recreational and should not heavily influence fair price.
  
- DraftKings/FanDuel are weight 3-4 here (especially 4 for props) which
  differs from ev_arb_bot.py's minimal list. This reflects their excellent
  prop markets.
  
- This module adds Circa and Bookmaker/CRIS as tier-1 sharps (weight 4),
  which are not currently used in the codebase but are industry-recognized
  sharp books.

Integration Note:
-----------------
This 0-4 scale system can work alongside or replace the existing percentage-based
weighting. The get_book_weight() function provides a single entry point for
looking up weights, which can be converted to percentages as needed.
"""
from typing import Optional, Dict


# =============================================================================
# BOOKMAKER CODE -> DISPLAY NAME MAPPING
# =============================================================================
BOOK_DISPLAY_NAMES: Dict[str, str] = {
    "pinnacle": "Pinnacle",
    "circa": "Circa Sports",
    "betonline": "BetOnline",
    "betonlineag": "BetOnline",  # API alias
    "bookmaker": "Bookmaker/CRIS",
    "heritage": "Heritage Sports",
    "draftkings": "DraftKings",
    "fanduel": "FanDuel",
    "bet365": "Bet365",
    "bet365_au": "Bet365 AU",
    "caesars": "Caesars",
    "betmgm": "BetMGM",
    "pointsbet": "PointsBet",
    "pointsbetau": "PointsBet AU",
    "espnbet": "ESPN Bet",
    "bovada": "Bovada",
    "betrivers": "BetRivers",
    "unibet": "Unibet",
    "matchbook": "Matchbook",
    "betfair_ex_au": "Betfair AU",
    "betfair_ex_eu": "Betfair EU",
    "lowvig": "LowVig",
    "mybookieag": "MyBookie",
    "betus": "BetUS",
    "marathonbet": "Marathonbet",
    "williamhill_us": "William Hill US",
}


# =============================================================================
# MAIN MARKET WEIGHTS (H2H, Spreads, Totals)
# =============================================================================
# Tier 1 sharps (4-3): Pinnacle, Circa, Bookmaker/CRIS, BetOnline, Heritage
# Tier 2 movers (3-2): DraftKings, FanDuel, Bet365
# Tier 3 followers (2-1): Caesars, BetMGM, PointsBet, ESPNBet
# Soft recs (1): Bovada, BetRivers, Unibet

MAIN_MARKET_WEIGHTS: Dict[str, int] = {
    # Tier 1: Primary sharp anchors (weight 4)
    "pinnacle": 4,
    "circa": 4,
    "bookmaker": 4,  # CRIS
    
    # Tier 1-2: Strong sharps (weight 3)
    "betonline": 3,
    "betonlineag": 3,  # API alias for betonline
    "heritage": 3,
    "matchbook": 3,  # Exchange, good liquidity
    "lowvig": 3,
    
    # Tier 2: Market movers (weight 3-2)
    "draftkings": 3,
    "fanduel": 3,
    "bet365": 2,
    "bet365_au": 2,
    
    # Tier 3: Followers (weight 2-1)
    "caesars": 2,
    "betmgm": 2,
    "pointsbet": 2,
    "pointsbetau": 2,
    "espnbet": 2,
    "williamhill_us": 2,
    
    # Soft recreational books (weight 1)
    "bovada": 1,
    "betrivers": 1,
    "unibet": 1,
    "mybookieag": 1,
    "betus": 1,
    "marathonbet": 1,
    
    # Betfair exchanges - weight 3 (strong due to deep liquidity, commission adjusted)
    # Note: Current ev_arb_bot.py gives Betfair 20% dedicated weight
    "betfair_ex_au": 3,
    "betfair_ex_eu": 3,
}


# =============================================================================
# PLAYER PROP WEIGHTS
# =============================================================================
# Player props rely heavily on:
# - Pinnacle (still sharp for props)
# - DraftKings (excellent prop markets)
# - FanDuel (excellent prop markets)
# Then BetOnline, Circa, Bookmaker as secondary
# Bet365, Caesars, BetMGM, ESPNBet relevant but lower
# Followers (Bovada, BetRivers, Unibet, PointsBet) as low weight

PLAYER_PROP_WEIGHTS: Dict[str, int] = {
    # Tier 1: Top prop sources (weight 4)
    "pinnacle": 4,
    "draftkings": 4,  # Excellent prop markets
    "fanduel": 4,     # Excellent prop markets
    
    # Tier 2: Strong prop sources (weight 3)
    "betonline": 3,
    "betonlineag": 3,
    "circa": 3,
    "bookmaker": 3,
    "betmgm": 3,  # Strong on player props
    
    # Tier 3: Decent prop sources (weight 2)
    "bet365": 2,
    "bet365_au": 2,
    "caesars": 2,
    "espnbet": 2,
    "heritage": 2,
    "lowvig": 2,
    "matchbook": 2,
    "williamhill_us": 2,
    
    # Tier 4: Followers (weight 1)
    "bovada": 1,
    "betrivers": 1,
    "unibet": 1,
    "pointsbet": 1,
    "pointsbetau": 1,
    "mybookieag": 1,
    "betus": 1,
    "marathonbet": 1,
    
    # Betfair exchanges (weight 1 for props - less liquid)
    "betfair_ex_au": 1,
    "betfair_ex_eu": 1,
}


# =============================================================================
# SPORT-SPECIFIC OVERRIDES
# =============================================================================
# Structure: { "SPORT_CODE": {"main": {...}, "props": {...}} }
# Only include overrides where weights differ from defaults
# If a book isn't in the override, fall back to global weights

SPORT_OVERRIDES: Dict[str, Dict[str, Dict[str, int]]] = {
    # MMA (UFC, etc.)
    # Main markets: Pinnacle, BetOnline, Circa, Bookmaker all very high
    # Regulated US books are secondary
    # Props: Treat MMA props almost like main lines (lower liquidity, same sharps)
    "MMA": {
        "main": {
            "pinnacle": 4,
            "betonline": 4,
            "betonlineag": 4,
            "circa": 4,
            "bookmaker": 4,
            "heritage": 3,
            "bovada": 2,  # Better for MMA than other sports
            "mybookieag": 2,
            "draftkings": 2,
            "fanduel": 2,
            "bet365": 2,
            "bet365_au": 2,
            "betmgm": 2,
            "caesars": 1,
            "pointsbet": 1,
            "pointsbetau": 1,
            "betrivers": 1,
            "unibet": 1,
        },
        "props": {
            # MMA props follow main market sharps (lower liquidity)
            "pinnacle": 4,
            "betonline": 4,
            "betonlineag": 4,
            "circa": 3,
            "bookmaker": 3,
            "draftkings": 3,
            "fanduel": 3,
            "bovada": 2,
            "bet365": 2,
            "bet365_au": 2,
            "betmgm": 2,
            "caesars": 1,
            "heritage": 2,
        },
    },
    
    # NBA Basketball
    # Props are heavily DK/FD driven
    # Main markets can use global MAIN_MARKET_WEIGHTS
    "NBA": {
        "props": {
            # NBA player props are very DK/FD-driven
            "pinnacle": 4,
            "draftkings": 4,
            "fanduel": 4,
            "betonline": 3,
            "betonlineag": 3,
            "circa": 3,
            "bookmaker": 3,
            "bet365": 3,  # Strong for NBA props
            "bet365_au": 3,
            "betmgm": 3,
            "caesars": 2,
            "espnbet": 2,
            "bovada": 1,
            "betrivers": 1,
            "unibet": 1,
            "pointsbet": 1,
            "pointsbetau": 1,
        },
    },
    
    # NFL American Football
    # Similar to NBA: Pinnacle, DK, FD as top
    # BetOnline / Circa / Bookmaker strong
    # Bet365 / Caesars / MGM / ESPN mid
    # Followers low
    "NFL": {
        "props": {
            "pinnacle": 4,
            "draftkings": 4,
            "fanduel": 4,
            "betonline": 3,
            "betonlineag": 3,
            "circa": 3,
            "bookmaker": 3,
            "bet365": 2,
            "bet365_au": 2,
            "caesars": 2,
            "betmgm": 2,
            "espnbet": 2,
            "bovada": 1,
            "betrivers": 1,
            "unibet": 1,
            "pointsbet": 1,
            "pointsbetau": 1,
        },
    },
    
    # NHL Ice Hockey
    # Similar structure to NBA/NFL
    "NHL": {
        "props": {
            "pinnacle": 4,
            "draftkings": 4,
            "fanduel": 4,
            "betonline": 3,
            "betonlineag": 3,
            "bet365": 3,
            "bet365_au": 3,
            "betmgm": 2,
            "caesars": 2,
            "bovada": 1,
            "betrivers": 1,
            "unibet": 1,
        },
    },
    
    # MLB Baseball
    "MLB": {
        "props": {
            "pinnacle": 4,
            "draftkings": 4,
            "fanduel": 4,
            "betonline": 3,
            "betonlineag": 3,
            "bet365": 2,
            "bet365_au": 2,
            "betmgm": 2,
            "caesars": 2,
            "bovada": 1,
            "betrivers": 1,
        },
    },
}


def get_book_weight(
    book_code: str,
    market_type: str,
    sport: Optional[str] = None
) -> int:
    """
    Get the weight for a bookmaker given the market type and optional sport.
    
    Args:
        book_code: The OddsAPI bookmaker code (e.g., "pinnacle", "draftkings")
        market_type: Market type - one of:
            - "main" for H2H/Spread/Total
            - "props" for player props
            - "h2h", "spread", "total" (all treated as "main")
        sport: Optional uppercase sport code (e.g., "NBA", "NFL", "MMA")
    
    Returns:
        Weight from 0-4. Returns 0 if bookmaker not found (ignore in fair price).
    
    Examples:
        >>> get_book_weight("pinnacle", "main")
        4
        >>> get_book_weight("draftkings", "props", "NBA")
        4
        >>> get_book_weight("unknown_book", "main")
        0
    """
    # Normalize inputs
    book_code = (book_code or "").lower().strip()
    market_type = (market_type or "").lower().strip()
    
    # Treat h2h, spread, total as "main"
    if market_type in ("h2h", "spread", "spreads", "total", "totals", "moneyline"):
        market_type = "main"
    elif market_type not in ("main", "props"):
        # Unknown market type, default to main
        market_type = "main"
    
    # Normalize sport code if provided
    if sport:
        sport = sport.upper().strip()
        # Handle common variations
        sport_map = {
            "BASKETBALL_NBA": "NBA",
            "AMERICANFOOTBALL_NFL": "NFL",
            "ICEHOCKEY_NHL": "NHL",
            "BASEBALL_MLB": "MLB",
            "UFC": "MMA",
            "MIXED_MARTIAL_ARTS": "MMA",
        }
        sport = sport_map.get(sport, sport)
    
    # Step 1: Check sport-specific overrides
    if sport and sport in SPORT_OVERRIDES:
        sport_override = SPORT_OVERRIDES[sport]
        
        if market_type == "props" and "props" in sport_override:
            if book_code in sport_override["props"]:
                return sport_override["props"][book_code]
        
        if market_type == "main" and "main" in sport_override:
            if book_code in sport_override["main"]:
                return sport_override["main"][book_code]
    
    # Step 2: Fall back to global weights
    if market_type == "props":
        return PLAYER_PROP_WEIGHTS.get(book_code, 0)
    else:  # main
        return MAIN_MARKET_WEIGHTS.get(book_code, 0)


def get_book_display_name(book_code: str) -> str:
    """
    Get human-friendly display name for a bookmaker code.
    
    Args:
        book_code: The OddsAPI bookmaker code
    
    Returns:
        Human-friendly name, or formatted code if not in lookup table
    """
    if not book_code:
        return ""
    book_code = book_code.lower().strip()
    # Return from lookup table if available
    if book_code in BOOK_DISPLAY_NAMES:
        return BOOK_DISPLAY_NAMES[book_code]
    # Fallback: format the code for display (replace underscores, title case)
    # This handles unknown codes gracefully
    return book_code.replace("_", " ").title()


def list_books_by_weight(
    market_type: str = "main",
    sport: Optional[str] = None,
    min_weight: int = 1
) -> Dict[str, int]:
    """
    Get all bookmakers with weight >= min_weight for a given market/sport.
    
    Args:
        market_type: "main" or "props"
        sport: Optional sport code for sport-specific weights
        min_weight: Minimum weight to include (default 1, excludes 0)
    
    Returns:
        Dict of {book_code: weight} sorted by weight descending
    """
    # Start with a COPY of global weights to avoid modifying originals
    if market_type == "props":
        base_weights = dict(PLAYER_PROP_WEIGHTS)  # Explicit copy
    else:
        base_weights = dict(MAIN_MARKET_WEIGHTS)  # Explicit copy
    
    # Apply sport overrides if specified (modifies our local copy only)
    if sport:
        sport = sport.upper().strip()
        if sport in SPORT_OVERRIDES:
            override = SPORT_OVERRIDES[sport]
            key = "props" if market_type == "props" else "main"
            if key in override:
                base_weights.update(override[key])
    
    # Filter by minimum weight and sort
    filtered = {k: v for k, v in base_weights.items() if v >= min_weight}
    return dict(sorted(filtered.items(), key=lambda x: (-x[1], x[0])))
