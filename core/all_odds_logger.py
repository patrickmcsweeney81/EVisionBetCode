"""
Logger for all odds analysis - captures EVERY opportunity without filtering.
This allows post-processing with different thresholds without re-fetching API data.
"""
import csv
from pathlib import Path
from typing import Dict
from datetime import datetime


def log_all_odds(csv_path: Path, row: Dict):
    """
    Log every single opportunity to all_odds_analysis.csv
    No filtering - just raw data for later analysis
    """
    file_exists = csv_path.exists()
    
    # Define fieldnames for all_odds_analysis.csv
    fieldnames = [
        "timestamp",      # When this opportunity was logged
        "Time",           # Event commence time
        "sport",
        "event",
        "market",
        "selection",
        "bookmaker",
        "Book",           # Bookmaker odds
        "Fair",           # Fair price
        "EV%",            # Edge percentage
        "Prob",           # Implied probability
        "Stake",          # Kelly stake
        "pinnacle",
        "betfair",
        # AU bookmakers
        "sportsbet", "tab", "neds", "ladbrokes_au", "pointsbetau",
        "boombet", "betright", "playup", "unibet", "tabtouch",
        "dabble_au", "betr_au", "bet365_au"
    ]
    
    # Add timestamp to row
    if "timestamp" not in row:
        row["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
