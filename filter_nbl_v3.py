"""
NBL V3 Data Filtering
======================
Filters extracted NBL odds CSV to include only desired markets and formats.

Usage:
    python filter_nbl_v3.py

Output:
    data/v3/extracts/NBL_Filtered.csv (or NBL_Filtered_new.csv if locked)
"""

import glob
import os

import pandas as pd


# 2-way market definitions
TWO_WAY_MARKETS = {
    "totals": {"Over": "Under", "Under": "Over"},
    "spreads": "pair_with_other_team",
    "h2h": "pair_with_other_team",
    "h2h_lay": "pair_with_other_team",
}


def is_2way_market(market_type):
    """Check if market is 2-way."""
    return market_type in TWO_WAY_MARKETS


def filter_nbl_data():
    """Load latest NBL_Raw CSV and create NBL_Filtered CSV with filters applied."""

    candidates = [
        "data/v3/extracts/NBL_Raw_new.csv",
        "data/v3/extracts/NBL_Raw.csv",
        "data/v3/extracts/basketball_nbl_raw.csv",
    ]

    if not any(os.path.exists(c) for c in candidates):
        legacy = sorted(glob.glob("data/v3/extracts/basketball_nbl_raw_*.csv"))
        if legacy:
            candidates.append(legacy[-1])

    latest_raw_csv = next((c for c in candidates if os.path.exists(c)), None)
    if not latest_raw_csv:
        print("[ERROR] No NBL_Raw CSV files found in data/v3/extracts/")
        return

    print(f"[*] Loading NBL_Raw: {latest_raw_csv}")
    df = pd.read_csv(latest_raw_csv)
    print(f"   Starting rows: {len(df):,}")

    # Normalize market names - consolidate alternates by base market type
    market_normalization = {
        "alternate_spreads": "spreads",
        "alternate_totals": "totals",
    }
    df["market_type"] = df["market_type"].map(
        lambda x: market_normalization.get(x, x)
    )
    print(f"[OK] After normalizing market names: {len(df):,} rows")

    # Split whole number vs half-point spreads/totals
    spread_total_rows = df[~df["market_type"].isin(["spreads", "totals"])].copy()

    spreads_totals = df[df["market_type"].isin(["spreads", "totals"])].copy()
    spreads_totals["is_half"] = spreads_totals["point"].fillna(0) % 1 != 0

    whole_numbers = spreads_totals[~spreads_totals["is_half"]].drop("is_half", axis=1)
    if not whole_numbers.empty:
        push_vig_csv = "data/v3/extracts/Push_Vig_markets.csv"
        try:
            whole_numbers.to_csv(push_vig_csv, index=False)
        except PermissionError:
            push_vig_csv = "data/v3/extracts/Push_Vig_markets_new.csv"
            whole_numbers.to_csv(push_vig_csv, index=False)
        print(
            f"[INFO] Saved {len(whole_numbers):,} whole number lines to: {push_vig_csv}"
        )

    spreads_totals = spreads_totals[spreads_totals["is_half"]].drop("is_half", axis=1)

    df = pd.concat([spread_total_rows, spreads_totals], ignore_index=True)
    print(
        f"[OK] After splitting whole/half spreads/totals: {len(df):,} rows (half-point only)"
    )

    sharp_books_4star = [
        "pinnacle",
        "betfair_ex_eu",
        "matchbook",
        "draftkings",
        "fanduel",
        "lowvig",
    ]
    sharp_books_3star = [
        "betonlineag",
        "betmgm",
        "betrivers",
        "fanatics",
    ]
    sharp_books = sharp_books_4star + sharp_books_3star

    df["has_sharp_book"] = df[sharp_books].notna().any(axis=1)
    df = df[df["has_sharp_book"]].drop("has_sharp_book", axis=1)
    print(f"[OK] After keeping only lines with sharp books: {len(df):,} rows")

    au_books = [
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
    df["has_au_book"] = df[au_books].notna().any(axis=1)
    df = df[df["has_au_book"]].drop("has_au_book", axis=1)
    print(f"[OK] After keeping only lines with AU books: {len(df):,} rows")

    # Require >=2 sharps (3⭐/4⭐) for fair-odds stability
    df["sharp_count"] = df[sharp_books].notna().sum(axis=1)

    push_vig_low_sharps = df[df["sharp_count"] < 2].drop("sharp_count", axis=1)
    if not push_vig_low_sharps.empty:
        push_vig_csv = "data/v3/extracts/Push_Vig_markets.csv"
        try:
            push_vig_low_sharps.to_csv(push_vig_csv, index=False)
        except PermissionError:
            push_vig_csv = "data/v3/extracts/Push_Vig_markets_new.csv"
            push_vig_low_sharps.to_csv(push_vig_csv, index=False)
        print(
            f"[INFO] Saved {len(push_vig_low_sharps):,} lines with <2 sharps to: {push_vig_csv}"
        )

    df = df[df["sharp_count"] >= 2].drop("sharp_count", axis=1)
    print(f"[OK] After filtering for >=2 sharps: {len(df):,} rows")

    # Deduplicate
    df = df.drop_duplicates(
        subset=["event_name", "market_type", "selection", "point", "player_name"],
        keep="first",
    )
    print(f"[OK] After removing all duplicate bets: {len(df):,} rows")

    # Assign pair_ids (Composite Key)
    df_full = df.copy()
    df_full["pair_id"] = None

    pair_counter = 0

    # Spreads: group by abs(point) and choose one + and one - for different teams
    if "spreads" in df_full["market_type"].values:
        spreads_df = df_full[df_full["market_type"] == "spreads"].copy()
        spreads_df["abs_point"] = spreads_df["point"].abs()

        for (_, _, _abs_point), group_indices in spreads_df.groupby(
            ["event_name", "market_type", "abs_point"], dropna=False
        ).groups.items():
            group = spreads_df.loc[group_indices].copy()
            rows_neg = group[group["point"] < 0]
            rows_pos = group[group["point"] > 0]
            if rows_neg.empty or rows_pos.empty:
                continue

            paired = False
            for _, neg_row in rows_neg.iterrows():
                pos_match = rows_pos[rows_pos["selection"] != neg_row["selection"]]
                if not pos_match.empty:
                    pos_row = pos_match.iloc[0]
                    df_full.loc[neg_row.name, "pair_id"] = pair_counter
                    df_full.loc[pos_row.name, "pair_id"] = pair_counter
                    pair_counter += 1
                    paired = True
                    break
            if not paired:
                continue

    # Totals & h2h: group by (event, market, point, player_name)
    non_spreads = df_full[df_full["market_type"] != "spreads"]
    key_groups = non_spreads.groupby(
        ["event_name", "market_type", "point", "player_name"], dropna=False
    )

    for (_event, market, _point, _player), group_indices in key_groups.groups.items():
        group = df_full.loc[group_indices].copy()
        if not is_2way_market(market):
            continue

        selections = group["selection"].unique()
        if len(selections) != 2:
            continue

        df_full.loc[group_indices, "pair_id"] = pair_counter
        pair_counter += 1

    df = df_full

    print("\n[VALIDATION] Checking pairing integrity...")
    if df["pair_id"].notna().any():
        print("[OK] Pairing completed")

    # Save
    output_csv = "data/v3/extracts/NBL_Filtered.csv"
    os.makedirs("data/v3/extracts", exist_ok=True)
    try:
        df.to_csv(output_csv, index=False)
    except PermissionError:
        output_csv = "data/v3/extracts/NBL_Filtered_new.csv"
        df.to_csv(output_csv, index=False)
        print(f"⚠️  Main file locked by backend, saved to: {output_csv}")

    print(f"[OK] NBL_Filtered CSV saved: {output_csv}")
    print(f"   Final rows: {len(df):,}")


if __name__ == "__main__":
    filter_nbl_data()
