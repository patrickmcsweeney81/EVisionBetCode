"""
Raw odds extractor - logs ALL bookmaker odds to raw_odds.csv
This captures every opportunity WITH fair prices, EV%, and Prob calculated.
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

from core.config import CSV_HEADERS
from core.logging import log_all_odds
from core.fair_odds import calculate_fair_odds

BOOK_TO_COL = {
    "pinnacle": "Pinnacle",
    "betfair_ex_eu": "Betfair_EU",
    "betfair_ex_au": "Betfair_AU",
    "draftkings": "Draftkings",
    "fanduel": "Fanduel",
    "betmgm": "Betmgm",
    "betonlineag": "Betonline",
    "bovada": "Bovada",
    "betus": "Betus",
    "lowvig": "Lowvig",
    "mybookieag": "Mybookie",
    "marathonbet": "Marathonbet",
    "matchbook": "Matchbook",
    "sportsbet": "Sportsbet",
    "bet365_au": "Bet365",
    "bet365": "Bet365",
    "pointsbetau": "Pointsbet",
    "betright": "Betright",
    "tab": "Tab",
    "dabble_au": "Dabble",
    "unibet": "Unibet",
    "ladbrokes_au": "Ladbrokes",
    "playup": "Playup",
    "tabtouch": "Tabtouch",
    "betr_au": "Betr",
    "neds": "Neds",
    "boombet": "Boombet",
    "caesars": "Caesars",
    "betrivers": "Betrivers",
    "sugarhouse": "Sugarhouse",
    "superbook": "Superbook",
    "twinspires": "Twinspires",
    "wynnbet": "Wynnbet",
    "williamhill_us": "Williamhill",
}

MAIN_MARKET_SHARPS = {
    "draftkings", "fanduel", "betmgm", "betonlineag", "bovada",
    "betus", "lowvig", "mybookieag", "marathonbet", "matchbook",
}

US_SHARP_BOOKS = {"draftkings", "fanduel", "betmgm"}


def american_to_decimal(american_odds: float, market_key: str = "", bookmaker_key: str = "") -> float:
    """Convert American odds to decimal odds with prop/book heuristics."""
    is_likely_american = market_key.startswith("player_") or bookmaker_key in {
        "draftkings", "fanduel", "betmgm", "betonlineag", "bovada",
        "williamhill_us", "pointsbetau", "fanatics",
    }

    if american_odds >= 100:
        return (american_odds / 100.0) + 1.0
    if american_odds <= -100:
        return (100.0 / abs(american_odds)) + 1.0
    if american_odds >= 10 and is_likely_american:
        return (american_odds / 100.0) + 1.0
    return american_odds


def get_csv_column_name(bookmaker_key: str) -> str:
    return BOOK_TO_COL.get(bookmaker_key, bookmaker_key.title())


def _format_commence_time(commence_time_utc: str) -> str:
    if not commence_time_utc:
        return ""
    try:
        dt_utc = datetime.fromisoformat(commence_time_utc.replace("Z", "+00:00"))
        perth_tz = timezone(timedelta(hours=8))
        return dt_utc.astimezone(perth_tz).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return commence_time_utc


def log_raw_event_odds(
    event: Dict,
    all_odds_csv: Path,
    au_bookies: List[str],
    bankroll: float = 1000,
    kelly_fraction: float = 0.25,
    betfair_commission: float = 0.06,
):
    """Extract and log ALL odds for an event in one row per outcome."""
    sport_key = event.get("sport_key", "")
    event_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    commence_time_utc = event.get("commence_time", "")

    commence_time = _format_commence_time(commence_time_utc)

    if not all([event_id, home_team, away_team]):
        return

    bookmakers = event.get("bookmakers", [])
    any_row_logged = False
    au_bookie_set = set(au_bookies)

    market_keys = set()
    for bm in bookmakers:
        for mkt in bm.get("markets", []):
            mk = mkt.get("key", "")
            if mk:
                market_keys.add(mk)

    for market_key in market_keys:
        all_bookie_odds: Dict[str, Dict[str, float]] = {}
        outcome_meta: Dict[str, Dict[str, Optional[str]]] = {}

        for bm in bookmakers:
            bm_key = bm.get("key", "")
            for bm_market in bm.get("markets", []):
                if bm_market.get("key") != market_key:
                    continue
                for bm_outcome in bm_market.get("outcomes", []):
                    outcome_name = bm_outcome.get("name", "")
                    outcome_odds_raw = bm_outcome.get("price", 0)
                    outcome_odds = american_to_decimal(outcome_odds_raw, market_key, bm_key)
                    point = bm_outcome.get("point")
                    description = bm_outcome.get("description", "")

                    outcome_key = f"{outcome_name}_{point}" if point is not None else outcome_name

                    if bm_key not in all_bookie_odds:
                        all_bookie_odds[bm_key] = {}
                    all_bookie_odds[bm_key][outcome_key] = outcome_odds

                    if outcome_key not in outcome_meta:
                        outcome_meta[outcome_key] = {
                            "name": outcome_name,
                            "point": point,
                            "description": description,
                        }

        for outcome_key, meta in outcome_meta.items():
            outcome_name = meta.get("name", "")
            point = meta.get("point")
            description = meta.get("description", "") or ""

            if point is not None:
                if market_key == "spreads":
                    selection = f"{outcome_name} {point:+.1f}"
                elif market_key.startswith("player_"):
                    selection = f"{description} {outcome_name}" if description else outcome_name
                else:
                    selection = outcome_name
                market_display = f"{market_key}_{abs(point)}"
            else:
                if market_key.startswith("player_") and description:
                    selection = f"{description} {outcome_name}"
                else:
                    selection = outcome_name
                market_display = market_key

            is_player_prop = market_key.startswith("player_")

            pinnacle_odds = all_bookie_odds.get("pinnacle", {}).get(outcome_key)
            betfair_au = all_bookie_odds.get("betfair_ex_au", {}).get(outcome_key)
            betfair_eu = all_bookie_odds.get("betfair_ex_eu", {}).get(outcome_key)
            betfair_odds = betfair_au if betfair_au and betfair_au > 1.0 else betfair_eu

            sharp_keys = [
                "draftkings", "fanduel", "betmgm", "betonlineag", "bovada",
                "betus", "lowvig", "mybookieag", "marathonbet", "matchbook",
            ]

            other_sharps_odds_for_outcome = []
            sharp_books_used = set()

            if pinnacle_odds and pinnacle_odds > 1.0:
                sharp_books_used.add("pinnacle")
            if betfair_odds and betfair_odds > 1.0:
                sharp_books_used.add("betfair")

            for sk in sharp_keys:
                odds_val = all_bookie_odds.get(sk, {}).get(outcome_key)
                if odds_val and odds_val > 1.0:
                    if is_player_prop:
                        if sk in US_SHARP_BOOKS:
                            other_sharps_odds_for_outcome.append(odds_val)
                            sharp_books_used.add(sk)
                    else:
                        if sk in MAIN_MARKET_SHARPS:
                            other_sharps_odds_for_outcome.append(odds_val)
                            sharp_books_used.add(sk)

            if is_player_prop:
                fair_odds = calculate_fair_odds(
                    None,
                    None,
                    other_sharps_odds_for_outcome,
                    weight_pinnacle=0.0,
                    weight_betfair=0.0,
                    weight_sharps=1.0,
                    betfair_commission=betfair_commission,
                )
            else:
                fair_odds = calculate_fair_odds(
                    pinnacle_odds,
                    betfair_odds,
                    other_sharps_odds_for_outcome,
                    betfair_commission=betfair_commission,
                )

            # Allow any available sharp source to count; we keep required_sharps below
            num_sharps = len(sharp_books_used)

            # Allow logging with a single sharp source to keep coverage high
            required_sharps = 1

            if fair_odds <= 1.0 or num_sharps < required_sharps:
                continue

            # Find best AU bookmaker price only
            available_prices = []
            for bk, outcomes_map in all_bookie_odds.items():
                if bk not in au_bookie_set:  # Only AU bookies
                    continue
                odds_val = outcomes_map.get(outcome_key)
                if odds_val and odds_val > 0:
                    available_prices.append((get_csv_column_name(bk), odds_val))
            if not available_prices:
                continue  # Skip if no AU price is available
            best_book_col, outcome_odds = max(available_prices, key=lambda t: t[1])

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

            all_odds_row = {col: "" for col in CSV_HEADERS}
            all_odds_row.update({
                "start_time": commence_time,
                "sport": sport_key,
                "event": f"{away_team} @ {home_team}",
                "market": market_display,
                "selection": selection,
                "line": "",
                "book": best_book_col,
                "price": f"{outcome_odds:.3f}",
                "fair": fair_str,
                "ev": edge_str,
                "prob": prob_str,
                "stake": stake_str,
                "num_sharps": num_sharps_str,
            })

            # DEBUG: Print outcome details for player props to track Over/Under mix-up
            if is_player_prop and "threes" in market_key and description:
                print(f"[DEBUG] Player: {description}, Market: {market_key}, Outcome_key: {outcome_key}")
                print(f"[DEBUG] Selection: {selection}")
                if "pinnacle" in all_bookie_odds:
                    print(f"[DEBUG] Pinnacle odds for {outcome_key}: {all_bookie_odds['pinnacle'].get(outcome_key)}")
                if "sportsbet" in all_bookie_odds:
                    print(f"[DEBUG] Sportsbet odds for {outcome_key}: {all_bookie_odds['sportsbet'].get(outcome_key)}")
            
            for bk, outcomes_map in all_bookie_odds.items():
                odds_val = outcomes_map.get(outcome_key)
                if odds_val and odds_val > 0:
                    csv_col = get_csv_column_name(bk)
                    all_odds_row[csv_col] = f"{odds_val:.3f}"

            if "pinnacle" in all_bookie_odds and outcome_key in all_bookie_odds["pinnacle"]:
                all_odds_row["Pinnacle"] = f"{all_bookie_odds['pinnacle'][outcome_key]:.3f}"
            if "betfair_ex_au" in all_bookie_odds and outcome_key in all_bookie_odds["betfair_ex_au"]:
                all_odds_row["Betfair_AU"] = f"{all_bookie_odds['betfair_ex_au'][outcome_key]:.3f}"
            if "betfair_ex_eu" in all_bookie_odds and outcome_key in all_bookie_odds["betfair_ex_eu"]:
                all_odds_row["Betfair_EU"] = f"{all_bookie_odds['betfair_ex_eu'][outcome_key]:.3f}"

            log_all_odds(all_odds_csv, all_odds_row)
            any_row_logged = True

    # Silenced noisy per-event debug when no rows log; rely on CSV counts instead.

