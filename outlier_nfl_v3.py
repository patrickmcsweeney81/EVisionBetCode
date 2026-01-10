"""
NFL Odds Spread Outlier Detection
- Flags AU books offering unusually high odds vs sharp median
- Requires >=2 sharp books and >=1 AU book on a line

Usage:
    python outlier_nfl_v3.py

Output:
    data/v3/extracts/NFL_Outliers.csv (or *_new.csv if locked)
"""

import glob
import os

import numpy as np
import pandas as pd

SHARP_BOOKS = [
    "pinnacle",
    "betfair_ex_eu",
    "matchbook",
    "draftkings",
    "fanduel",
    "lowvig",
]
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
ALL_BOOKS = SHARP_BOOKS + AU_BOOKS + [
    "betonlineag",
    "betmgm",
    "betrivers",
    "fanatics",
    "hardrockbet",
    "williamhill_us",
    "bovada",
    "espnbet",
    "coolbet",
    "fliff",
]

OUTLIER_THRESHOLD = 0.02


def detect_odds_outliers(row, sharp_books, au_books):
    sharp_odds = {}
    for book in sharp_books:
        if pd.notna(row[book]):
            try:
                odds = float(row[book])
                sharp_odds[book] = odds
            except Exception:
                pass

    if len(sharp_odds) == 0:
        return {
            "outlier_books": "",
            "median_sharp_odds": np.nan,
            "num_outliers": 0,
            "outlier_details": "",
        }

    median_sharp = np.median(list(sharp_odds.values()))

    au_outliers = []
    for book in au_books:
        if pd.notna(row[book]):
            try:
                odds = float(row[book])
                deviation = (odds - median_sharp) / median_sharp
                if deviation > OUTLIER_THRESHOLD:
                    au_outliers.append({
                        "book": book,
                        "odds": odds,
                        "deviation": deviation,
                    })
            except Exception:
                pass

    outlier_books = ", ".join([o["book"] for o in au_outliers])
    outlier_details = " | ".join(
        [
            f"{o['book']}:{o['odds']:.3f}(+{o['deviation']:.1%})"
            for o in au_outliers
        ]
    )

    return {
        "outlier_books": outlier_books,
        "median_sharp_odds": median_sharp,
        "num_outliers": len(au_outliers),
        "outlier_details": outlier_details,
    }


def detect_nfl_outliers():
    candidates = [
        "data/v3/extracts/NFL_Raw_new.csv",
        "data/v3/extracts/NFL_Raw.csv",
        "data/v3/extracts/football_nfl_raw.csv",
    ]
    latest_csv = next((c for c in candidates if os.path.exists(c)), None)
    if not latest_csv:
        legacy = sorted(glob.glob("data/v3/extracts/football_nfl_raw_*.csv"))
        if legacy:
            latest_csv = legacy[-1]
    if not latest_csv:
        print("❌ No raw NFL CSV found. Run extract_nfl_v3.py first.")
        return

    print(f"📂 Loading raw NFL CSV: {latest_csv}")
    df = pd.read_csv(latest_csv)
    print(f"   Rows: {len(df):,}\n")

    print("🔍 Filtering to lines with 2+ sharp + 1+ AU books...")
    df["num_sharp_books"] = df[SHARP_BOOKS].notna().sum(axis=1)
    df["num_au_books"] = df[AU_BOOKS].notna().sum(axis=1)
    df_filtered = df[
        (df["num_sharp_books"] >= 2) & (df["num_au_books"] >= 1)
    ].copy()
    print(f"   Starting rows: {len(df):,}")
    print(f"   After filtering: {len(df_filtered):,}\n")

    print("📊 Detecting odds spread outliers...")
    df_filtered["outlier_books"] = ""
    df_filtered["median_odds"] = np.nan
    df_filtered["num_outliers"] = 0
    df_filtered["outlier_details"] = ""

    for idx, row in df_filtered.iterrows():
        result = detect_odds_outliers(row, SHARP_BOOKS, AU_BOOKS)
        df_filtered.at[idx, "outlier_books"] = result["outlier_books"]
        df_filtered.at[idx, "median_odds"] = result["median_sharp_odds"]
        df_filtered.at[idx, "num_outliers"] = result["num_outliers"]
        df_filtered.at[idx, "outlier_details"] = result["outlier_details"]
        if (idx + 1) % 500 == 0:
            print(f"   Processed {idx + 1} rows...")

    df_outliers = df_filtered[df_filtered["num_outliers"] > 0].copy()
    print(f"✅ Found {len(df_outliers):,} lines with outliers\n")

    core_cols = [
        "event_id",
        "extracted_at",
        "commence_time",
        "league",
        "event_name",
        "market_type",
        "point",
        "selection",
        "player_name",
    ]
    outlier_cols = [
        "num_outliers",
        "outlier_books",
        "median_odds",
        "outlier_details",
    ]
    bookmaker_cols = [col for col in df_outliers.columns if col in ALL_BOOKS]
    final_cols = core_cols + outlier_cols + bookmaker_cols
    df_output = df_outliers[final_cols].copy()

    df_output["sport"] = "americanfootball_nfl"
    normalized_cols = [
        "sport",
        "event_id",
        "extracted_at",
        "commence_time",
        "league",
        "event_name",
        "market_type",
        "point",
        "selection",
        "player_name",
        "num_outliers",
        "outlier_books",
        "median_odds",
        "outlier_details",
    ]
    normalized_cols = [c for c in normalized_cols if c in df_output.columns]
    normalized_cols_with_books = normalized_cols + [
        col for col in bookmaker_cols if col in df_output.columns
    ]
    df_all = df_output[normalized_cols_with_books].copy()

    os.makedirs("data/v3/extracts", exist_ok=True)
    output_csv = "data/v3/extracts/NFL_Outliers.csv"
    try:
        df_output.to_csv(output_csv, index=False)
    except PermissionError:
        output_csv = "data/v3/extracts/NFL_Outliers_new.csv"
        df_output.to_csv(output_csv, index=False)
        print(f"⚠️  Main file locked by backend, saved to: {output_csv}")
    else:
        print(f"✅ Outlier CSV saved: {output_csv}")

    combined_csv = "data/v3/extracts/AllSports_Outliers.csv"
    try:
        df_all.to_csv(combined_csv, index=False)
    except PermissionError:
        combined_csv = "data/v3/extracts/AllSports_Outliers_new.csv"
        df_all.to_csv(combined_csv, index=False)
        print(f"⚠️  Combined outliers locked, saved to: {combined_csv}")
    else:
        print(f"✅ All-sports Outlier CSV saved: {combined_csv}")

    print(f"   Columns: {len(df_output.columns)}")
    print(f"   Rows: {len(df_output):,}\n")
    print("📊 Outlier Statistics:")
    print(f"   Total outlier occurrences: {df_output['num_outliers'].sum():,}")
    print(f"   Avg outliers per line: {df_output['num_outliers'].mean():.1f}")
    print(f"   Max outliers per line: {df_output['num_outliers'].max()}")

    print("\n📈 Most Common Outlier Books:")
    all_outliers = []
    for books_str in df_output["outlier_books"].dropna():
        if books_str:
            all_outliers.extend([b.strip() for b in books_str.split(",")])
    from collections import Counter

    top_books = Counter(all_outliers)
    for book, count in top_books.most_common(10):
        print(f"   {book}: {count} times")
    return output_csv


if __name__ == "__main__":
    detect_nfl_outliers()
