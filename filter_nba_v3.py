"""
NBA V3 Data Filtering
======================
Filters extracted NBA odds CSV to include only desired markets and formats.

Usage:
    python filter_nba_v3.py

Output:
    data/v3/extracts/basketball_nba_filtered_*.csv
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
    
    # Get latest NBA_Raw CSV
    csv_files = sorted(glob.glob("data/v3/extracts/basketball_nba_raw*.csv"))
    if not csv_files:
        print("[ERROR] No NBA_Raw CSV files found in data/v3/extracts/")
        return
    
    # Prioritize _new.csv (fresh extraction, main file might be locked by backend)
    csv_new = [f for f in csv_files if f.endswith("_new.csv")]
    latest_raw_csv = csv_new[-1] if csv_new else csv_files[-1]
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
        
        # Player points alternates
        'player_points_alternate': 'player_points',
        
        # Other alternates
        'player_rebounds_alternate': 'player_rebounds',
        'player_assists_alternate': 'player_assists',
        'player_threes_alternate': 'player_threes',
        'player_blocks_alternate': 'player_blocks',
        'player_steals_alternate': 'player_steals',
    }
    
    df['market_type'] = df['market_type'].map(lambda x: market_normalization.get(x, x))
    print(f"[OK] After normalizing market names: {len(df):,} rows")
    
    # FILTER 2: Remove whole number spreads/totals (keep only .5 lines)
    spread_total_rows = df[~df['market_type'].isin(['spreads', 'totals', 'team_totals'])]
    
    spreads_totals = df[df['market_type'].isin(['spreads', 'totals', 'team_totals'])].copy()
    spreads_totals['is_half'] = spreads_totals['point'].fillna(0) % 1 != 0
    spreads_totals = spreads_totals[spreads_totals['is_half']]
    spreads_totals = spreads_totals.drop('is_half', axis=1)
    
    df = pd.concat([spread_total_rows, spreads_totals], ignore_index=True)
    print(f"[OK] After removing whole number spreads/totals: {len(df):,} rows")
    
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
        
        # Group by composite key: (event_name, market_type, point, player_name)
        # This ensures each key represents ONE market (not multiple players/points)
        key_groups = df_full.groupby(['event_name', 'market_type', 'point', 'player_name'], dropna=False)
        
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
                df_full.loc[group_indices[group['selection'] == selection_1].tolist(), 'pair_id'] = pair_counter
                df_full.loc[group_indices[group['selection'] == selection_2].tolist(), 'pair_id'] = pair_counter
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
        # Rule 1: Each pair must have exactly 2 rows
        if len(group) != 2:
            pair_violations.append(f"Pair {pair_id}: {len(group)} rows (expected 2)")
        
        # Rule 2: Same event, market, point, player
        if group['event_name'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed events {group['event_name'].unique().tolist()}")
        if group['market_type'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed markets {group['market_type'].unique().tolist()}")
        if group['point'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed points {group['point'].unique().tolist()}")
        if group['player_name'].nunique() > 1:
            pair_violations.append(f"Pair {pair_id}: Mixed players {group['player_name'].unique().tolist()}")
        
        # Rule 3: Opposite selections (Over/Under or Home/Away)
        selections = group['selection'].unique()
        if len(selections) != 2:
            pair_violations.append(f"Pair {pair_id}: {len(selections)} selections (expected 2)")
    
    if pair_violations:
        print(f"[WARN] Found {len(pair_violations)} violations:")
        for v in pair_violations[:10]:  # Show first 10
            print(f"   - {v}")
    else:
        print(f"[OK] All {len(paired_df) // 2} pairs valid (2 rows each, same market/point/player)")
    
    # Save output
    os.makedirs("data/v3/extracts", exist_ok=True)
    
    # Use timestamped filename to avoid backend lock issues
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"data/v3/extracts/basketball_nba_filtered_{timestamp}.csv"
    
    df.to_csv(output_csv, index=False)
    print(f"[OK] NBA_Filtered CSV saved: {output_csv}")
    
    print(f"   Final rows: {len(df):,}")
    print(f"\nMarket breakdown:")
    print(df['market_type'].value_counts())
    
    return output_csv

if __name__ == "__main__":
    filter_nba_data()
