"""
Manage AllSports_EV.csv - Archive, rotate, and cleanup daily history.

Workflow:
1. Before calculation: Call this script to archive previous runs
2. If AllSports_EV.csv exists → append to AllSports_EV_{date}.csv
3. Delete AllSports_EV_{date}.csv files older than 4 days
4. Fresh data can then be written to AllSports_EV.csv

Usage:
    python manage_allsports_ev.py
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import glob

EV_DIR = "data/v3/extracts"
ALLSPORTS_EV = os.path.join(EV_DIR, "AllSports_EV.csv")
DAYS_TO_KEEP = 4


def get_today_dated_file():
    """Get today's dated AllSports_EV file name."""
    date_str = datetime.now().strftime("%m.%d.%y")
    return os.path.join(EV_DIR, f"AllSports_EV_{date_str}.csv")


def archive_current_to_dated():
    """
    If AllSports_EV.csv exists, append it to today's dated file.
    This captures all runs from before this call.
    """
    if not os.path.exists(ALLSPORTS_EV):
        print("[INFO] No current AllSports_EV.csv to archive")
        return

    dated_file = get_today_dated_file()
    current_df = pd.read_csv(ALLSPORTS_EV)

    if os.path.exists(dated_file):
        # Append to existing dated file
        dated_df = pd.read_csv(dated_file)
        combined = pd.concat([dated_df, current_df], ignore_index=True)
        combined.to_csv(dated_file, index=False)
        print(
            f"[OK] Appended to {os.path.basename(dated_file)}: "
            f"{len(combined):,} rows"
        )
    else:
        # Create new dated file
        current_df.to_csv(dated_file, index=False)
        print(
            f"[OK] Created {os.path.basename(dated_file)}: "
            f"{len(current_df):,} rows"
        )


def cleanup_old_archives():
    """Delete AllSports_EV_*.csv files older than DAYS_TO_KEEP."""
    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)
    pattern = os.path.join(EV_DIR, "AllSports_EV_*.csv")
    archived_files = glob.glob(pattern)

    deleted_count = 0
    for file_path in archived_files:
        try:
            file_mtime = os.path.getmtime(file_path)
            file_date = datetime.fromtimestamp(file_mtime)

            if file_date < cutoff_date:
                os.remove(file_path)
                print(
                    f"[OK] Deleted {os.path.basename(file_path)} "
                    f"({file_date.strftime('%m.%d.%y')})"
                )
                deleted_count += 1
        except Exception as e:
            print(f"[WARN] Could not delete {file_path}: {e}")

    if deleted_count == 0:
        print(f"[INFO] No files older than {DAYS_TO_KEEP} days to delete")


def list_history():
    """Show current dated files (history)."""
    pattern = os.path.join(EV_DIR, "AllSports_EV_*.csv")
    files = sorted(glob.glob(pattern), reverse=True)

    if not files:
        print("[INFO] No dated history files")
        return

    print("[INFO] AllSports_EV History:")
    for file_path in files:
        file_size_kb = os.path.getsize(file_path) / 1024
        file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
        df = pd.read_csv(file_path)
        print(
            f"  {os.path.basename(file_path)}: {len(df):,} rows, "
            f"{file_size_kb:.1f} KB ({file_date.strftime('%m.%d.%y %H:%M')})"
        )


def main():
    """Run management pipeline."""
    print("[MANAGE] AllSports_EV Daily Management")
    print()

    # Step 1: Archive current to dated
    archive_current_to_dated()
    print()

    # Step 2: Cleanup old archives
    cleanup_old_archives()
    print()

    # Step 3: Show history
    list_history()
    print()
    print(
        "[DONE] Ready for next calculation run. "
        "Fresh data will be written to AllSports_EV.csv"
    )


if __name__ == "__main__":
    main()
