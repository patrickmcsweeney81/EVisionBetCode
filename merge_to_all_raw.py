"""
Merge individual sport raw CSVs into all_raw.csv

Usage:
    python merge_to_all_raw.py basketball_nba    # Merge NBA
    python merge_to_all_raw.py americanfootball_nfl  # Merge NFL

Behavior:
- Reads latest timestamped sport_raw_*.csv file
- Merges into data/v3/extracts/all_raw.csv
- Deduplicates by (event_id, market_type, point, selection, commence_time)
- Keeps newest data (by extracted_at timestamp)
- Deletes individual sport file after successful merge
"""

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def find_latest_sport_file(sport_key: str) -> Path:
    """Find latest timestamped raw file for sport"""
    extracts_dir = Path(__file__).parent / "data" / "v3" / "extracts"
    pattern = f"{sport_key}_raw_*.csv"
    
    files = list(extracts_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern} in {extracts_dir}")
    
    # Sort by name (timestamp) and get latest
    latest = sorted(files)[-1]
    logger.info(f"Found latest file: {latest.name}")
    return latest


def deduplicate_rows(
    existing_rows: List[Dict],
    new_rows: List[Dict],
    sport_key: str,
) -> List[Dict]:
    """
    Merge rows, keeping newest version of duplicates.
    
    Duplicate key: (event_id, market_type, point, selection, commence_time)
    Newest = highest extracted_at timestamp
    """
    # Build dict keyed by duplicate identifier
    merged = {}
    
    # Add existing rows first
    for row in existing_rows:
        key = (
            row.get("event_id", ""),
            row.get("market_type", ""),
            row.get("point", ""),
            row.get("selection", ""),
            row.get("commence_time", ""),
        )
        merged[key] = row
    
    # Add new rows, overwriting if newer
    for row in new_rows:
        key = (
            row.get("event_id", ""),
            row.get("market_type", ""),
            row.get("point", ""),
            row.get("selection", ""),
            row.get("commence_time", ""),
        )
        
        # If key exists, keep the one with newer extracted_at
        if key in merged:
            existing_extracted = merged[key].get("extracted_at", "")
            new_extracted = row.get("extracted_at", "")
            if new_extracted > existing_extracted:
                logger.debug(f"Updating duplicate: {key[:3]}")
                merged[key] = row
        else:
            merged[key] = row
    
    return list(merged.values())


def merge_sport_to_all_raw(sport_key: str) -> None:
    """
    Merge latest sport file into all_raw.csv
    
    Args:
        sport_key: Sport identifier (e.g., "basketball_nba", "americanfootball_nfl")
    """
    extracts_dir = Path(__file__).parent / "data" / "v3" / "extracts"
    all_raw_file = extracts_dir / "all_raw.csv"
    
    # Find latest sport file
    sport_file = find_latest_sport_file(sport_key)
    logger.info(f"✓ Found sport file: {sport_file.name}")
    
    # Read new sport data
    logger.info(f"Reading {sport_file.name}...")
    with open(sport_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        new_rows = list(reader)
    
    logger.info(f"✓ Read {len(new_rows)} rows from {sport_file.name}")
    
    # Read existing all_raw.csv if exists
    existing_rows = []
    if all_raw_file.exists():
        logger.info(f"Reading {all_raw_file.name}...")
        with open(all_raw_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
        logger.info(f"✓ Read {len(existing_rows)} existing rows")
    else:
        logger.info(f"Creating new {all_raw_file.name}")
    
    # Merge and deduplicate
    logger.info("Deduplicating rows (keeping newest by extracted_at)...")
    merged_rows = deduplicate_rows(existing_rows, new_rows, sport_key)
    logger.info(f"✓ Merged to {len(merged_rows)} unique rows")
    
    # Write merged result
    logger.info(f"Writing {all_raw_file.name}...")
    with open(all_raw_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_rows)
    
    logger.info(f"✓ Wrote {len(merged_rows)} rows to {all_raw_file.name}")
    
    # Delete original sport file
    logger.info(f"Cleaning up {sport_file.name}...")
    sport_file.unlink()
    logger.info(f"✓ Deleted {sport_file.name}")
    
    print("")
    print("=" * 70)
    print(f"✓ MERGE COMPLETE")
    print("=" * 70)
    print(f"Sport: {sport_key}")
    print(f"New rows added: {len(new_rows)}")
    print(f"Total rows in all_raw.csv: {len(merged_rows)}")
    print(f"Output: {all_raw_file}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python merge_to_all_raw.py <sport_key>")
        print("Examples:")
        print("  python merge_to_all_raw.py basketball_nba")
        print("  python merge_to_all_raw.py americanfootball_nfl")
        sys.exit(1)
    
    sport_key = sys.argv[1]
    
    try:
        merge_sport_to_all_raw(sport_key)
    except Exception as e:
        logger.error(f"✗ Merge failed: {e}")
        sys.exit(1)
