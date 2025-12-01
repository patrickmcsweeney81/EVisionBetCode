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
    fieldnames = list(row.keys())
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"[!] Error writing exotics_value CSV: {e}")
