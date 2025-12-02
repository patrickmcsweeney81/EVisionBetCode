"""
Logger for all odds analysis - captures EVERY opportunity without filtering.
This allows post-processing with different thresholds without re-fetching API data.
"""
from pathlib import Path
from typing import Dict
from datetime import datetime

import csv
from core.config import CSV_HEADERS


def log_all_odds(csv_path: Path, row: Dict):
    """
    Log every single opportunity to all_odds_analysis.csv
    No filtering - just raw data for later analysis
    """
    file_exists = csv_path.exists()
    
    preferred = CSV_HEADERS
    # Map old/original keys to new column names
    key_map = {
        "pinnacle": "Pinnacle", "betfair": "Betfair", "sportsbet": "Sportsbet", "bet365": "Bet365", "pointsbetau": "Pointsbet", "betright": "Betright", "tab": "Tab", "dabble_au": "Dabble", "unibet": "Unibet", "ladbrokes": "Ladbrokes", "playup": "Playup", "tabtouch": "Tabtouch", "betr_au": "Betr", "neds": "Neds", "draftkings": "Draftkings", "fanduel": "Fanduel", "betmgm": "Betmgm", "betonlineag": "Betonline", "bovada": "Bovada", "boombet": "Boombet"
    }
    new_row = {}
    for k, v in row.items():
        if k in key_map:
            new_row[key_map[k]] = v
        elif k in preferred:
            new_row[k] = v
        # else: skip old keys not in preferred

    # Keep Price column aligned with the bookmaker specified in Book
    book_value = row.get("Book") or row.get("book")
    if book_value:
        book_key_lower = book_value.lower()
        possible_columns = []
        if book_key_lower in key_map:
            possible_columns.append(key_map[book_key_lower])
        if book_value in key_map:
            mapped = key_map[book_value]
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
            new_row["Price"] = price_from_book
    # Add timestamp if needed (optional, not in preferred)
    # if "timestamp" not in new_row:
    #     new_row["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    fieldnames = preferred
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        writer.writerow(new_row)

    # Ensure all columns are present in new_row
    for col in preferred:
        if col not in new_row:
            new_row[col] = ""
