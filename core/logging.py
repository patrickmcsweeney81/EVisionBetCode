"""
Logging functions for EV opportunities and analysis data.
Separated for clean architecture and easy maintenance.
"""
import csv
from pathlib import Path
from typing import Dict
import os

from core.config import CSV_HEADERS

# Track temp file for atomic writes
_current_temp_file = None
_final_csv_path = None


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
    
    Uses atomic write: writes to .tmp file to prevent "file in use" errors.
    """
    global _current_temp_file, _final_csv_path
    from datetime import datetime
    
    # Initialize temp file on first call
    if _final_csv_path is None:
        _final_csv_path = csv_path
        _current_temp_file = csv_path.parent / f"{csv_path.stem}.tmp"
    
    file_exists = _current_temp_file.exists()
    
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
        # Write to temp file
        with open(_current_temp_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=preferred)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_row)
    except Exception as e:
        print(f"[!] Error writing all odds CSV: {e}")


def finalize_all_odds_csv():
    """
    Atomically replace final CSV with temp file.
    Call this after all log_all_odds() calls are complete.
    """
    global _current_temp_file, _final_csv_path
    
    if _current_temp_file is None or not _current_temp_file.exists():
        return
    
    try:
        # Remove old file if exists
        if _final_csv_path.exists():
            try:
                _final_csv_path.unlink()
            except PermissionError:
                # File locked - rename to .old backup
                backup = _final_csv_path.parent / f"{_final_csv_path.stem}.old"
                if backup.exists():
                    backup.unlink()
                _final_csv_path.rename(backup)
        
        # Rename temp to final
        _current_temp_file.rename(_final_csv_path)
        print(f"[CSV] Successfully wrote {_final_csv_path}")
        
    except Exception as e:
        print(f"[!] Error finalizing CSV: {e}")
        print(f"[!] Data saved in: {_current_temp_file}")
    
    # Reset for next run
    _current_temp_file = None
    _final_csv_path = None
