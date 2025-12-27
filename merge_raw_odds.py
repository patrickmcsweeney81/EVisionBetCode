"""
Merge all sport-specific raw odds CSVs into a single all_raw_odds.csv file.
This script combines raw_NFL.csv, raw_NBA.csv, raw_MLB.csv, raw_NHL.csv, etc.
into a unified file for admin access and analysis.
"""

import csv
from pathlib import Path
from typing import Dict, List, Set

# Data paths
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "all_raw_odds.csv"

# Sport files to merge (in priority order)
SPORT_FILES = [
    "raw_NFL.csv",
    "raw_NBA.csv",
    "raw_MLB.csv",
    "raw_NHL.csv",
    "raw_NCAAF.csv",
    "raw_EPL.csv",
]


def collect_all_bookmakers(sport_files: List[Path]) -> Set[str]:
    """Scan all sport CSV files and collect all unique bookmaker column names."""
    all_bookies = set()
    base_columns = ["timestamp", "sport", "event_id", "commence_time", "teams", "market", "line", "selection", "player"]
    
    for sport_file in sport_files:
        if not sport_file.exists():
            continue
        
        try:
            with open(sport_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    for field in reader.fieldnames:
                        if field not in base_columns:
                            all_bookies.add(field)
        except Exception as e:
            print(f"⚠️  Warning: Could not read {sport_file.name}: {e}")
    
    return all_bookies


def merge_sport_csvs():
    """Merge all sport-specific CSVs into all_raw_odds.csv."""
    print("[MERGE] Merging sport-specific CSVs into all_raw_odds.csv")
    print("=" * 70)
    
    # Find existing sport files
    sport_files = []
    for sport_filename in SPORT_FILES:
        sport_path = DATA_DIR / sport_filename
        if sport_path.exists():
            sport_files.append(sport_path)
            print(f"✓ Found {sport_filename}")
        else:
            print(f"  Skip {sport_filename} (not found)")
    
    if not sport_files:
        print("❌ No sport CSV files found in data/")
        return
    
    # Collect all unique bookmaker columns across all sports
    print("\n[SCAN] Collecting bookmaker columns...")
    all_bookies = collect_all_bookmakers(sport_files)
    all_bookies = sorted(all_bookies)
    print(f"✓ Found {len(all_bookies)} unique bookmakers")
    
    # Define output headers
    base_columns = ["timestamp", "sport", "event_id", "commence_time", "teams", "market", "line", "selection", "player"]
    headers = base_columns + all_bookies
    
    # Merge all rows
    print("\n[MERGE] Merging rows...")
    all_rows = []
    row_count_by_sport = {}
    
    for sport_file in sport_files:
        sport_name = sport_file.stem.replace("raw_", "")
        row_count = 0
        
        try:
            with open(sport_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Ensure all bookmaker columns exist (fill missing with empty string)
                    for bookie in all_bookies:
                        if bookie not in row:
                            row[bookie] = ""
                    all_rows.append(row)
                    row_count += 1
            
            row_count_by_sport[sport_name] = row_count
            print(f"  {sport_name}: {row_count} rows")
        except Exception as e:
            print(f"⚠️  Error reading {sport_file.name}: {e}")
    
    # Write merged CSV
    print(f"\n[WRITE] Writing {len(all_rows)} rows to {OUTPUT_FILE.name}...")
    try:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in all_rows:
                writer.writerow(row)
        
        print(f"✅ Successfully wrote {OUTPUT_FILE}")
        print(f"\n[SUMMARY]")
        print(f"  Total rows: {len(all_rows)}")
        print(f"  Total bookmakers: {len(all_bookies)}")
        print(f"  Sports merged: {len(row_count_by_sport)}")
        print(f"  Breakdown:")
        for sport, count in row_count_by_sport.items():
            print(f"    - {sport}: {count} rows")
        print("\n[DONE]")
    except Exception as e:
        print(f"❌ Error writing merged file: {e}")


def main():
    merge_sport_csvs()


if __name__ == "__main__":
    main()
