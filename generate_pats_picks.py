"""
Generate Pats_Picks.csv from AllSports_EV.csv
Custom filtering and column selection for betting analysis.

Usage:
    python generate_pats_picks.py
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path


def calculate_kelly(row):
    """Calculate full Kelly bet size for $1000 bankroll."""
    fair_odds = row['fair_odds_decimal']
    best_odds = row['best_au_odds_decimal']
    
    if pd.isna(fair_odds) or pd.isna(best_odds) or fair_odds <= 1 or best_odds <= 1:
        return np.nan
    
    # Kelly formula: K = (bp - q) / b
    # where b = net odds, p = fair prob, q = 1 - p
    fair_prob = 1 / fair_odds
    net_odds = best_odds - 1
    
    if net_odds <= 0:
        return np.nan
    
    kelly_fraction = ((best_odds * fair_prob) - 1) / net_odds
    
    # Bet size for $1000 bankroll
    bankroll = 1000
    bet_size = bankroll * kelly_fraction
    
    # Don't allow negative bets
    return max(0, bet_size)


def generate_pats_picks():
    """Generate Pats_Picks.csv from AllSports_EV.csv."""
    
    # Prefer the current run output (AllSports_EV.csv) and its lock fallback.
    # Dated archive files (AllSports_EV_*.csv) are append-only history and can
    # contain older rows.
    data_dir = Path("data/v3/extracts")
    preferred_inputs = [
        data_dir / "AllSports_EV.csv",
        data_dir / "AllSports_EV_new.csv",
    ]
    input_csv = next(
        (p for p in preferred_inputs if p.exists() and p.stat().st_size > 0),
        None,
    )

    if input_csv is None:
        ev_candidates = list(data_dir.glob("AllSports_EV*.csv"))
        if not ev_candidates:
            print(
                f"[ERROR] No AllSports_EV*.csv found in {data_dir}. "
                "Run orchestrate_pipeline.py or calculate_*_ev_full.py first."
            )
            return

        input_csv = max(ev_candidates, key=lambda p: p.stat().st_mtime)
        print(f"[WARN] Using fallback EV file: {input_csv.name}")

    print(f"[*] Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    
    # Filter to positive EV only
    print("\n[FILTER] Keeping only positive EV bets...")
    df = df[df['ev_percent'] > 0].copy()
    print(f"   Positive EV rows: {len(df):,}")
    
    # Filter to fair odds < 2.5
    print("\n[FILTER] Keeping only fair odds < 2.5...")
    df = df[df['fair_odds_decimal'] < 2.5].copy()
    print(f"   After fair odds filter: {len(df):,}")
    
    # Round EV to 2 decimal places
    df['ev_percent'] = df['ev_percent'].round(2)
    
    # Add Kelly column as Excel formula (will calculate dynamically)
    # Kelly formula: K = ((best_odds / fair_odds) - 1) / (best_odds - 1)
    # For $1000 bankroll: bet_size = 1000 * K
    # Rounded to nearest $5 using MROUND
    # Excel formula references columns I (best_au_odds_decimal)
    # and K (fair_odds_decimal)
    print("\n[CALC] Adding Kelly formula column...")
    
    # Create Excel formula for each row (row numbers start at 2 in Excel)
    kelly_formulas = []
    for idx in range(len(df)):
        row_num = idx + 2  # Excel rows start at 2 (1 is header)
        formula = (
            f"=MROUND(MAX(0, 1000 * ((I{row_num}/K{row_num}) - 1) / "
            f"(I{row_num} - 1)), 5)"
        )
        kelly_formulas.append(formula)
    
    df['kelly_1000'] = kelly_formulas
    
    # Remove unwanted columns
    columns_to_remove = ['sport', 'event_id', 'extracted_at', 'pair_id']
    df_filtered = df.drop(columns=columns_to_remove, errors='ignore')
    
    # Reorder columns to put kelly_1000 after uses_devig
    cols = df_filtered.columns.tolist()
    
    # Find index of uses_devig
    if 'uses_devig' in cols:
        uses_devig_idx = cols.index('uses_devig')
        
        # Remove kelly_1000 from its current position
        if 'kelly_1000' in cols:
            cols.remove('kelly_1000')
        
        # Insert kelly_1000 right after uses_devig
        cols.insert(uses_devig_idx + 1, 'kelly_1000')
        
        df_filtered = df_filtered[cols]
    
    # Save to Pats_Picks.csv
    output_csv = data_dir / "Pats_Picks.csv"
    try:
        df_filtered.to_csv(output_csv, index=False)
    except PermissionError:
        output_csv = data_dir / "Pats_Picks_new.csv"
        df_filtered.to_csv(output_csv, index=False)
        print(f"⚠️  Main file locked, saved to: {output_csv}")
    
    print(f"\n[OK] Pats_Picks.csv saved: {output_csv}")
    print(f"   Rows: {len(df_filtered):,}")
    print(f"   Columns: {len(df_filtered.columns)}")
    print("\n[STATS] Column order:")
    for i, col in enumerate(df_filtered.columns[:20], 1):
        print(f"   {i:2d}. {col}")
    if len(df_filtered.columns) > 20:
        print(f"   ... ({len(df_filtered.columns) - 20} more columns)")
    
    print("\n[INFO] Kelly column contains Excel formulas")
    print("   Formula: =MROUND(MAX(0, 1000 * ((I#/K#) - 1) / (I# - 1)), 5)")
    print("   Rounded to nearest $5")
    print("   Will auto-calculate when you open in Excel!")
    
    return output_csv


if __name__ == "__main__":
    generate_pats_picks()
