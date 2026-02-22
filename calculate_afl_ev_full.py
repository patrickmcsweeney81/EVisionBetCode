"""AFL Fair Price & EV Calculation - FULL ANALYSIS VERSION (WITH DE-VIGGING)

This is a thin AFL wrapper around the shared fair-odds/EV logic used by
`calculate_nfl_ev_full.py`.

Usage:
    python calculate_afl_ev_full.py

Output:
    data/v3/extracts/AFL_EV.csv
    data/v3/extracts/AllSports_EV.csv (merged)
"""

import glob
import os
import subprocess
import sys

import pandas as pd

from calculate_nfl_ev_full import (
    AU_BOOKS,
    FAIR_ODDS_BOOKS,
    calculate_best_au_odds,
    calculate_ev,
    calculate_fair_odds_fast,
    count_available_books,
    get_best_au_bookmaker,
)


BOOKMAKERS_IN_CSV = [
    # 4⭐ SHARPS
    "pinnacle",
    "betfair_ex_eu",
    "matchbook",
    "draftkings",
    "fanduel",
    "lowvig",
    # 0⭐ AU TARGETS
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
    # 3⭐ SHARPS
    "betonlineag",
    "betmgm",
    "betrivers",
    "fanatics",
    # 2⭐ DECENT
    "hardrockbet",
    "williamhill_us",
    "bovada",
    "espnbet",
    # 1⭐ SOFT
    "coolbet",
    "fliff",
]


def calculate_afl_ev_full():
    print("[INIT] EV Calculation Pipeline for AFL")
    print()

    print("[MANAGE] Archiving previous runs and cleaning up old files...")
    try:
        result = subprocess.run(
            [sys.executable, "manage_allsports_ev.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            print(f"[WARN] Management script error: {result.stderr}")
    except Exception as e:
        print(f"[WARN] Could not run management script: {e}")
    print()

    candidates = [
        "data/v3/extracts/AFL_Filtered_new.csv",
        "data/v3/extracts/AFL_Filtered.csv",
    ]
    filtered_csv = next((c for c in candidates if os.path.exists(c)), None)
    if not filtered_csv:
        legacy = sorted(glob.glob("data/v3/extracts/AFL_Filtered*.csv"))
        if legacy:
            filtered_csv = legacy[-1]

    if not filtered_csv:
        print("[ERROR] No filtered AFL CSV found. Run filter_afl_v3.py first.")
        return

    print(f"[*] Loading filtered CSV: {filtered_csv}")
    df = pd.read_csv(filtered_csv)
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}\n")

    # Ensure all needed bookmaker columns exist to avoid KeyErrors
    required_books = set(FAIR_ODDS_BOOKS + AU_BOOKS)
    for book in required_books:
        if book not in df.columns:
            df[book] = pd.NA

    print("[PREP] Building pair_id lookup table...")
    pair_lookup: dict = {}
    for idx, row in df.iterrows():
        pair_id = row.get("pair_id")
        if pd.notna(pair_id):
            pair_lookup.setdefault(pair_id, []).append(idx)
    print(f"[OK] Pair lookup built: {len(pair_lookup):,} unique pairs\n")

    print(
        "[CALC] Calculating fair odds and EV "
        "(with de-vigging for 2-way markets)..."
    )

    fair_odds_list = []
    uses_devig_list = []

    for idx, row in df.iterrows():
        fair_odds, uses_devig = calculate_fair_odds_fast(row, df, pair_lookup)
        fair_odds_list.append(fair_odds)
        uses_devig_list.append(uses_devig)

        if (idx + 1) % 2000 == 0:
            print(f"  ... processed {idx + 1:,} / {len(df):,} rows")

    df["fair_odds_decimal"] = [round(x, 2) for x in fair_odds_list]
    df["uses_devig"] = uses_devig_list

    df["best_au_odds_decimal"] = df.apply(calculate_best_au_odds, axis=1)
    df["best_au_bookmaker"] = df.apply(get_best_au_bookmaker, axis=1)
    df["ev_percent"] = df.apply(
        lambda r: calculate_ev(
            r["fair_odds_decimal"],
            r["best_au_odds_decimal"],
        ),
        axis=1,
    )
    df["ev_percent"] = df["ev_percent"].round(2)

    df["total_books"] = df.apply(
        lambda r: count_available_books(r, BOOKMAKERS_IN_CSV), axis=1
    )

    valid_evs = df["ev_percent"].notna().sum()
    print(f"[OK] Calculated EV for {valid_evs:,} rows\n")

    # All-sports format (consistent with other *_EV.csv files)
    df_all = df.copy()
    df_all["sport"] = "aussierules_afl"

    core_cols = [
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
        "pair_id",
        "best_au_bookmaker",
        "best_au_odds_decimal",
        "ev_percent",
        "fair_odds_decimal",
        "total_books",
        "uses_devig",
    ]
    core_cols = [c for c in core_cols if c in df_all.columns]

    bookmaker_cols = [c for c in BOOKMAKERS_IN_CSV if c in df_all.columns]
    df_all_output = df_all[core_cols + bookmaker_cols].copy()

    os.makedirs("data/v3/extracts", exist_ok=True)
    afl_ev = "data/v3/extracts/AFL_EV.csv"
    afl_ev_fallback = "data/v3/extracts/AFL_EV_new.csv"

    try:
        df_all_output.to_csv(afl_ev, index=False)
        print(f"[OK] AFL_EV.csv saved: {len(df_all_output):,} rows")
    except PermissionError:
        df_all_output.to_csv(afl_ev_fallback, index=False)
        afl_ev = afl_ev_fallback
        print(f"[WARN] AFL_EV.csv locked, saved to: {afl_ev_fallback}")

    all_sports_ev = "data/v3/extracts/AllSports_EV.csv"

    ev_candidates = [
        f
        for f in glob.glob("data/v3/extracts/*_EV*.csv")
        if not os.path.basename(f).startswith("AllSports_EV")
    ]

    ev_by_sport: dict[str, str] = {}
    for f in ev_candidates:
        sport_key = os.path.basename(f).split("_EV")[0]
        if sport_key not in ev_by_sport or (
            os.path.getmtime(f) > os.path.getmtime(ev_by_sport[sport_key])
        ):
            ev_by_sport[sport_key] = f

    ev_files = sorted(ev_by_sport.values())
    if ev_files:
        dfs = []
        sport_map = {
            "NBA": "basketball_nba",
            "NFL": "americanfootball_nfl",
            "NBL": "basketball_nbl",
            "AFL": "aussierules_afl",
        }
        for f in ev_files:
            try:
                df_s = pd.read_csv(f)
                if "sport" not in df_s.columns:
                    sport_key = os.path.basename(f).split("_EV")[0]
                    df_s["sport"] = sport_map.get(sport_key, sport_key.lower())
                dfs.append(df_s)
            except Exception:
                pass

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            combined.to_csv(all_sports_ev, index=False)
            print(
                f"[OK] AllSports_EV merged: {len(combined):,} rows "
                f"({combined['sport'].nunique()} sports)"
            )

    return afl_ev


if __name__ == "__main__":
    calculate_afl_ev_full()
