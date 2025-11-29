"""
Raw odds extractor - logs ALL bookmaker odds to all_odds_analysis.csv
This captures every opportunity WITH fair prices, EV%, and Prob calculated.
"""
from pathlib import Path
from typing import Dict, List, Optional
from statistics import median
from datetime import datetime, timezone, timedelta
from core.logging import log_all_odds
from core.utils import kelly_stake


def calculate_fair_odds(
    pinnacle_odds: Optional[float],
    betfair_odds: Optional[float],
    other_sharps_odds: List[float],
    weight_pinnacle: float = 0.6,
    weight_betfair: float = 0.25,
    weight_sharps: float = 0.15,
    betfair_commission: float = 0.06
) -> float:
    """
    Calculate fair odds using weighted sharp bookmaker prices.
    
    Args:
        pinnacle_odds: Pinnacle odds (or None)
        betfair_odds: Betfair raw odds (will be adjusted for commission)
        other_sharps_odds: List of other sharp book odds
        weight_pinnacle: Weight for Pinnacle (default 60%)
        weight_betfair: Weight for Betfair (default 25%)
        weight_sharps: Weight for other sharps (default 15%)
        betfair_commission: Betfair commission (default 6%)
    
    Returns:
        Fair odds (or 0.0 if no valid inputs)
    """
    components = []
    
    # Pinnacle
    if pinnacle_odds and pinnacle_odds > 1.0:
        components.append((pinnacle_odds, weight_pinnacle))
    
    # Betfair (adjust for commission)
    if betfair_odds and betfair_odds > 1.0:
        betfair_adjusted = 1 + (betfair_odds - 1) * (1 - betfair_commission)
        components.append((betfair_adjusted, weight_betfair))
    
    # Other sharps (median if 2+)
    if other_sharps_odds and len(other_sharps_odds) >= 2:
        valid_sharps = [o for o in other_sharps_odds if o > 1.0]
        if valid_sharps:
            median_odds = median(valid_sharps)
            components.append((median_odds, weight_sharps))
    
    if not components:
        return 0.0
    
    # Normalize weights
    w_sum = sum(w for _, w in components)
    if w_sum <= 0:
        return 0.0
    
    # Weighted probability average
    p_star = 0.0
    for odds_i, w_i in components:
        if odds_i <= 1.0:
            continue
        p_i = 1.0 / odds_i
        p_star += p_i * (w_i / w_sum)
    
    return (1.0 / p_star) if p_star > 0 else 0.0


def american_to_decimal(american_odds: float, market_key: str = "", bookmaker_key: str = "") -> float:
    """
    Convert American odds to decimal odds.
    American odds: +150, -110, +5000, +34, etc.
    Decimal odds: 2.50, 1.91, 51.00, 1.34, etc.
    
    If odds >= 100, it's positive American (+150 = 2.50)
    If odds <= -100, it's negative American (-110 = 1.91)
    If odds is between 10 and 99, it's likely American for player props (+34 = 1.34)
    If odds is between 1.01 and 9.99, it's already decimal
    """
    # US bookmakers and player prop markets often return American odds
    is_likely_american = market_key.startswith("player_") or bookmaker_key in [
        "draftkings", "fanduel", "betmgm", "betonlineag", "bovada", 
        "williamhill_us", "pointsbetau", "fanatics"
    ]
    
    if american_odds >= 100:
        # Positive American odds: +150 becomes 2.50
        return (american_odds / 100.0) + 1.0
    elif american_odds <= -100:
        # Negative American odds: -110 becomes 1.91
        return (100.0 / abs(american_odds)) + 1.0
    elif american_odds >= 10 and is_likely_american:
        # For player props, odds like 34, 50 are American (+3400 = 35.00, +5000 = 51.00)
        return (american_odds / 100.0) + 1.0
    else:
        # Already decimal odds (1.01 to 9.99, or non-prop markets)
        return american_odds


def log_raw_event_odds(
    event: Dict,
    all_odds_csv: Path,
    au_bookies: List[str],
    bankroll: float = 1000,
    kelly_fraction: float = 0.25,
    betfair_commission: float = 0.06
):
    """
    Extract and log ALL odds from a raw event to all_odds_analysis.csv
    
    This logs EVERY bookmaker × market × selection combination WITH:
    - Fair prices calculated from sharp bookmakers (Pinnacle, Betfair, others)
    - EV%, Prob, and Kelly Stake calculated
    - ALL bookmaker odds for cross-reference
    
    Args:
        event: Raw event dict from Odds API
        all_odds_csv: Path to all_odds_analysis.csv
        au_bookies: List of AU bookmaker keys to include
        bankroll: Bankroll for Kelly stake calculation
        kelly_fraction: Kelly fraction (default 0.25)
        betfair_commission: Betfair commission (default 0.06)
    """
    sport_key = event.get("sport_key", "")
    event_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time_utc = event.get("commence_time", "")
    
    # Convert UTC to Perth time (UTC+8) in readable format
    commence_time = ""
    if commence_time_utc:
        try:
            dt_utc = datetime.fromisoformat(commence_time_utc.replace('Z', '+00:00'))
            perth_tz = timezone(timedelta(hours=8))
            dt_perth = dt_utc.astimezone(perth_tz)
            commence_time = dt_perth.strftime("%Y-%m-%d %H:%M")
        except:
            commence_time = commence_time_utc
    
    if not all([event_id, home_team, away_team]):
        return
    
    bookmakers = event.get("bookmakers", [])
    
    # AU bookmaker column list
    au_books_in_csv = ["sportsbet", "tab", "neds", "ladbrokes_au", "pointsbetau",
                       "boombet", "betright", "playup", "unibet", "tabtouch",
                       "dabble_au", "betr_au", "bet365_au"]
    
    # Sharp bookmakers for fair price calculation
    sharp_bookies = ["pinnacle", "betfair_ex_au", "betfair_ex_eu"]
    
    # Extract ALL odds from ALL bookmakers
    for bookmaker in bookmakers:
        bkey = bookmaker.get("key", "")
        
        # Only log AU bookmakers + sharp bookmakers (for fair price calculation)
        if bkey not in au_bookies and bkey not in sharp_bookies:
            continue
        
        markets = bookmaker.get("markets", [])
        
        for market in markets:
            market_key = market.get("key", "")
            outcomes = market.get("outcomes", [])
            
            # Build a dict of all bookmaker odds for this market
            # (for filling the bookmaker columns)
            all_bookie_odds = {}
            for bm in bookmakers:
                bm_key = bm.get("key", "")
                for bm_market in bm.get("markets", []):
                    if bm_market.get("key") == market_key:
                        for bm_outcome in bm_market.get("outcomes", []):
                            outcome_name = bm_outcome.get("name", "")
                            outcome_odds_raw = bm_outcome.get("price", 0)
                            # Convert American odds to decimal if needed
                            outcome_odds = american_to_decimal(outcome_odds_raw, market_key, bm_key)
                            point = bm_outcome.get("point")
                            
                            # Create key for this outcome
                            if point is not None:
                                outcome_key = f"{outcome_name}_{point}"
                            else:
                                outcome_key = outcome_name
                            
                            if bm_key not in all_bookie_odds:
                                all_bookie_odds[bm_key] = {}
                            all_bookie_odds[bm_key][outcome_key] = outcome_odds
            
            # Log each outcome for this bookmaker
            for outcome in outcomes:
                outcome_name = outcome.get("name", "")
                outcome_odds_raw = outcome.get("price", 0)
                # Convert American odds to decimal if needed
                outcome_odds = american_to_decimal(outcome_odds_raw, market_key, bkey)
                point = outcome.get("point")
                description = outcome.get("description", "")  # Player name for props
                
                if outcome_odds <= 0:
                    continue
                
                # Build selection name
                if point is not None:
                    # For spreads, include the point
                    if market_key == "spreads":
                        selection = f"{outcome_name} {point:+.1f}"
                    # For player props, include player name
                    elif market_key.startswith("player_"):
                        selection = f"{description} {outcome_name}" if description else outcome_name
                    else:
                        selection = outcome_name
                    market_display = f"{market_key}_{abs(point)}"
                    outcome_key = f"{outcome_name}_{point}"
                else:
                    # For player props without point (double/triple double, first basket)
                    if market_key.startswith("player_") and description:
                        selection = f"{description} {outcome_name}"
                    else:
                        selection = outcome_name
                    market_display = market_key
                    outcome_key = outcome_name
                
                # Calculate fair price using sharp bookmakers
                pinnacle_odds_for_outcome = None
                betfair_odds_for_outcome = None
                other_sharps_odds_for_outcome = []
                
                # Sharp bookmaker keys (includes US books for player props)
                sharp_keys = ["pinnacle", "betfair_ex_au", "betfair_ex_eu", 
                             "draftkings", "fanduel", "betmgm",
                             "betonlineag", "bovada", "betus", "lowvig", 
                             "mybookieag", "marathonbet", "matchbook"]
                
                # For player props, prioritize US sharp books over Pinnacle
                is_player_prop = market_key.startswith("player_")
                us_sharp_books = ["draftkings", "fanduel", "betmgm"]
                
                for bm in bookmakers:
                    bm_key = bm.get("key", "")
                    if bm_key not in sharp_keys:
                        continue
                    
                    for bm_market in bm.get("markets", []):
                        if bm_market.get("key") == market_key:
                            for bm_outcome in bm_market.get("outcomes", []):
                                bm_outcome_name = bm_outcome.get("name", "")
                                bm_outcome_odds = bm_outcome.get("price", 0)
                                bm_point = bm_outcome.get("point")
                                
                                # Match outcome and point
                                if bm_outcome_name != outcome_name:
                                    continue
                                if point is not None and bm_point != point:
                                    continue
                                
                                if bm_key == "pinnacle":
                                    pinnacle_odds_for_outcome = bm_outcome_odds
                                elif bm_key in ["betfair_ex_au", "betfair_ex_eu"]:
                                    betfair_odds_for_outcome = bm_outcome_odds
                                elif bm_key in us_sharp_books and bm_outcome_odds > 1.0:
                                    # For player props, US sharps go in other_sharps with high weight
                                    other_sharps_odds_for_outcome.append(bm_outcome_odds)
                                elif bm_outcome_odds > 1.0:
                                    other_sharps_odds_for_outcome.append(bm_outcome_odds)
                
                # Calculate fair odds (different weighting for player props vs main markets)
                if is_player_prop:
                    # Player props: Use US sharps only (DraftKings, FanDuel, BetMGM, etc.)
                    # DraftKings 30%, FanDuel 30%, BetMGM 20%, BetOnline 10%, Bovada 10%
                    # Since these are all in other_sharps_odds_for_outcome, give 100% weight
                    fair_odds = calculate_fair_odds(
                        None,  # No Pinnacle for player props
                        None,  # No Betfair for player props
                        other_sharps_odds_for_outcome,
                        weight_pinnacle=0.0,
                        weight_betfair=0.0,
                        weight_sharps=1.0,  # 100% weight on US sharps
                        betfair_commission=betfair_commission
                    )
                else:
                    # Main markets: Pinnacle 60%, Betfair 25%, Others 15%
                    fair_odds = calculate_fair_odds(
                        pinnacle_odds_for_outcome,
                        betfair_odds_for_outcome,
                        other_sharps_odds_for_outcome,
                        betfair_commission=betfair_commission
                    )
                
                # Count how many sharp books were used
                num_sharps = 0
                if is_player_prop:
                    # For player props, only count US sharps (no Pinnacle/Betfair)
                    if other_sharps_odds_for_outcome:
                        valid_other = [o for o in other_sharps_odds_for_outcome if o > 1.0]
                        num_sharps = len(valid_other)  # Count each US sharp individually
                else:
                    # For main markets, count Pinnacle, Betfair, and other sharps
                    if pinnacle_odds_for_outcome and pinnacle_odds_for_outcome > 1.0:
                        num_sharps += 1
                    if betfair_odds_for_outcome and betfair_odds_for_outcome > 1.0:
                        num_sharps += 1
                    if other_sharps_odds_for_outcome:
                        valid_other = [o for o in other_sharps_odds_for_outcome if o > 1.0]
                        if len(valid_other) >= 2:  # Only counts if 2+ (since we take median)
                            num_sharps += len(valid_other)
                
                # Calculate edge, prob, stake
                if fair_odds > 1.0:
                    edge = (outcome_odds / fair_odds) - 1.0
                    implied_prob = 1.0 / fair_odds  # Probability based on FAIR odds, not book odds
                    
                    # Kelly stake
                    if edge > 0:
                        kelly_full = (outcome_odds * implied_prob - (1 - implied_prob)) / outcome_odds
                        kelly_stake_amt = bankroll * kelly_full * kelly_fraction
                        kelly_stake_amt = max(0, min(kelly_stake_amt, bankroll * 0.1))
                        stake_str = f"${int(kelly_stake_amt)}"
                    else:
                        stake_str = "$0"
                    
                    fair_str = f"{fair_odds:.3f}"
                    edge_str = f"{edge * 100:.2f}%"
                    prob_str = f"{implied_prob * 100:.2f}%"
                    num_sharps_str = str(num_sharps) if num_sharps > 0 else ""
                else:
                    fair_str = ""
                    edge_str = ""
                    prob_str = ""
                    stake_str = ""
                    num_sharps_str = ""
                
                # Build row for this specific bookmaker × selection
                all_odds_row = {
                    "Time": commence_time,
                    "sport": sport_key,
                    "event": f"{away_team} @ {home_team}",
                    "market": market_display,
                    "selection": selection,
                    "bookmaker": bkey,
                    "Book": f"{outcome_odds:.3f}",
                    "Fair": fair_str,
                    "EV%": edge_str,
                    "Prob": prob_str,
                    "Stake": stake_str,
                    "NumSharps": num_sharps_str,
                    "pinnacle": "",  # Will be filled from all_bookie_odds
                    "betfair": "",   # Will be filled from all_bookie_odds
                    # Initialize US sharp bookmaker columns
                    "draftkings": "",
                    "fanduel": "",
                    "betmgm": "",
                    "betonlineag": "",
                    "bovada": "",
                }
                
                # Fill in all bookmaker odds for this selection
                for bk_col in au_books_in_csv:
                    if bk_col in all_bookie_odds and outcome_key in all_bookie_odds[bk_col]:
                        all_odds_row[bk_col] = f"{all_bookie_odds[bk_col][outcome_key]:.3f}"
                
                # Fill pinnacle and betfair if available
                if "pinnacle" in all_bookie_odds and outcome_key in all_bookie_odds["pinnacle"]:
                    all_odds_row["pinnacle"] = f"{all_bookie_odds['pinnacle'][outcome_key]:.3f}"
                
                # Check both Betfair exchanges (prefer AU, fallback to EU)
                betfair_odds = None
                if "betfair_ex_au" in all_bookie_odds and outcome_key in all_bookie_odds["betfair_ex_au"]:
                    betfair_odds = all_bookie_odds["betfair_ex_au"][outcome_key]
                elif "betfair_ex_eu" in all_bookie_odds and outcome_key in all_bookie_odds["betfair_ex_eu"]:
                    betfair_odds = all_bookie_odds["betfair_ex_eu"][outcome_key]
                
                if betfair_odds:
                    all_odds_row["betfair"] = f"{betfair_odds:.3f}"
                
                # Fill US sharp bookmaker odds (for player props)
                us_sharps = ["draftkings", "fanduel", "betmgm", "betonlineag", "bovada"]
                for us_sharp in us_sharps:
                    if us_sharp in all_bookie_odds and outcome_key in all_bookie_odds[us_sharp]:
                        all_odds_row[us_sharp] = f"{all_bookie_odds[us_sharp][outcome_key]:.3f}"
                
                # Log to all_odds_analysis.csv
                log_all_odds(all_odds_csv, all_odds_row)
