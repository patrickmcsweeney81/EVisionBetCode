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
from core.interpolation import interpolate_odds


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
    """
    sport_key = event.get("sport_key", "")
    event_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time_utc = event.get("commence_time", "")

    # DEBUG: Print which bookmakers have totals markets for this event
    totals_coverage = {}
    bookmakers = event.get("bookmakers", [])
    for b in bookmakers:
        bkey = b.get('key', '')
        totals_keys = [m.get('key', '') for m in b.get('markets', []) if m.get('key', '').startswith('totals')]
        totals_coverage[bkey] = totals_keys
    print(f"[DEBUG] Totals market coverage for event {event_id}: {totals_coverage}")
    any_row_logged = False
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
    au_books_in_csv = [
        "sportsbet", "tab", "neds", "ladbrokes_au", "pointsbetau",
        "boombet", "betright", "playup", "unibet", "tabtouch",
        "dabble_au", "betr_au", "bet365_au"
    ]  # Do NOT include betfair_ex_au or betfair_ex_eu
    
    # Sharp bookmakers for fair price calculation
    sharp_bookies = ["pinnacle", "betfair_ex_au", "betfair_ex_eu"]
    
    # DEBUG: Print all bookmaker keys and their market keys for the first event
    print(f"[DEBUG] Bookmakers for event {event_id}: {[b.get('key') for b in bookmakers]}")
    for b in bookmakers:
        print(f"[DEBUG] Bookmaker {b.get('key')} markets: {[m.get('key') for m in b.get('markets', [])]}")

    # Extract ALL odds from ALL bookmakers
    for bookmaker in bookmakers:
        bkey = bookmaker.get("key", "")

        # Never log a row with bookmaker as betfair_ex_au or betfair_ex_eu
        if bkey in ["betfair_ex_au", "betfair_ex_eu"]:
            continue

        # Only log AU bookmakers + sharp bookmakers (for fair price calculation)
        if bkey not in au_bookies and bkey not in sharp_bookies:
            # Special fallback for main markets: if only Betfair (and/or Pinnacle) has odds, log a row for Pinnacle or Betfair
            # Only do this for h2h, spreads, totals (not player props)
            fallback_logged = False
            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")
                if market_key not in ["h2h", "spreads", "totals"]:
                    continue
                # Check if only Betfair and/or Pinnacle have odds for this market
                available_books = set()
                for bm in bookmakers:
                    bm_key = bm.get("key", "")
                    for bm_market in bm.get("markets", []):
                        if bm_market.get("key") == market_key:
                            available_books.add(bm_key)
                allowed = {"betfair_ex_au", "betfair_ex_eu", "pinnacle"}
                if available_books and available_books.issubset(allowed):
                    # Find a bookmaker to log as: prefer pinnacle, else betfair
                    log_bkey = None
                    if "pinnacle" in available_books:
                        log_bkey = "pinnacle"
                    elif "betfair_ex_au" in available_books or "betfair_ex_eu" in available_books:
                        log_bkey = "betfair"
                    if log_bkey:
                        # Inline the logging logic for this synthetic bookmaker
                        fake_bookie = {"key": log_bkey, "markets": [market]}
                        # The rest of the code is similar to the main loop below
                        # (Copy the market/outcome logging code here, but use fake_bookie and bookmakers)
                        # --- Begin inline logging ---
                        bkey_fallback = fake_bookie["key"]
                        markets_fallback = fake_bookie.get("markets", [])
                        for market_fallback in markets_fallback:
                            market_key_fallback = market_fallback.get("key", "")
                            outcomes_fallback = market_fallback.get("outcomes", [])
                            # Build a dict of all bookmaker odds for this market
                            all_bookie_odds_fallback = {}
                            for bm in bookmakers:
                                bm_key = bm.get("key", "")
                                for bm_market in bm.get("markets", []):
                                    if bm_market.get("key") == market_key_fallback:
                                        for bm_outcome in bm_market.get("outcomes", []):
                                            outcome_name = bm_outcome.get("name", "")
                                            outcome_odds_raw = bm_outcome.get("price", 0)
                                            outcome_odds = american_to_decimal(outcome_odds_raw, market_key_fallback, bm_key)
                                            point = bm_outcome.get("point")
                                            if point is not None:
                                                outcome_key = f"{outcome_name}_{point}"
                                            else:
                                                outcome_key = outcome_name
                                            if bm_key not in all_bookie_odds_fallback:
                                                all_bookie_odds_fallback[bm_key] = {}
                                            all_bookie_odds_fallback[bm_key][outcome_key] = outcome_odds
                            for outcome in outcomes_fallback:
                                outcome_name = outcome.get("name", "")
                                outcome_odds_raw = outcome.get("price", 0)
                                outcome_odds = american_to_decimal(outcome_odds_raw, market_key_fallback, bkey_fallback)
                                point = outcome.get("point")
                                description = outcome.get("description", "")
                                if outcome_odds <= 0:
                                    continue
                                if point is not None:
                                    if market_key_fallback == "spreads":
                                        selection = f"{outcome_name} {point:+.1f}"
                                    else:
                                        selection = outcome_name
                                    market_display = f"{market_key_fallback}_{abs(point)}"
                                    outcome_key = f"{outcome_name}_{point}"
                                else:
                                    selection = outcome_name
                                    market_display = market_key_fallback
                                    outcome_key = outcome_name
                                # Calculate fair price using sharp bookmakers
                                pinnacle_odds_for_outcome = None
                                betfair_odds_for_outcome = None
                                other_sharps_odds_for_outcome = []
                                sharp_keys = ["pinnacle", "betfair_ex_au", "betfair_ex_eu"]
                                for bm in bookmakers:
                                    bm_key = bm.get("key", "")
                                    if bm_key not in sharp_keys:
                                        continue
                                    for bm_market in bm.get("markets", []):
                                        if bm_market.get("key") == market_key_fallback:
                                            for bm_outcome in bm_market.get("outcomes", []):
                                                bm_outcome_name = bm_outcome.get("name", "")
                                                bm_outcome_odds = bm_outcome.get("price", 0)
                                                bm_point = bm_outcome.get("point")
                                                if bm_outcome_name != outcome_name:
                                                    continue
                                                if point is not None and bm_point != point:
                                                    continue
                                                if bm_key == "pinnacle":
                                                    pinnacle_odds_for_outcome = bm_outcome_odds
                                                elif bm_key in ["betfair_ex_au", "betfair_ex_eu"]:
                                                    betfair_odds_for_outcome = bm_outcome_odds
                                fair_odds = calculate_fair_odds(
                                    pinnacle_odds_for_outcome,
                                    betfair_odds_for_outcome,
                                    other_sharps_odds_for_outcome,
                                    betfair_commission=betfair_commission
                                )
                                num_sharps = 0
                                if pinnacle_odds_for_outcome and pinnacle_odds_for_outcome > 1.0:
                                    num_sharps += 1
                                if betfair_odds_for_outcome and betfair_odds_for_outcome > 1.0:
                                    num_sharps += 1
                                if fair_odds > 1.0 and num_sharps >= 2:
                                    edge = (outcome_odds / fair_odds) - 1.0
                                    implied_prob = 1.0 / fair_odds
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
                                    num_sharps_str = str(num_sharps)
                                else:
                                    continue
                                all_odds_row = {
                                    "Start Time": commence_time,
                                    "Sport": sport_key,
                                    "Event": f"{away_team} @ {home_team}",
                                    "Market": market_display,
                                    "Selection": selection,
                                    "O/U + Y/N": "",  # Fill if available
                                    "Book": bkey_fallback,
                                    "Price": f"{outcome_odds:.3f}",
                                    "Fair": fair_str,
                                    "EV%": edge_str,
                                    "Prob": prob_str,
                                    "Stake": stake_str,
                                    "NumSharps": num_sharps_str,
                                    "Pinnacle": "",
                                    "Betfair": "",
                                    "Draftkings": "",
                                    "Fanduel": "",
                                    "Betmgm": "",
                                    "Betonline": "",
                                    "Bovada": "",
                                }
                                for bk_col in au_books_in_csv:
                                    if bk_col in ["betfair_ex_au", "betfair_ex_eu"]:
                                        continue
                                    if bk_col in all_bookie_odds_fallback and outcome_key in all_bookie_odds_fallback[bk_col]:
                                        all_odds_row[bk_col] = f"{all_bookie_odds_fallback[bk_col][outcome_key]:.3f}"
                                if "pinnacle" in all_bookie_odds_fallback and outcome_key in all_bookie_odds_fallback["pinnacle"]:
                                    all_odds_row["pinnacle"] = f"{all_bookie_odds_fallback['pinnacle'][outcome_key]:.3f}"
                                betfair_odds = None
                                if "betfair_ex_au" in all_bookie_odds_fallback and outcome_key in all_bookie_odds_fallback["betfair_ex_au"]:
                                    betfair_odds = all_bookie_odds_fallback["betfair_ex_au"][outcome_key]
                                elif "betfair_ex_eu" in all_bookie_odds_fallback and outcome_key in all_bookie_odds_fallback["betfair_ex_eu"]:
                                    betfair_odds = all_bookie_odds_fallback["betfair_ex_eu"][outcome_key]
                                if betfair_odds:
                                    all_odds_row["betfair"] = f"{betfair_odds:.3f}"
                                # Log to all_odds_analysis.csv
                                print(f"[DEBUG] Fallback Logging row: event={event_id}, market={market_key_fallback}, selection={selection}, bookmaker={bkey_fallback}, odds={outcome_odds}")
                                log_all_odds(all_odds_csv, all_odds_row)
                                any_row_logged = True
                        fallback_logged = True
            if fallback_logged:
                continue
            else:
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
                    print(f"[DEBUG] Skipping outcome with non-positive odds: event={event_id}, market={market_key}, outcome={outcome_name}, odds={outcome_odds}")
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
                
                # Only log if fair_odds is valid and at least 2 sharps contributed
                if fair_odds > 1.0 and num_sharps >= 2:
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
                    num_sharps_str = str(num_sharps)
                else:
                    # Skip logging this row if not enough sharps or invalid fair price
                    continue
                
                # Build row for this specific bookmaker × selection
                all_odds_row = {
                    "Start Time": commence_time,
                    "Sport": sport_key,
                    "Event": f"{away_team} @ {home_team}",
                    "Market": market_display,
                    "Selection": selection,
                    "O/U + Y/N": "",  # Fill if available
                    "Book": bkey,
                    "Price": f"{outcome_odds:.3f}",
                    "Fair": fair_str,
                    "EV%": edge_str,
                    "Prob": prob_str,
                    "Stake": stake_str,
                    "NumSharps": num_sharps_str,
                    "Pinnacle": "",  # Will be filled from all_bookie_odds
                    "Betfair": "",   # Will be filled from all_bookie_odds
                    "Draftkings": "",
                    "Fanduel": "",
                    "Betmgm": "",
                    "Betonline": "",
                    "Bovada": "",
                }
                

                # DEBUG: Print all_bookie_odds and outcome_key for tracing
                if bkey in ["bovada", "draftkings", "neds", "ladbrokes_au", "sportsbet", "betmgm", "fanduel"]:
                    print(f"[TRACE] Event: {event_id}, Market: {market_key}, Selection: {selection}, Bookmaker: {bkey}, Outcome Key: {outcome_key}")
                    print(f"[TRACE] all_bookie_odds for {bkey}: {all_bookie_odds.get(bkey, {})}")


                # Only fill the odds for the current bookmaker in its column
                if bkey in all_bookie_odds and outcome_key in all_bookie_odds[bkey]:
                    all_odds_row[bkey] = f"{all_bookie_odds[bkey][outcome_key]:.3f}"
                else:
                    # Try to interpolate odds for this bookmaker/line if missing
                    # Only for player props (market_key.startswith("player_"))
                    if market_key.startswith("player_"):
                        # Gather all lines/odds for this bookmaker/market/outcome_name
                        alt_points = []
                        for alt_key, alt_odds in all_bookie_odds.get(bkey, {}).items():
                            # alt_key format: "Under_24.5", "Under_25.5", etc.
                            if alt_key.startswith(outcome_name + "_"):
                                try:
                                    alt_point = float(alt_key.split("_")[-1])
                                    alt_points.append((alt_point, alt_odds))
                                except Exception:
                                    continue
                        if point is not None and alt_points:
                            interp_odds = interpolate_odds(alt_points, float(point))
                            if interp_odds and interp_odds > 1.01:
                                all_odds_row[bkey] = f"({interp_odds:.2f})"  # Mark as interpolated

                # Optionally fill sharp columns for reference (pinnacle, betfair, US sharps)
                if "pinnacle" in all_bookie_odds and outcome_key in all_bookie_odds["pinnacle"]:
                    all_odds_row["pinnacle"] = f"{all_bookie_odds['pinnacle'][outcome_key]:.3f}"

                betfair_odds = None
                if "betfair_ex_au" in all_bookie_odds and outcome_key in all_bookie_odds["betfair_ex_au"]:
                    betfair_odds = all_bookie_odds["betfair_ex_au"][outcome_key]
                elif "betfair_ex_eu" in all_bookie_odds and outcome_key in all_bookie_odds["betfair_ex_eu"]:
                    betfair_odds = all_bookie_odds["betfair_ex_eu"][outcome_key]
                if betfair_odds:
                    all_odds_row["betfair"] = f"{betfair_odds:.3f}"

                us_sharps = ["draftkings", "fanduel", "betmgm", "betonlineag", "bovada"]
                for us_sharp in us_sharps:
                    if us_sharp in all_bookie_odds and outcome_key in all_bookie_odds[us_sharp]:
                        all_odds_row[us_sharp] = f"{all_bookie_odds[us_sharp][outcome_key]:.3f}"
                
                # Log to all_odds_analysis.csv
                print(f"[DEBUG] Logging row: event={event_id}, market={market_key}, selection={selection}, bookmaker={bkey}, odds={outcome_odds}")
                log_all_odds(all_odds_csv, all_odds_row)
                any_row_logged = True
    if not any_row_logged:
        print(f"[DEBUG] No valid outcomes logged for event {event_id} ({home_team} vs {away_team})")

