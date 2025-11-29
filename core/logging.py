"""
Logging functions for EV opportunities and analysis data.
Separated for clean architecture and easy maintenance.
"""
import csv
from pathlib import Path
from typing import Dict
from core.config import ALL_BOOKIES_ORDERED


def log_ev_hit(csv_path: Path, row: Dict):
    """Log a +EV opportunity to CSV with all bookmaker odds."""
    file_exists = csv_path.exists()
    
    # Base columns + selected bookmaker columns (AU books only, no US/international)
    fieldnames = [
        "Time", "sport", "event", "market", "selection",
        "bookmaker", "Book", "Fair", "EV", "prob", "Stake",
        # Sharp books for reference
        "pinnacle", "betfair",
        # AU bookmakers (from Odds API widget list)
        "sportsbet", "tab", "neds", "ladbrokes_au", "pointsbetau",
        "boombet", "betright", "playup", "unibet", "tabtouch",
        "dabble_au", "betr_au", "bet365_au"
    ]
    
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"[!] Error writing EV CSV: {e}")


def log_all_odds(csv_path: Path, row: Dict):
    """
    Log ALL opportunities for comprehensive analysis (not just +EV hits).
    This captures every opportunity so you can filter later without re-fetching API data.
    """
    from datetime import datetime
    
    file_exists = csv_path.exists()
    
    # Same structure as hits_ev.csv for easy comparison
    fieldnames = [
        "Time",           # Event commence time (Perth local time)
        "sport", "event", "market", "selection",
        "bookmaker",      # Which bookmaker has this opportunity
        "Book",           # Bookmaker odds
        "Fair",           # Fair price
        "EV%",            # Edge percentage
        "Prob",           # Implied probability of fair price
        "Stake",          # Kelly stake suggestion
        "NumSharps",      # Number of sharp bookmakers used in fair calculation
        # Sharp bookmakers (EU/Global)
        "pinnacle", "betfair",
        # US sharp bookmakers (for player props)
        "draftkings", "fanduel", "betmgm", "betonlineag", "bovada",
        # AU bookmakers (target books)
        "sportsbet", "tab", "neds", "ladbrokes_au", "pointsbetau",
        "boombet", "betright", "playup", "unibet", "tabtouch",
        "dabble_au", "betr_au", "bet365_au"
    ]
    
    # Remove timestamp from row if present (no longer needed)
    row.pop("timestamp", None)
    
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"[!] Error writing all odds CSV: {e}")
