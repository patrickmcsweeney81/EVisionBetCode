"""
Debug: Find opposite bets for 2-way markets in filtered NBA CSV.
Investigates why some lines aren't getting de-vigged.
"""

import pandas as pd
import numpy as np

# Load filtered CSV
filtered_csv = "data/v3/extracts/basketball_nba_filtered.csv"
df = pd.read_csv(filtered_csv)

print(f"📂 Loaded {len(df):,} rows from {filtered_csv}\n")

# 2-way market mapping
TWO_WAY_MARKETS = {
    'totals': {'Over': 'Under', 'Under': 'Over'},
    'spreads': {'Home': 'Away', 'Away': 'Home'},
    'h2h': {'Home': 'Away', 'Away': 'Home'},
}

def get_opposite_selection(market_type, selection):
    """Get opposite selection for 2-way markets."""
    if market_type not in TWO_WAY_MARKETS:
        return None
    return TWO_WAY_MARKETS[market_type].get(selection)

def is_2way_market(market_type):
    """Check if market is 2-way."""
    return market_type in TWO_WAY_MARKETS

# Analyze 2-way markets
print("=" * 80)
print("ANALYZING 2-WAY MARKETS")
print("=" * 80)

two_way_rows = df[df['market_type'].isin(['totals', 'spreads', 'h2h'])].copy()
print(f"\n📊 Total 2-way market rows: {len(two_way_rows):,}\n")

found_opposites = 0
missing_opposites = 0
issues = []

for idx, row in two_way_rows.iterrows():
    event_id = row['event_id']
    market_type = row['market_type']
    selection = row['selection']
    point = row.get('point', '')
    
    opposite_sel = get_opposite_selection(market_type, selection)
    
    # Try to find opposite
    opposite_rows = df[(df['event_id'] == event_id) & 
                       (df['market_type'] == market_type) & 
                       (df['selection'] == opposite_sel)]
    
    if not opposite_rows.empty:
        found_opposites += 1
    else:
        missing_opposites += 1
        
        # Debug info
        if missing_opposites <= 10:  # Show first 10 issues
            issue_info = {
                'event_id': event_id,
                'event_name': row['event_name'],
                'market_type': market_type,
                'selection': selection,
                'opposite_sel': opposite_sel,
                'point': point
            }
            issues.append(issue_info)
            
            # Check what selections exist for this event+market combo
            existing = df[(df['event_id'] == event_id) & 
                         (df['market_type'] == market_type)]['selection'].unique()
            print(f"❌ Missing opposite for: {selection} ({market_type})")
            print(f"   Event: {row['event_name']}")
            print(f"   Point: {point}")
            print(f"   Existing selections: {list(existing)}")
            print()

print(f"=" * 80)
print(f"📊 SUMMARY:")
print(f"   Total 2-way rows: {len(two_way_rows):,}")
print(f"   ✅ Found opposite: {found_opposites:,} ({found_opposites/len(two_way_rows)*100:.1f}%)")
print(f"   ❌ Missing opposite: {missing_opposites:,} ({missing_opposites/len(two_way_rows)*100:.1f}%)")
print(f"=" * 80)

# Check market type distribution
print(f"\n📊 2-WAY MARKET BREAKDOWN:")
print(df[df['market_type'].isin(['totals', 'spreads', 'h2h'])]['market_type'].value_counts())

# Check if point/selection combinations are issue
print(f"\n🔍 SAMPLE: Totals Market Analysis")
totals_df = df[df['market_type'] == 'totals'].head(20)
print(f"\nSample totals rows (first 20):")
print(totals_df[['event_name', 'selection', 'point', 'market_type']].to_string(index=False))

# Check for point mismatches
print(f"\n🔍 CHECKING POINT ALIGNMENT (Totals)")
totals_events = totals_df['event_id'].unique()
for event_id in totals_events[:2]:  # Check first 2 events
    event_totals = df[(df['event_id'] == event_id) & (df['market_type'] == 'totals')]
    if len(event_totals) > 0:
        print(f"\nEvent {event_id[:8]}...: {event_totals.iloc[0]['event_name']}")
        print(event_totals[['selection', 'point', 'market_type']].to_string(index=False))

print(f"\n🔍 CHECKING POINT ALIGNMENT (Spreads)")
spreads_df = df[df['market_type'] == 'spreads'].head(20)
spreads_events = spreads_df['event_id'].unique()
for event_id in spreads_events[:2]:  # Check first 2 events
    event_spreads = df[(df['event_id'] == event_id) & (df['market_type'] == 'spreads')]
    if len(event_spreads) > 0:
        print(f"\nEvent {event_id[:8]}...: {event_spreads.iloc[0]['event_name']}")
        print(event_spreads[['selection', 'point', 'market_type']].to_string(index=False))
