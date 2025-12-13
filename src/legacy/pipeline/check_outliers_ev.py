#!/usr/bin/env python
"""
Check each AU-book outlier and see if it is an EV opportunity using the
current fair-odds calculation (with sport-specific weights and outlier removal).

Inputs:
- data/raw_odds_pure.csv
- data/outlier_highlights.csv (from outlier_test.py)

Output:
- data/outlier_ev_check.csv
"""
import csv
from pathlib import Path

import calculate_ev as ev
from bookmaker_ratings import get_sharp_books_only, load_weight_config

RAW_CSV = Path("data/raw_odds_pure.csv")
OUTLIER_CSV = Path("data/outlier_highlights.csv")
OUTPUT_CSV = Path("data/outlier_ev_check.csv")

META_COLS = ev.META_COLS
EV_MIN_EDGE = ev.EV_MIN_EDGE


def load_rows(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bookie_columns(row):
    return [c for c in row.keys() if c not in META_COLS]


def player_key(market: str, selection: str) -> str:
    return ev._player_key(selection) if market.startswith("player_") else ""


def main():
    raw_rows = load_rows(RAW_CSV)
    outliers = load_rows(OUTLIER_CSV)

    grouped = ev.group_rows_wide(raw_rows)
    cols = bookie_columns(raw_rows[0]) if raw_rows else []

    results = []

    for o in outliers:
        sport = o.get("sport", "")
        event_id = o.get("event_id", "")
        market = o.get("market", "")
        selection = o.get("selection", "")
        point = o.get("point", "")
        au_book = o.get("au_book", "")
        au_odds = ev.parse_float(o.get("au_odds", "0"))

        # Configure sharp weights per sport
        weights = load_weight_config(sport)
        ev.SHARP_WEIGHTS = get_sharp_books_only(weights)

        key = (sport, event_id, market, point, player_key(market, selection))
        rows = grouped.get(key)
        if not rows:
            results.append({**o, "status": "missing_rows"})
            continue

        side_a, side_b = ev.extract_sides(rows)
        if not side_a or not side_b:
            results.append({**o, "status": "missing_sides"})
            continue

        fair_a, fair_b, sharp_count = ev.fair_from_sharps(side_a, side_b, cols)
        if sharp_count == 0 or fair_a <= 1 or fair_b <= 1:
            results.append({**o, "status": "no_sharps", "fair_odds": ""})
            continue

        # Determine which side matches selection
        sel_lower = selection.lower()
        if sel_lower.endswith(" over") or sel_lower.startswith("over"):
            fair = fair_a
            side = side_a
        elif sel_lower.endswith(" under") or sel_lower.startswith("under"):
            fair = fair_b
            side = side_b
        else:
            # Fallback: use selection match
            fair = fair_a
            side = side_a

        odds = ev.parse_float(side.get(au_book, "0")) if side else 0.0
        if odds <= 1:
            odds = au_odds  # fallback to outlier value

        ev_pct = (odds / fair - 1.0) * 100
        status = "ev" if ev_pct >= EV_MIN_EDGE * 100 else "below_threshold"

        results.append(
            {
                **o,
                "fair_odds": f"{fair:.4f}",
                "ev_percent": f"{ev_pct:.2f}%",
                "sharp_count": sharp_count,
                "status": status,
            }
        )

    # Write results
    fieldnames = list(results[0].keys()) if results else []
    if results:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print(f"[OK] Written EV check to {OUTPUT_CSV}")

    # Summary
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("Summary by status:", counts)

    ev_hits = [r for r in results if r.get("status") == "ev"]
    print(f"EV opportunities among outliers: {len(ev_hits)}")
    for r in ev_hits[:10]:
        print(
            f"  {r.get('selection')} @ {r.get('au_book')} {r.get('au_odds')} vs fair {r.get('fair_odds')} -> {r.get('ev_percent')}"
        )


if __name__ == "__main__":
    main()
