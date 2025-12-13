"""
Logger for all odds analysis - captures EVERY opportunity without filtering.
This allows post-processing with different thresholds without re-fetching API data.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from core.config import CSV_HEADERS

# Track which file we're writing to (temp during writes, then swap)
_current_temp_file = None
_final_csv_path = None


def log_all_odds(csv_path: Path, row: Dict):
    """
    Log every single opportunity to raw_odds.csv
    No filtering - just raw data for later analysis

    Uses atomic write pattern: writes to .tmp file, then renames.
    This prevents "file in use" errors when Excel has the CSV open.
    """
    global _current_temp_file, _final_csv_path

    # Initialize temp file on first call
    if _final_csv_path is None:
        _final_csv_path = csv_path
        _current_temp_file = csv_path.parent / f"{csv_path.stem}.tmp"

    # Check if temp file exists (determines if we write header)
    file_exists = _current_temp_file.exists()

    preferred = CSV_HEADERS

    # Map old/original keys to new column names
    column_map = {
        # Main data columns (old format → new lowercase format)
        "Start Time": "start_time",
        "Sport": "sport",
        "Event": "event",
        "Market": "market",
        "Selection": "selection",
        "O/U + Y/N": "line",
        "Book": "book",
        "Price": "price",
        "Fair": "fair",
        "EV%": "ev",
        "Prob": "prob",
        "Stake": "stake",
        "NumSharps": "num_sharps",
        # Bookmaker columns (lowercase keys → Title case)
        "pinnacle": "Pinnacle",
        "betfair": "Betfair",
        "sportsbet": "Sportsbet",
        "bet365": "Bet365",
        "pointsbetau": "Pointsbet",
        "betright": "Betright",
        "tab": "Tab",
        "dabble_au": "Dabble",
        "unibet": "Unibet",
        "ladbrokes": "Ladbrokes",
        "playup": "Playup",
        "tabtouch": "Tabtouch",
        "betr_au": "Betr",
        "neds": "Neds",
        "draftkings": "Draftkings",
        "fanduel": "Fanduel",
        "betmgm": "Betmgm",
        "betonlineag": "Betonline",
        "bovada": "Bovada",
        "boombet": "Boombet",
    }

    new_row = {}
    for k, v in row.items():
        # Map old keys to new format
        if k in column_map:
            new_row[column_map[k]] = v
        elif k in preferred:
            new_row[k] = v
        # else: skip old keys not in preferred

    # Keep price column aligned with the bookmaker specified in book column
    book_value = row.get("Book") or row.get("book")
    if book_value:
        book_key_lower = book_value.lower()
        possible_columns = []
        if book_key_lower in column_map:
            possible_columns.append(column_map[book_key_lower])
        if book_value in column_map:
            mapped = column_map[book_value]
            if mapped not in possible_columns:
                possible_columns.append(mapped)
        if book_value in preferred and book_value not in possible_columns:
            possible_columns.append(book_value)

        price_from_book = None
        for col_name in possible_columns:
            col_value = new_row.get(col_name)
            if col_value:
                price_from_book = col_value
                break
        if not price_from_book:
            for raw_key in (book_value, book_key_lower):
                col_value = row.get(raw_key)
                if col_value:
                    price_from_book = col_value
                    break
        if price_from_book:
            new_row["price"] = price_from_book
    # Add timestamp if needed (optional, not in preferred)
    # if "timestamp" not in new_row:
    #     new_row["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    fieldnames = preferred
    # Write to temp file instead of final file
    with open(_current_temp_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(new_row)

    # Ensure all columns are present in new_row
    for col in preferred:
        if col not in new_row:
            new_row[col] = ""


def finalize_all_odds_csv():
    """
    Call this when all odds are logged to atomically replace the final CSV.
    This allows Excel to keep the file open without blocking writes.
    """
    global _current_temp_file, _final_csv_path

    if _current_temp_file is None or not _current_temp_file.exists():
        return  # Nothing to finalize

    try:
        # Remove old file if exists (Windows allows this even if open in Excel read-only)
        if _final_csv_path.exists():
            try:
                _final_csv_path.unlink()
            except PermissionError:
                # File is locked, try alternate approach
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
