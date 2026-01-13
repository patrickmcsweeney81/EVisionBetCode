"""
NBA V3 Data Filtering
======================
Filters extracted NBA odds CSV to include only desired markets and formats.

Usage:
    python filter_nba_v3.py

Output:
    data/v3/extracts/NBA_Filtered.csv (or NBA_Filtered_new.csv if locked)
"""

import pandas as pd
import glob
import os
from datetime import datetime
import numpy as np
import networkx as nx

# 2-way market definitions
TWO_WAY_MARKETS = {
    'totals': {'Over': 'Under', 'Under': 'Over'},
    'spreads': 'pair_with_other_team',
    'h2h': 'pair_with_other_team',
    'h2h_lay': 'pair_with_other_team',
    'player_rebounds': {'Over': 'Under', 'Under': 'Over'},
    'player_rebounds_assists': {'Over': 'Under', 'Under': 'Over'},
    'player_points': {'Over': 'Under', 'Under': 'Over'},
    'player_points_assists': {'Over': 'Under', 'Under': 'Over'},
    'player_points_rebounds': {'Over': 'Under', 'Under': 'Over'},
    'player_points_rebounds_assists': {'Over': 'Under', 'Under': 'Over'},
    'player_assists': {'Over': 'Under', 'Under': 'Over'},
    'player_threes': {'Over': 'Under', 'Under': 'Over'},
    'player_blocks': {'Over': 'Under', 'Under': 'Over'},
    'player_steals': {'Over': 'Under', 'Under': 'Over'},
}

def is_2way_market(market_type):
    """Check if market is 2-way."""
    return market_type in TWO_WAY_MARKETS

def get_opposite_selection(market_type, selection):
    """Get opposite selection for 2-way markets."""
    if market_type not in TWO_WAY_MARKETS:
        return None
    
    mapping = TWO_WAY_MARKETS[market_type]
    
    # If mapping is a dict (Over/Under), use it
    if isinstance(mapping, dict):
        return mapping.get(selection)
    
    # If it's 'pair_with_other_team' (spreads/h2h), handled separately
    return None

def filter_nba_data():
    """Load latest NBA_Raw CSV and create NBA_Filtered CSV with filters applied."""
    
    # Get latest NBA_Raw CSV (prefer _new, fallback to main)
    candidates = [
        "data/v3/extracts/NBA_Raw_new.csv",
        "data/v3/extracts/NBA_Raw.csv",
        "data/v3/extracts/basketball_nba_raw.csv",
    ]
    # Legacy timestamped raw files as last resort
    if not any(os.path.exists(c) for c in candidates):
        legacy = sorted(glob.glob("data/v3/extracts/basketball_nba_raw_*.csv"))
        if legacy:
            candidates.append(legacy[-1])
    latest_raw_csv = next((c for c in candidates if os.path.exists(c)), None)
    if not latest_raw_csv:
        print("[ERROR] No NBA_Raw CSV files found in data/v3/extracts/")
        return
    print(f"[*] Loading NBA_Raw: {latest_raw_csv}")
    
    df = pd.read_csv(latest_raw_csv)
    print(f"   Starting rows: {len(df):,}")
    
    # ============ APPLY FILTERS ============
    
    # FILTER 1: Normalize market names - consolidate alternates by base market type
    market_normalization = {
        # Spreads consolidation
        'alternate_spreads': 'spreads',
        'spreads_q1': 'spreads',
        'spreads_q2': 'spreads',
        'spreads_q3': 'spreads',
        'spreads_q4': 'spreads',
        'spreads_h1': 'spreads',
        'spreads_h2': 'spreads',
        
        # Totals consolidation
        'alternate_totals': 'totals',
        'alternate_totals_q1': 'totals',
        'alternate_totals_q2': 'totals',
        'alternate_totals_q3': 'totals',
        'alternate_totals_q4': 'totals',
        'alternate_totals_h1': 'totals',
        'alternate_totals_h2': 'totals',
        'totals_q1': 'totals',
        'totals_q2': 'totals',
        'totals_q3': 'totals',
        'totals_q4': 'totals',
        'totals_h1': 'totals',
        'totals_h2': 'totals',
        
        # Team totals consolidation
        'alternate_team_totals': 'team_totals',
        'team_totals_q1': 'team_totals',
        'team_totals_q2': 'team_totals',
        'team_totals_q3': 'team_totals',
        'team_totals_q4': 'team_totals',
        'team_totals_h1': 'team_totals',
        'team_totals_h2': 'team_totals',
        
        # Player single stat alternates
        'player_points_alternate': 'player_points',
        'player_rebounds_alternate': 'player_rebounds',
        'player_assists_alternate': 'player_assists',
        'player_threes_alternate': 'player_threes',
        'player_blocks_alternate': 'player_blocks',
        'player_steals_alternate': 'player_steals',
        
        # Player combo stat alternates (align with base markets)
        'player_points_rebounds_alternate': 'player_points_rebounds',
        'player_points_rebounds_assists_alternate': 'player_points_rebounds_assists',
        'player_points_assists_alternate': 'player_points_assists',
        'player_rebounds_assists_alternate': 'player_rebounds_assists',
    }
    
    df['market_type'] = df['market_type'].map(lambda x: market_normalization.get(x, x))
    print(f"[OK] After normalizing market names: {len(df):,} rows")
    
    # FILTER 2: Split whole number vs half-point spreads/totals
    # Whole numbers → Push_Vig_markets.csv (separate output)
    # Half-points (.5) → continue to main filtered output
    spread_total_rows = df[~df['market_type'].isin(['spreads', 'totals', 'team_totals'])]
    
    spreads_totals = df[df['market_type'].isin(['spreads', 'totals', 'team_totals'])].copy()
    spreads_totals['is_half'] = spreads_totals['point'].fillna(0) % 1 != 0
    
    # Save whole number markets to separate CSV
    whole_numbers = spreads_totals[~spreads_totals['is_half']].drop('is_half', axis=1)
    if not whole_numbers.empty:
        push_vig_csv = "data/v3/extracts/Push_Vig_markets.csv"
        whole_numbers.to_csv(push_vig_csv, index=False)
        print(f"[INFO] Saved {len(whole_numbers):,} whole number lines to: {push_vig_csv}")
    
    # Keep only half-point lines for main output
    spreads_totals = spreads_totals[spreads_totals['is_half']].drop('is_half', axis=1)
    
    df = pd.concat([spread_total_rows, spreads_totals], ignore_index=True)
    print(f"[OK] After splitting whole/half spreads/totals: {len(df):,} rows (half-point only)")
    
    # FILTER 3: Keep only lines with at least one sharp book
    sharp_books = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 'fanduel', 'lowvig']
    
    df['has_sharp_book'] = df[sharp_books].notna().any(axis=1)
    df = df[df['has_sharp_book']]
    df = df.drop('has_sharp_book', axis=1)
    print(f"[OK] After keeping only lines with sharp books: {len(df):,} rows")
    
    # FILTER 4: Keep only lines with at least one AU bookmaker
    au_books = ['bet365', 'betfair_ex_au', 'sportsbet', 'dabble_au', 'pointsbetau', 
                'neds', 'ladbrokes_au', 'unibet', 'betright', 'betr_au', 'boombet', 
                'playup', 'tab', 'tabtouch']
    
    df['has_au_book'] = df[au_books].notna().any(axis=1)
    df = df[df['has_au_book']]
    df = df.drop('has_au_book', axis=1)
    print(f"[OK] After keeping only lines with AU books: {len(df):,} rows")
    
    # FILTER 4B: Split lines by 4-star sharp book count
    # Lines with <2 4-star sharps → Push_Vig_markets.csv (harder to de-vig)
    # Lines with >=2 4-star sharps → Main filtered output
    four_star_books = ['pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings',
                       'fanduel', 'lowvig']
    df['sharp_count'] = df[four_star_books].notna().sum(axis=1)
    
    # Save lines with <2 sharps to Push_Vig
    push_vig_low_sharps = df[df['sharp_count'] < 2].drop('sharp_count', axis=1)
    if not push_vig_low_sharps.empty:
        push_vig_csv = "data/v3/extracts/Push_Vig_markets.csv"
        try:
            push_vig_low_sharps.to_csv(push_vig_csv, index=False)
        except PermissionError:
            push_vig_csv = "data/v3/extracts/Push_Vig_markets_new.csv"
            push_vig_low_sharps.to_csv(push_vig_csv, index=False)
        msg = f"[INFO] Saved {len(push_vig_low_sharps):,} lines with <2 sharps"
        print(f"{msg} to: {push_vig_csv}")
    
    # Keep only lines with >=2 4-star sharps for main output
    df = df[df['sharp_count'] >= 2].drop('sharp_count', axis=1)
    print(f"[OK] After filtering for >=2 4-star sharps: {len(df):,} rows")
    
    # FILTER 5: Remove duplicate bets
    df = df.drop_duplicates(subset=['event_name', 'market_type', 'selection', 'point', 'player_name'], keep='first')
    print(f"[OK] After removing all duplicate bets: {len(df):,} rows")
    
    # ASSIGN PAIR IDs: Match both sides of 2-way markets within each event
    # Using Composite Key approach: (event, market_type, point, player_name)
    def assign_pair_ids_composite_key(df_full):
        """Composite Key approach (Option C) - No cross-player/point grouping."""
        df_full = df_full.copy()
        df_full['pair_id'] = None
        pair_counter = 0
        
        # SPECIAL HANDLING FOR SPREADS: Group by (event, market, |point|)
        # Spreads should produce exactly two usable rows: favorite (-abs_point) vs underdog (+abs_point)
        # Some books emit both teams with both signs; we must pick one + and one - with different selections.
        if 'spreads' in df_full['market_type'].values:
            spreads_df = df_full[df_full['market_type'] == 'spreads'].copy()
            spreads_df['abs_point'] = spreads_df['point'].abs()
            
            for (event, market, abs_point), group_indices in spreads_df.groupby(['event_name', 'market_type', 'abs_point'], dropna=False).groups.items():
                group = spreads_df.loc[group_indices].copy()
                rows_neg = group[group['point'] < 0]
                rows_pos = group[group['point'] > 0]
                
                # Need at least one negative and one positive row with different selections
                if rows_neg.empty or rows_pos.empty:
                    continue
                
                paired = False
                # Pick first negative row whose selection differs from a positive row
                for _, neg_row in rows_neg.iterrows():
                    pos_match = rows_pos[rows_pos['selection'] != neg_row['selection']]
                    if not pos_match.empty:
                        pos_row = pos_match.iloc[0]
                        df_full.loc[neg_row.name, 'pair_id'] = pair_counter
                        df_full.loc[pos_row.name, 'pair_id'] = pair_counter
                        pair_counter += 1
                        paired = True
                        break
                if not paired:
                    # Could not find opposite team; leave unpaired
                    continue
        
        # NORMAL HANDLING FOR OTHER MARKETS: Group by exact point value
        # For player props: same player, same point → Over/Under pair
        # For totals: same event, same point → Over/Under pair
        non_spreads = df_full[df_full['market_type'] != 'spreads']
        key_groups = non_spreads.groupby(['event_name', 'market_type', 'point', 'player_name'], dropna=False)
        
        for (event, market, point, player), group_indices in key_groups.groups.items():
            group = df_full.loc[group_indices].copy()
            
            # Only process 2-way markets
            if not is_2way_market(market):
                continue
            
            # Get unique selections in this group
            selections = group['selection'].unique()
            
            if len(selections) == 2:
                # Perfect pair: Over+Under or Home+Away
                selection_1, selection_2 = selections[0], selections[1]
                indices_1 = group_indices[group['selection'] == selection_1].tolist()
                indices_2 = group_indices[group['selection'] == selection_2].tolist()
                df_full.loc[indices_1, 'pair_id'] = pair_counter
                df_full.loc[indices_2, 'pair_id'] = pair_counter
                pair_counter += 1
            elif len(selections) == 1:
                # Single selection (orphaned - can't pair without opposite)
                # Leave pair_id as None
                pass
        
        return df_full
    
    # Apply composite key pairing
    df = assign_pair_ids_composite_key(df)
    print(f"[OK] After assigning pair_ids (Composite Key): {len(df):,} rows")
    
    # VALIDATION: Check pairing integrity with NetworkX
    print("\n[VALIDATION] Checking pairing integrity...")
    
    # Build validation graph
    G = nx.Graph()
    paired_df = df[df['pair_id'].notna()].copy()
    pair_violations = []
    
    for pair_id, group in paired_df.groupby('pair_id'):
        # For spreads: can have 4+ rows (multiple bookmakers per team)
        # For others: must have exactly 2 rows (Over+Under or Home+Away)
        market_type = group['market_type'].iloc[0]
        expected_rows = "2+" if market_type == 'spreads' else "2"
        
        # Rule 1: Each pair must have >= 2 rows (spreads can have 4+)
        if market_type == 'spreads':
            if len(group) < 2:
                pair_violations.append(f"Pair {pair_id}: {len(group)} rows (expected 2+)")
        else:
            if len(group) != 2:
                pair_violations.append(f"Pair {pair_id}: {len(group)} rows (expected 2)")
        
        # Rule 2: Same event, market, point, player
        if group['event_name'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed events {group['event_name'].unique().tolist()}")
        if group['market_type'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed markets {group['market_type'].unique().tolist()}")
        # Spreads can have mixed points due to |point| grouping (that's OK)
        if market_type != 'spreads' and group['point'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed points {group['point'].unique().tolist()}")
        if group['player_name'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed players {group['player_name'].unique().tolist()}")
        
        # Rule 3: Opposite selections (Over/Under or Home/Away)
        selections = group['selection'].unique()
        if len(selections) < 2:
            pair_violations.append(f"Pair {pair_id}: Only {len(selections)} selection (expected 2)")
    
    if pair_violations:
        print(f"[WARN] Found {len(pair_violations)} violations:")
        for v in pair_violations[:10]:  # Show first 10
            print(f"   - {v}")
    else:
        total_pairs = len(paired_df) // 2 if df[df['market_type'] != 'spreads']['pair_id'].notna().sum() > 0 else "multiple"
        print(f"[OK] All pairs valid (2 rows for player props, 4+ rows for spreads)")
    
    # FILTER: Count 4-star sharp books for de-vigging requirement
    four_star_books = [
        'pinnacle', 'betfair_ex_eu', 'matchbook', 'draftkings', 
        'fanduel', 'lowvig'
    ]
    df['sharp_book_count'] = df[four_star_books].notna().sum(axis=1)
    
    # Split: Paired + >=2 4-star sharps → main filtered
    # Unpaired OR <2 4-star sharps → Push_Vig
    main_df = df[(df['pair_id'].notna()) & (df['sharp_book_count'] >= 2)]
    vig_df = df[(df['pair_id'].isna()) | (df['sharp_book_count'] < 2)]
    
    # Save output
    os.makedirs("data/v3/extracts", exist_ok=True)
    
    # Save Push_Vig lines (unpaired or <2 sharps)
    if not vig_df.empty:
        vig_csv = "data/v3/extracts/Push_Vig_markets.csv"
        try:
            vig_df_out = vig_df.drop('sharp_book_count', axis=1)
            vig_df_out.to_csv(vig_csv, index=False)
            print(
                f"[INFO] Saved {len(vig_df):,} unpaired/low-sharp lines "
                f"to: {vig_csv}"
            )
        except PermissionError:
            vig_csv = "data/v3/extracts/Push_Vig_markets_new.csv"
            vig_df.drop('sharp_book_count', axis=1).to_csv(vig_csv, index=False)
            print(f"[WARN] Push_Vig locked; saved to {vig_csv}")
    
    output_csv = "data/v3/extracts/NBA_Filtered.csv"
    main_df_out = main_df.drop('sharp_book_count', axis=1)
    try:
        main_df_out.to_csv(output_csv, index=False)
    except PermissionError:
        output_csv = "data/v3/extracts/NBA_Filtered_new.csv"
        main_df_out.to_csv(output_csv, index=False)
        print(f"[WARN] Main NBA_Filtered locked; saved to {output_csv}")
    else:
        print(f"[OK] NBA_Filtered CSV saved: {output_csv}")
    
    print(f"   Final rows: {len(main_df):,}")
    print(f"\nMarket breakdown:")
    print(main_df['market_type'].value_counts())
    
    return output_csv

if __name__ == "__main__":
    filter_nba_data()
