"""
AFL V3 Data Filtering (mirrors NFL/NBA V3 composite pairing)
- Normalizes market names (align alternates to base types)
- Drops whole-number spreads/totals (keeps .5)
- Requires 1+ sharp book AND 1+ AU book
- Assigns pair_id using composite-key pairing (event, market, point, player)

Usage:
    python filter_afl_v3.py

Output:
    data/v3/extracts/AFL_Filtered.csv (or *_new.csv if locked)
"""

import glob
import os

import pandas as pd


TWO_WAY_MARKETS = {
    "totals": {"Over": "Under", "Under": "Over"},
    "spreads": "pair_with_other_team",
    "h2h": "pair_with_other_team",
    "h2h_lay": "pair_with_other_team",
}


def is_2way_market(market_type: str) -> bool:
    return market_type in TWO_WAY_MARKETS


def filter_afl_data():
    candidates = [
        "data/v3/extracts/AFL_Raw_new.csv",
        "data/v3/extracts/AFL_Raw.csv",
        "data/v3/extracts/aussierules_afl_raw.csv",
    ]

    if not any(os.path.exists(c) for c in candidates):
        legacy = sorted(
            glob.glob("data/v3/extracts/aussierules_afl_raw_*.csv")
        )
        if legacy:
            candidates.append(legacy[-1])

    latest_raw_csv = next((c for c in candidates if os.path.exists(c)), None)
    if not latest_raw_csv:
        print("[ERROR] No AFL_Raw CSV files found in data/v3/extracts/")
        return

    print(f"[*] Loading AFL_Raw: {latest_raw_csv}")
    df = pd.read_csv(latest_raw_csv)
    print(f"   Starting rows: {len(df):,}")

    # Ensure point is numeric for spreads/totals math; non-numeric -> NaN
    if "point" in df.columns:
        df["point"] = pd.to_numeric(df["point"], errors="coerce")

    # Normalize market names (align alternates to base types)
    market_normalization = {
        "alternate_spreads": "spreads",
        "alternate_totals": "totals",
    }
    df["market_type"] = df["market_type"].map(
        lambda x: market_normalization.get(x, x)
    )
    print(f"[OK] After normalizing market names: {len(df):,} rows")

    # Remove whole-number spreads/totals
    spread_total_rows = df[~df["market_type"].isin(["spreads", "totals"])]
    spreads_totals = df[df["market_type"].isin(["spreads", "totals"])].copy()

    spreads_totals["is_half"] = spreads_totals["point"].fillna(0) % 1 != 0
    spreads_totals = spreads_totals[spreads_totals["is_half"]]
    spreads_totals = spreads_totals.drop("is_half", axis=1)

    df = pd.concat([spread_total_rows, spreads_totals], ignore_index=True)
    print(f"[OK] After removing whole number spreads/totals: {len(df):,} rows")

    sharp_books = [
        "pinnacle",
        "betfair_ex_eu",
        "matchbook",
        "draftkings",
        "fanduel",
        "lowvig",
    ]
    df["has_sharp_book"] = df[sharp_books].notna().any(axis=1)
    df = df[df["has_sharp_book"]]
    df = df.drop("has_sharp_book", axis=1)
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
    df = df[df["has_au_book"]]
    df = df.drop("has_au_book", axis=1)
    print(f"[OK] After keeping only lines with AU books: {len(df):,} rows")

    # FILTER 4B: Split lines by 4-star sharp book count
    four_star_books = sharp_books
    df["sharp_count"] = df[four_star_books].notna().sum(axis=1)

    # Save lines with <2 sharps to Push_Vig
    push_vig_low_sharps = df[df["sharp_count"] < 2].drop("sharp_count", axis=1)
    if not push_vig_low_sharps.empty:
        push_vig_csv = "data/v3/extracts/Push_Vig_markets.csv"
        try:
            push_vig_low_sharps.to_csv(push_vig_csv, index=False)
        except PermissionError:
            push_vig_csv = "data/v3/extracts/Push_Vig_markets_new.csv"
            push_vig_low_sharps.to_csv(push_vig_csv, index=False)
        print(
            (
                "[INFO] Saved "
                f"{len(push_vig_low_sharps):,} lines with <2 4-star sharps "
                f"to: {push_vig_csv}"
            )
        )

    # Keep only lines with >=2 4-star sharps for main output
    df = df[df["sharp_count"] >= 2].drop("sharp_count", axis=1)
    print(f"[OK] After filtering for >=2 4-star sharps: {len(df):,} rows")

    df = df.drop_duplicates(
        subset=[
            "event_name",
            "market_type",
            "selection",
            "point",
            "player_name",
        ],
        keep="first",
    )
    print(f"[OK] After removing all duplicate bets: {len(df):,} rows")

    def assign_pair_ids_composite_key(df_full: pd.DataFrame) -> pd.DataFrame:
        df_full = df_full.copy()
        df_full["pair_id"] = None
        pair_counter = 0

        # Spreads: group by (event, spreads, |point|)
        # and pick one (-) + one (+)
        if "spreads" in df_full["market_type"].values:
            spreads_df = df_full[df_full["market_type"] == "spreads"].copy()
            spreads_df["abs_point"] = spreads_df["point"].abs()

            for (
                _event,
                _market,
                _abs_point,
            ), group_indices in spreads_df.groupby(
                ["event_name", "market_type", "abs_point"], dropna=False
            ).groups.items():
                group = spreads_df.loc[group_indices].copy()
                rows_neg = group[group["point"] < 0]
                rows_pos = group[group["point"] > 0]
                if rows_neg.empty or rows_pos.empty:
                    continue

                for _, neg_row in rows_neg.iterrows():
                    pos_match = rows_pos[
                        rows_pos["selection"] != neg_row["selection"]
                    ]
                    if not pos_match.empty:
                        pos_row = pos_match.iloc[0]
                        df_full.loc[neg_row.name, "pair_id"] = pair_counter
                        df_full.loc[pos_row.name, "pair_id"] = pair_counter
                        pair_counter += 1
                        break

        # Other 2-way markets: group by exact (event, market, point, player)
        non_spreads = df_full[df_full["market_type"] != "spreads"]
        key_groups = non_spreads.groupby(
            ["event_name", "market_type", "point", "player_name"], dropna=False
        )
        for (
            _event,
            market,
            _point,
            _player,
        ), group_indices in key_groups.groups.items():
            if not is_2way_market(market):
                continue

            group = df_full.loc[group_indices].copy()
            selections = group["selection"].unique()
            if len(selections) == 2:
                selection_1, selection_2 = selections[0], selections[1]
                indices_1 = group_indices[
                    group["selection"] == selection_1
                ].tolist()
                indices_2 = group_indices[
                    group["selection"] == selection_2
                ].tolist()
                df_full.loc[indices_1, "pair_id"] = pair_counter
                df_full.loc[indices_2, "pair_id"] = pair_counter
                pair_counter += 1

        return df_full

    df = assign_pair_ids_composite_key(df)
    print(f"[OK] After assigning pair_ids (Composite Key): {len(df):,} rows")

    print("\n[VALIDATION] Checking pairing integrity...")
    paired_df = df[df["pair_id"].notna()].copy()
    pair_violations = []

    for pair_id, group in paired_df.groupby("pair_id"):
        market_type = group["market_type"].iloc[0]
        if market_type == "spreads":
            if len(group) < 2:
                pair_violations.append(
                    f"Pair {pair_id}: {len(group)} rows (expected 2+)"
                )
        else:
            if len(group) != 2:
                pair_violations.append(
                    f"Pair {pair_id}: {len(group)} rows (expected 2)"
                )

        if group["event_name"].nunique() > 1:
            pair_violations.append(
                (
                    f"Pair {pair_id}: Mixed events "
                    f"{group['event_name'].unique().tolist()}"
                )
            )
        if group["market_type"].nunique() > 1:
            pair_violations.append(
                (
                    f"Pair {pair_id}: Mixed markets "
                    f"{group['market_type'].unique().tolist()}"
                )
            )
        if market_type != "spreads" and group["point"].nunique() > 1:
            pair_violations.append(
                (
                    f"Pair {pair_id}: Mixed points "
                    f"{group['point'].unique().tolist()}"
                )
            )
        if group["player_name"].nunique() > 1:
            pair_violations.append(
                (
                    f"Pair {pair_id}: Mixed players "
                    f"{group['player_name'].unique().tolist()}"
                )
            )

        selections = group["selection"].unique()
        if len(selections) < 2:
            pair_violations.append(
                (
                    f"Pair {pair_id}: Only {len(selections)} selection "
                    "(expected 2)"
                )
            )

    if pair_violations:
        print(f"[WARN] Found {len(pair_violations)} violations:")
        for v in pair_violations[:10]:
            print(f"   - {v}")
    else:
        print("[OK] All pairs valid")

    # FILTER: Split paired + >=2 4-star sharps → main filtered; else → Push_Vig
    df["sharp_book_count"] = df[four_star_books].notna().sum(axis=1)

    main_df = df[(df["pair_id"].notna()) & (df["sharp_book_count"] >= 2)]
    vig_df = df[(df["pair_id"].isna()) | (df["sharp_book_count"] < 2)]

    os.makedirs("data/v3/extracts", exist_ok=True)

    if not vig_df.empty:
        vig_csv = "data/v3/extracts/Push_Vig_markets.csv"
        vig_df_out = vig_df.drop("sharp_book_count", axis=1)
        try:
            vig_df_out.to_csv(vig_csv, index=False)
        except PermissionError:
            vig_csv = "data/v3/extracts/Push_Vig_markets_new.csv"
            vig_df_out.to_csv(vig_csv, index=False)
        print(
            (
                "[INFO] Saved "
                f"{len(vig_df):,} unpaired/low-sharp lines to: {vig_csv}"
            )
        )

    output_csv = "data/v3/extracts/AFL_Filtered.csv"
    main_df_out = main_df.drop("sharp_book_count", axis=1)
    try:
        main_df_out.to_csv(output_csv, index=False)
    except PermissionError:
        output_csv = "data/v3/extracts/AFL_Filtered_new.csv"
        main_df_out.to_csv(output_csv, index=False)
        print(f"[WARN] Main AFL_Filtered locked; saved to {output_csv}")
    else:
        print(f"[OK] AFL_Filtered CSV saved: {output_csv}")

    print(f"   Final rows: {len(main_df):,}")
    print("\nMarket breakdown:")
    print(main_df["market_type"].value_counts())
    return output_csv


if __name__ == "__main__":
    filter_afl_data()
