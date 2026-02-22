""" 
NBL Fair Price & EV Calculation - FULL ANALYSIS VERSION (WITH DE-VIGGING)
==========================================================================

This mirrors the NBA/NFL V3 EV calculation, but targets NBL input/output files.

Usage:
    python calculate_nbl_ev_full.py

Output:
    data/v3/extracts/NBL_EV.csv (or *_new.csv if locked)
    data/v3/extracts/AllSports_EV.csv (merged)
"""

import glob
import os
import subprocess
import sys

import numpy as np
import pandas as pd

# Bookmaker groupings for fair odds calculation
SHARP_BOOKS_4STAR = [
    "pinnacle",
    "betfair_ex_eu",
    "matchbook",
    "draftkings",
    "fanduel",
    "lowvig",
]
SHARP_BOOKS_3STAR = ["betonlineag", "betmgm", "betrivers", "fanatics"]
SOFT_BOOKS_2STAR = ["hardrockbet", "williamhill_us", "bovada", "espnbet"]
SOFT_BOOKS_1STAR = ["coolbet", "fliff"]

FAIR_ODDS_BOOKS = (
    SHARP_BOOKS_4STAR + SHARP_BOOKS_3STAR + SOFT_BOOKS_2STAR + SOFT_BOOKS_1STAR
)

AU_BOOKS = [
    "bet365",
    "betfair_ex_au",
    "sportsbet",
    "dabble_au",
    "pointsbetau",
    "neds",
    "ladbrokes_au",
    "unibet",
    "betright",
    "betr_au",
    "boombet",
    "playup",
    "tab",
    "tabtouch",
]

BOOK_WEIGHTS = {}
for book in SHARP_BOOKS_4STAR:
    BOOK_WEIGHTS[book] = 1.5
for book in SHARP_BOOKS_3STAR:
    BOOK_WEIGHTS[book] = 1.0
for book in SOFT_BOOKS_2STAR:
    BOOK_WEIGHTS[book] = 0.75
for book in SOFT_BOOKS_1STAR:
    BOOK_WEIGHTS[book] = 0.5
for book in AU_BOOKS:
    BOOK_WEIGHTS[book] = 0

TWO_WAY_MARKETS = {
    "totals": {"Over": "Under", "Under": "Over"},
    "spreads": "pair_with_other_team",
    "h2h": "pair_with_other_team",
    "h2h_lay": "pair_with_other_team",
    "alternate_spreads": "pair_with_other_team",
    "alternate_totals": {"Over": "Under", "Under": "Over"},
}


def is_2way_market(market_type: str) -> bool:
    return market_type in TWO_WAY_MARKETS


def get_opposite_selection(market_type: str, selection: str) -> str | None:
    mapping = TWO_WAY_MARKETS.get(market_type)
    if isinstance(mapping, dict):
        return mapping.get(selection)
    return None


def american_to_decimal(odds):
    """Convert odds to decimal if needed; pass through decimal strings/numbers."""
    if odds is None or (isinstance(odds, float) and np.isnan(odds)):
        return None
    try:
        o = float(odds)
        if o >= 1.01 and o < 1000:
            return o
    except Exception:
        return None
    return None


def devig_two_way(odds_a: float, odds_b: float) -> tuple[float, float] | tuple[None, None]:
    """Simple 2-way de-vig (normalized implied probabilities)."""
    if not odds_a or not odds_b:
        return (None, None)
    pa = 1.0 / odds_a
    pb = 1.0 / odds_b
    total = pa + pb
    if total <= 0:
        return (None, None)
    return (pa / total, pb / total)


def weighted_consensus_probability(prob_by_book: dict[str, float]) -> float | None:
    if not prob_by_book:
        return None

    weighted_sum = 0.0
    weight_total = 0.0
    for book, prob in prob_by_book.items():
        w = BOOK_WEIGHTS.get(book, 0)
        if w <= 0:
            continue
        weighted_sum += w * prob
        weight_total += w

    if weight_total <= 0:
        return None

    return weighted_sum / weight_total


def best_au_price(row: pd.Series) -> tuple[float | None, str]:
    """Pick best (max) AU odds for this line."""

    best_odds = None
    best_book = ""
    for book in AU_BOOKS:
        if pd.notna(row.get(book)):
            dec = american_to_decimal(row.get(book))
            if dec is None:
                continue
            if best_odds is None or dec > best_odds:
                best_odds = dec
                best_book = book
    return best_odds, best_book


def compute_pair_fair_odds(
    row_a: pd.Series,
    row_b: pd.Series,
) -> tuple[float | None, float | None]:
    """Compute fair odds for both sides of a 2-way market using per-book de-vig."""

    probs_a = {}
    probs_b = {}
    for book in FAIR_ODDS_BOOKS:
        if pd.notna(row_a.get(book)) and pd.notna(row_b.get(book)):
            oa = american_to_decimal(row_a.get(book))
            ob = american_to_decimal(row_b.get(book))
            if not oa or not ob:
                continue

            pa, pb = devig_two_way(oa, ob)
            if pa is None or pb is None:
                continue

            probs_a[book] = pa
            probs_b[book] = pb

    fair_pa = weighted_consensus_probability(probs_a)
    fair_pb = weighted_consensus_probability(probs_b)
    if fair_pa is None or fair_pb is None:
        return (None, None)

    total = fair_pa + fair_pb
    if total <= 0:
        return (None, None)

    fair_pa /= total
    fair_pb /= total
    if fair_pa <= 0 or fair_pb <= 0:
        return (None, None)

    return (1.0 / fair_pa, 1.0 / fair_pb)


def get_latest_filtered_csv() -> str | None:
    candidates = [
        "data/v3/extracts/NBL_Filtered_new.csv",
        "data/v3/extracts/NBL_Filtered.csv",
        "data/v3/extracts/basketball_nbl_filtered.csv",
    ]
    latest = next((c for c in candidates if os.path.exists(c)), None)
    if latest:
        return latest
    legacy = sorted(glob.glob("data/v3/extracts/basketball_nbl_filtered_*.csv"))
    return legacy[-1] if legacy else None


def merge_allsports_ev():
    ev_candidates = [
        f
        for f in glob.glob("data/v3/extracts/*_EV*.csv")
        if not os.path.basename(f).startswith("AllSports_EV")
    ]

    ev_by_sport = {}
    for f in ev_candidates:
        sport_key = os.path.basename(f).split("_EV")[0]
        if sport_key not in ev_by_sport or os.path.getmtime(f) > os.path.getmtime(
            ev_by_sport[sport_key]
        ):
            ev_by_sport[sport_key] = f

    ev_files = sorted(ev_by_sport.values())
    if not ev_files:
        print("[ERROR] No EV CSV files found to merge")
        return

    sport_map = {
        "NBA": "basketball_nba",
        "NFL": "americanfootball_nfl",
        "NBL": "basketball_nbl",
    }

    dfs = []
    for file_path in ev_files:
        df = pd.read_csv(file_path)
        sport = os.path.basename(file_path).split("_")[0]
        if "sport" not in df.columns:
            df["sport"] = sport_map.get(sport, sport.lower())
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    allsports_ev = "data/v3/extracts/AllSports_EV.csv"
    combined.to_csv(allsports_ev, index=False)
    print(
        f"[OK] AllSports_EV merged: {len(combined):,} rows ({combined['sport'].nunique()} sports)"
    )


def main():
    print("[INIT] EV Calculation Pipeline for NBL")

    latest_filtered = get_latest_filtered_csv()
    if not latest_filtered:
        print("❌ No filtered NBL CSV found. Run filter_nbl_v3.py first.")
        return

    print(f"[*] Loading filtered CSV: {latest_filtered}")
    df = pd.read_csv(latest_filtered)
    print(f"   Rows: {len(df):,}")

    if "pair_id" not in df.columns:
        print("❌ Missing pair_id column in NBL filtered CSV")
        return

    print("[CALC] Calculating fair odds and EV (pair-based de-vig)...")

    df["fair_odds_decimal"] = np.nan
    df["best_au_odds_decimal"] = np.nan
    df["best_au_bookmaker"] = ""
    df["ev_percent"] = np.nan
    df["uses_devig"] = False
    df["total_books"] = 0

    all_books_for_count = list(dict.fromkeys(FAIR_ODDS_BOOKS + AU_BOOKS))

    processed_pairs = 0
    for pair_id, group in df.groupby("pair_id", dropna=False):
        if pd.isna(pair_id):
            continue

        market_type = str(group["market_type"].iloc[0])
        if market_type not in TWO_WAY_MARKETS:
            continue

        selections = list(group["selection"].dropna().unique())
        if len(selections) != 2:
            continue

        row_a = group[group["selection"] == selections[0]].iloc[0]
        row_b = group[group["selection"] == selections[1]].iloc[0]

        fair_odds_a, fair_odds_b = compute_pair_fair_odds(row_a, row_b)
        if fair_odds_a is None or fair_odds_b is None:
            continue

        for idx, row in group.iterrows():
            best_au, best_book = best_au_price(row)
            if best_au is None:
                continue

            fair_odds = fair_odds_a if row["selection"] == selections[0] else fair_odds_b
            ev_percent = ((best_au / fair_odds) - 1.0) * 100.0

            df.at[idx, "fair_odds_decimal"] = fair_odds
            df.at[idx, "best_au_odds_decimal"] = best_au
            df.at[idx, "best_au_bookmaker"] = best_book
            df.at[idx, "ev_percent"] = ev_percent
            df.at[idx, "uses_devig"] = True
            df.at[idx, "total_books"] = int(row[all_books_for_count].notna().sum())

        processed_pairs += 1
        if processed_pairs % 250 == 0:
            print(f"  ... processed {processed_pairs:,} pairs")

    # Percent precision rule
    if "ev_percent" in df.columns:
        df["ev_percent"] = pd.to_numeric(df["ev_percent"], errors="coerce").round(2)

    output_csv = "data/v3/extracts/NBL_EV.csv"
    os.makedirs("data/v3/extracts", exist_ok=True)
    try:
        df.to_csv(output_csv, index=False)
    except PermissionError:
        output_csv = "data/v3/extracts/NBL_EV_new.csv"
        df.to_csv(output_csv, index=False)
        print(f"⚠️  Main file locked by backend, saved to: {output_csv}")
    else:
        print(f"[OK] NBL_EV.csv saved: {len(df):,} rows")

    # Merge AllSports
    merge_allsports_ev()

    # Generate Pats Picks if available
    try:
        subprocess.run(
            [sys.executable, "generate_pats_picks.py"],
            check=False,
            capture_output=False,
            text=True,
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()
