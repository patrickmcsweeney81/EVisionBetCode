#!/usr/bin/env python
"""
Outlier Test - Highlights AU books that are 3%+ higher than ANY sharp book
Uses raw_odds_pure.csv data only
"""
import csv
from pathlib import Path

from bookmaker_ratings import get_sharp_books_only, get_target_books_only, load_weight_config

# File paths
RAW_CSV = Path("data/raw_odds_pure.csv")
OUTPUT_CSV = Path("data/outlier_highlights.csv")

# Get sharp and target books
weights = load_weight_config("basketball_nba")
SHARP_BOOKS = list(get_sharp_books_only(weights).keys())
TARGET_BOOKS = get_target_books_only()

# AU target books only
AU_BOOKS = ["Sportsbet", "Pointsbet", "Tab", "Tabtouch", "Betr", "Neds", "Boombet"]

OUTLIER_THRESHOLD = 0.03  # 3%

META_COLS = {
    "timestamp",
    "sport",
    "event_id",
    "away_team",
    "home_team",
    "commence_time",
    "market",
    "point",
    "selection",
}


def parse_float(val: str) -> float:
    try:
        return float(val)
    except:
        return 0.0


def find_outliers():
    """Find AU book odds that are 3%+ higher than any sharp book."""

    print("=" * 70)
    print("OUTLIER DETECTION: AU Books > Sharp Books by 3%+")
    print("=" * 70)
    print(f"Sharp books: {', '.join(SHARP_BOOKS)}")
    print(f"AU target books: {', '.join(AU_BOOKS)}")
    print(f"Threshold: {OUTLIER_THRESHOLD:.0%}\n")

    # Read raw CSV
    rows = []
    with open(RAW_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"Loaded {len(rows)} rows from {RAW_CSV.name}")

    # Find outliers
    outliers = []
    bookmaker_cols = [c for c in rows[0].keys() if c not in META_COLS]

    for row in rows:
        # Get max sharp odds for this selection
        sharp_odds = []
        for book in SHARP_BOOKS:
            if book in bookmaker_cols:
                odds = parse_float(row.get(book, "0"))
                if odds > 1:
                    sharp_odds.append(odds)

        if not sharp_odds:
            continue

        max_sharp = max(sharp_odds)

        # Check each AU book
        for au_book in AU_BOOKS:
            if au_book not in bookmaker_cols:
                continue

            au_odds = parse_float(row.get(au_book, "0"))
            if au_odds <= 1:
                continue

            # Calculate edge over best sharp
            edge = (au_odds / max_sharp) - 1.0

            if edge >= OUTLIER_THRESHOLD:
                outliers.append(
                    {
                        "sport": row.get("sport", ""),
                        "event_id": row.get("event_id", ""),
                        "event": f"{row.get('away_team', '')} vs {row.get('home_team', '')}",
                        "market": row.get("market", ""),
                        "selection": row.get("selection", ""),
                        "point": row.get("point", ""),
                        "au_book": au_book,
                        "au_odds": au_odds,
                        "max_sharp": max_sharp,
                        "edge_percent": edge * 100,
                        "highlight": "YELLOW",
                        # Include all bookmaker odds for reference
                        **{book: parse_float(row.get(book, "0")) for book in bookmaker_cols},
                    }
                )

    print(f"\nFound {len(outliers)} outlier opportunities (AU book > sharp by 3%+)")

    # Write to CSV
    if outliers:
        # Build headers
        headers = [
            "highlight",
            "sport",
            "event_id",
            "event",
            "market",
            "selection",
            "point",
            "au_book",
            "au_odds",
            "max_sharp",
            "edge_percent",
        ] + bookmaker_cols

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for opp in outliers:
                # Format numbers
                row_data = opp.copy()
                row_data["au_odds"] = f"{opp['au_odds']:.2f}"
                row_data["max_sharp"] = f"{opp['max_sharp']:.2f}"
                row_data["edge_percent"] = f"{opp['edge_percent']:.2f}%"

                # Format bookmaker odds
                for book in bookmaker_cols:
                    val = opp.get(book, 0)
                    row_data[book] = f"{val:.2f}" if val > 0 else ""

                writer.writerow(row_data)

        print(f"[OK] Written to {OUTPUT_CSV}")

        # Show top 10
        print("\nTop 10 Outliers:")
        print("-" * 70)
        for i, opp in enumerate(
            sorted(outliers, key=lambda x: x["edge_percent"], reverse=True)[:10], 1
        ):
            print(
                f"{i:2}. {opp['selection']:30} | {opp['au_book']:12} {opp['au_odds']:.2f} vs Sharp {opp['max_sharp']:.2f} → +{opp['edge_percent']:.2f}%"
            )
    else:
        print("[!] No outliers found")


if __name__ == "__main__":
    find_outliers()
