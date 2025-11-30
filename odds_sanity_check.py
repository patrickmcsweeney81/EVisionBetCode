"""
odds_sanity_check.py
Scan all_odds_analysis.csv for suspicious odds (identical, out-of-range, missing, or stale).
"""
import csv
from collections import Counter, defaultdict

CSV_FILE = "data/all_odds_analysis.csv"
LOG_FILE = "data/odds_sanity_issues.csv"

# Bookies to check
BOOKIES = [
    "pinnacle","betfair","draftkings","fanduel","betmgm","betonlineag","bovada",
    "sportsbet","tab","neds","ladbrokes_au","pointsbetau","boombet","betright",
    "playup","unibet","tabtouch","dabble_au","betr_au","bet365_au"
]

MIN_ODDS = 1.01
MAX_ODDS = 100.0


def is_suspicious(odds, all_odds):
    # Identical to >5 other bookies (possible copy error)
    if odds and all_odds.count(odds) > 5:
        return "identical_to_many"
    # Out of range
    try:
        o = float(odds)
        if o < MIN_ODDS or o > MAX_ODDS:
            return "out_of_range"
    except Exception:
        if odds.strip() == "":
            return "missing"
        return "not_a_number"
    return None


def main():
    issues = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_odds = [row[b] for b in BOOKIES if b in row]
            for b in BOOKIES:
                if b in row:
                    reason = is_suspicious(row[b], all_odds)
                    if reason:
                        issues.append({
                            "event": row.get("event",""),
                            "market": row.get("market",""),
                            "selection": row.get("selection",""),
                            "bookie": b,
                            "odds": row[b],
                            "reason": reason
                        })
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event","market","selection","bookie","odds","reason"])
        writer.writeheader()
        for issue in issues:
            writer.writerow(issue)
    print(f"Sanity check complete. Issues written to {LOG_FILE}")

if __name__ == "__main__":
    main()
