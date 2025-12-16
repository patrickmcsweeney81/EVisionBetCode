"""
Filter raw_NFL.csv to keep only markets with opposite outcomes (two-way markets).

For EV calculations, we need both sides:
- Over/Under props: Keep only if both Over AND Under exist for same player/line
- h2h markets: Keep only if both teams exist
- Spreads: Keep only if both teams exist  
- Totals: Keep only if both Over AND Under exist for same line
- Anytime TD: Keep only if both Yes AND No exist for same player
"""
import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/raw_NFL.csv")
OUTPUT_FILE = Path("data/raw_NFL_two_way.csv")
REMOVED_FILE = Path("data/raw_NFL_removed.csv")


def filter_two_way_markets(df):
    """Keep only rows that have opposite outcomes.

    Returns a tuple of (filtered_df, kept_index_list) so callers
    can compute removed rows using original indices.
    """
    keep_rows = []

    # Group by market type
    for (event_id, market, line, player), group in df.groupby(
        ["event_id", "market", "line", "player"], dropna=False
    ):
        selections = set(group["selection"].unique())

        # Check if this group has opposite outcomes
        has_opposite = False

        if market in ["h2h", "spreads"]:
            # For h2h/spreads: need both teams (should be 2 unique selections)
            if len(selections) >= 2:
                has_opposite = True

        elif market == "totals" or market.startswith("player_"):
            # For totals and player props: need both Over and Under
            if "Over" in selections and "Under" in selections:
                has_opposite = True
            # For anytime_td: need both Yes and No
            elif "Yes" in selections and "No" in selections:
                has_opposite = True

        # Keep all rows in this group if it has opposite
        if has_opposite:
            keep_rows.extend(group.index.tolist())

    filtered = df.loc[keep_rows].reset_index(drop=True)
    return filtered, keep_rows


def main():
    print("[FILTER] Keep only two-way markets from raw_NFL.csv")
    print("=" * 60)
    
    # Read input
    df = pd.read_csv(INPUT_FILE)
    print(f"[IN] {len(df)} total rows")
    
    # Show breakdown by market
    print("\nOriginal market breakdown:")
    for market in df["market"].unique():
        count = len(df[df["market"] == market])
        print(f"  {market}: {count} rows")
    
    # Filter
    df_filtered, keep_rows = filter_two_way_markets(df)
    print(f"\n[OUT] {len(df_filtered)} rows with opposite outcomes")
    
    # Get removed rows using original indices
    df_removed = df.drop(index=keep_rows).reset_index(drop=True)
    
    # Show filtered breakdown
    print("\nFiltered market breakdown:")
    for market in df_filtered["market"].unique():
        count = len(df_filtered[df_filtered["market"] == market])
        print(f"  {market}: {count} rows")
    
    # Write output
    df_filtered.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Wrote {len(df_filtered)} rows to {OUTPUT_FILE}")
    
    # Write removed rows
    df_removed.to_csv(REMOVED_FILE, index=False)
    print(f"📝 Wrote {len(df_removed)} incomplete markets to {REMOVED_FILE}")
    
    # Show removed count
    removed = len(df) - len(df_filtered)
    print(f"\n❌ Removed {removed} incomplete markets")


if __name__ == "__main__":
    main()
