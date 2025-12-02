"""
Logging functions for EV opportunities and analysis data.
Separated for clean architecture and easy maintenance.
"""
import csv
from pathlib import Path
from typing import Dict

from core.config import CSV_HEADERS


def log_ev_hit(csv_path: Path, row: Dict):
    """Log a +EV opportunity to CSV with all bookmaker odds."""
    file_exists = csv_path.exists()
    
    fieldnames = CSV_HEADERS
    key_map = {
        "pinnacle": "Pinnacle", "betfair": "Betfair", "sportsbet": "Sportsbet", "bet365": "Bet365", "pointsbetau": "Pointsbet", "betright": "Betright", "tab": "Tab", "dabble_au": "Dabble", "unibet": "Unibet", "ladbrokes": "Ladbrokes", "playup": "Playup", "tabtouch": "Tabtouch", "betr_au": "Betr", "neds": "Neds", "draftkings": "Draftkings", "fanduel": "Fanduel", "betmgm": "Betmgm", "betonlineag": "Betonline", "bovada": "Bovada", "boombet": "Boombet"
    }
    for k, v in row.items():
        if k in key_map:
            new_row[key_map[k]] = v
        elif k in fieldnames:
            new_row[k] = v
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_row)
    except Exception as e:
        print(f"[!] Error writing EV CSV: {e}")

    # Ensure all columns are present in new_row
    for col in fieldnames:
        if col not in new_row:
            new_row[col] = ""


def log_all_odds(csv_path: Path, row: Dict):
    """
    Log ALL opportunities for comprehensive analysis (not just +EV hits).
    This captures every opportunity so you can filter later without re-fetching API data.
    """
    from datetime import datetime
    
    file_exists = csv_path.exists()
    
    preferred = CSV_HEADERS
    key_map = {
        "pinnacle": "Pinnacle", "betfair": "Betfair", "sportsbet": "Sportsbet", "bet365": "Bet365", "pointsbetau": "Pointsbet", "betright": "Betright", "tab": "Tab", "dabble_au": "Dabble", "unibet": "Unibet", "ladbrokes": "Ladbrokes", "playup": "Playup", "tabtouch": "Tabtouch", "betr_au": "Betr", "neds": "Neds", "draftkings": "Draftkings", "fanduel": "Fanduel", "betmgm": "Betmgm", "betonlineag": "Betonline", "bovada": "Bovada", "boombet": "Boombet"
    }
    new_row = {}
    for k, v in row.items():
        if k in key_map:
            new_row[key_map[k]] = v
        elif k in preferred:
            new_row[k] = v
    # Ensure all columns are present in new_row
    for col in preferred:
        if col not in new_row:
            new_row[col] = ""
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=preferred)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_row)
    except Exception as e:
        print(f"[!] Error writing all odds CSV: {e}")
