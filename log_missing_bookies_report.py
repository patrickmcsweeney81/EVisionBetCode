"""
log_missing_bookies_report.py
Summarize missing AU bookies/markets from the coverage log and output a report.
"""
import csv
from collections import Counter, defaultdict

LOG_FILE = "data/missing_bookies_log.csv"
REPORT_FILE = "data/missing_bookies_summary.csv"

def summarize_missing_bookies():
    missing_counter = Counter()
    event_counter = defaultdict(set)
    with open(LOG_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for bookie in row["missing_bookies"].split(","):
                if bookie:
                    missing_counter[bookie] += 1
                    event_counter[bookie].add((row["sport"], row["event"]))
    with open(REPORT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bookie", "missing_count", "unique_events"])
        for bookie, count in missing_counter.most_common():
            writer.writerow([bookie, count, len(event_counter[bookie])])
    print(f"Summary written to {REPORT_FILE}")

if __name__ == "__main__":
    summarize_missing_bookies()
