from core.config import CSV_HEADERS
"""
Logging for one-sided/exotic markets flagged by the EV bot.
Appends flagged opportunities to data/exotics_value.csv for later review.
"""
import csv
from pathlib import Path
from typing import Dict

def log_exotic_value(csv_path: Path, row: Dict):
    """Log a flagged exotic/one-sided market to exotics_value.csv."""
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
        print(f"[!] Error writing exotics_value CSV: {e}")

    # Ensure all columns are present in new_row
    for col in fieldnames:
        if col not in new_row:
            new_row[col] = ""
