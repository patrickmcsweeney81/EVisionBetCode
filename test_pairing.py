"""
Test suite for NBA pairing logic
Run with: pytest test_pairing.py -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')

# Import functions from filter_nba_v3
def is_2way_market(market_type):
    """Check if market is 2-way."""
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
    return market_type in TWO_WAY_MARKETS

def get_opposite_selection(market_type, selection):
    """Get opposite selection for 2-way markets."""
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
    if market_type not in TWO_WAY_MARKETS:
        return None
    
    mapping = TWO_WAY_MARKETS[market_type]
    if isinstance(mapping, dict):
        return mapping.get(selection)
    return None

def assign_pair_ids_composite_key(df_full):
    """Composite Key approach (Option C) - No cross-player/point grouping."""
    df_full = df_full.copy()
    df_full['pair_id'] = None
    pair_counter = 0
    
    # Group by composite key: (event_name, market_type, point, player_name)
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
            pass
    
    return df_full


class TestPairingLogic:
    """Test pairing algorithm correctness."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'event_name': [
                'Team A @ Team B', 'Team A @ Team B',  # Pair 1: Kon Knueppel Over/Under
                'Team A @ Team B', 'Team A @ Team B',  # Pair 2: Nikola Vucevic Over/Under
                'Team C @ Team D', 'Team C @ Team D',  # Pair 3: Aaron Nesmith Over/Under
            ],
            'market_type': ['player_assists'] * 6,
            'selection': ['Over', 'Under', 'Over', 'Under', 'Over', 'Under'],
            'point': [3.5, 3.5, 3.5, 3.5, 2.5, 2.5],
            'player_name': ['Kon Knueppel', 'Kon Knueppel', 'Nikola Vucevic', 'Nikola Vucevic', 'Aaron Nesmith', 'Aaron Nesmith'],
        })
    
    def test_pairing_no_cross_player_grouping(self, sample_data):
        """Verify: Different players don't share same pair_id."""
        df = assign_pair_ids_composite_key(sample_data)
        
        # Get paired rows
        paired = df[df['pair_id'].notna()]
        
        # Check each pair_id has exactly one unique player
        for pair_id, group in paired.groupby('pair_id'):
            unique_players = group['player_name'].nunique()
            assert unique_players == 1, f"Pair {pair_id} has {unique_players} players (expected 1)"
    
    def test_pairing_correct_count(self, sample_data):
        """Verify: Each pair has exactly 2 rows."""
        df = assign_pair_ids_composite_key(sample_data)
        
        paired = df[df['pair_id'].notna()]
        
        for pair_id, group in paired.groupby('pair_id'):
            assert len(group) == 2, f"Pair {pair_id} has {len(group)} rows (expected 2)"
    
    def test_pairing_opposite_selections(self, sample_data):
        """Verify: Paired rows have opposite selections (Over/Under)."""
        df = assign_pair_ids_composite_key(sample_data)
        
        paired = df[df['pair_id'].notna()]
        
        for pair_id, group in paired.groupby('pair_id'):
            selections = group['selection'].unique()
            assert len(selections) == 2, f"Pair {pair_id} should have 2 different selections"
            assert set(selections) == {'Over', 'Under'} or set(selections) == {'home', 'away'}, \
                f"Pair {pair_id} selections {selections} not valid opposites"
    
    def test_pairing_same_market_point(self, sample_data):
        """Verify: Paired rows have same market_type and point."""
        df = assign_pair_ids_composite_key(sample_data)
        
        paired = df[df['pair_id'].notna()]
        
        for pair_id, group in paired.groupby('pair_id'):
            assert group['market_type'].nunique() == 1, f"Pair {pair_id} has different market types"
            assert group['point'].nunique() == 1, f"Pair {pair_id} has different points"
    
    def test_is_2way_market(self):
        """Test market classification."""
        assert is_2way_market('player_assists') == True
        assert is_2way_market('totals') == True
        assert is_2way_market('spreads') == True
        assert is_2way_market('player_first_basket') == False
        # odd_even not in our 2-way list (not implemented yet)
        assert is_2way_market('odd_even') == False
    
    def test_get_opposite_selection(self):
        """Test opposite selection lookup."""
        assert get_opposite_selection('player_assists', 'Over') == 'Under'
        assert get_opposite_selection('player_assists', 'Under') == 'Over'
        assert get_opposite_selection('totals', 'Over') == 'Under'
        assert get_opposite_selection('spreads', 'Over') == None  # Spreads use home/away
        assert get_opposite_selection('invalid', 'Over') == None


class TestPairingEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_orphaned_single_selection(self):
        """Verify: Single selection without opposite gets pair_id=None."""
        df = pd.DataFrame({
            'event_name': ['Event1', 'Event1'],
            'market_type': ['player_points', 'player_points'],
            'selection': ['Over', 'Over'],  # Both Over, no Under
            'point': [20.5, 20.5],
            'player_name': ['Player A', 'Player A'],
        })
        
        result = assign_pair_ids_composite_key(df)
        
        # Both rows should have NaN pair_id (can't pair single selection)
        assert result['pair_id'].isna().all()
    
    def test_multiple_pairs_same_event(self):
        """Verify: Multiple pairs within same event get different pair_ids."""
        df = pd.DataFrame({
            'event_name': ['Event1'] * 8,
            'market_type': ['player_assists'] * 8,
            'selection': ['Over', 'Under', 'Over', 'Under', 'Over', 'Under', 'Over', 'Under'],
            'point': [3.5, 3.5, 3.5, 3.5, 2.5, 2.5, 2.5, 2.5],
            'player_name': ['A', 'A', 'B', 'B', 'A', 'A', 'C', 'C'],
        })
        
        result = assign_pair_ids_composite_key(df)
        
        # Should have 4 distinct pair_ids
        paired = result[result['pair_id'].notna()]
        unique_pairs = paired['pair_id'].nunique()
        assert unique_pairs == 4, f"Expected 4 pairs, got {unique_pairs}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
