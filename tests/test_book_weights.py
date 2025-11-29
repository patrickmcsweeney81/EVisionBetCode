"""
Tests for the book_weights module.
"""
import sys
import os

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.book_weights import (
    get_book_weight,
    get_book_display_name,
    list_books_by_weight,
    MAIN_MARKET_WEIGHTS,
    PLAYER_PROP_WEIGHTS,
    SPORT_OVERRIDES,
)


def test_main_market_weights():
    """Test MAIN_MARKET_WEIGHTS structure and key bookmakers."""
    # Tier 1 sharps should be 4
    assert MAIN_MARKET_WEIGHTS.get("pinnacle") == 4, "Pinnacle should be weight 4"
    assert MAIN_MARKET_WEIGHTS.get("circa") == 4, "Circa should be weight 4"
    assert MAIN_MARKET_WEIGHTS.get("bookmaker") == 4, "Bookmaker/CRIS should be weight 4"
    
    # Tier 1-2 sharps should be 3
    assert MAIN_MARKET_WEIGHTS.get("betonline") == 3, "BetOnline should be weight 3"
    assert MAIN_MARKET_WEIGHTS.get("draftkings") == 3, "DraftKings should be weight 3"
    
    # Soft books should be 1
    assert MAIN_MARKET_WEIGHTS.get("bovada") == 1, "Bovada should be weight 1"
    
    print("  ✓ Main market weights validated")


def test_player_prop_weights():
    """Test PLAYER_PROP_WEIGHTS structure and key bookmakers."""
    # DK/FD should be top tier (4) for props
    assert PLAYER_PROP_WEIGHTS.get("pinnacle") == 4, "Pinnacle should be weight 4 for props"
    assert PLAYER_PROP_WEIGHTS.get("draftkings") == 4, "DraftKings should be weight 4 for props"
    assert PLAYER_PROP_WEIGHTS.get("fanduel") == 4, "FanDuel should be weight 4 for props"
    
    # BetMGM should be 3 for props (stronger than main)
    assert PLAYER_PROP_WEIGHTS.get("betmgm") == 3, "BetMGM should be weight 3 for props"
    
    # Soft books should be 1
    assert PLAYER_PROP_WEIGHTS.get("bovada") == 1, "Bovada should be weight 1 for props"
    
    print("  ✓ Player prop weights validated")


def test_sport_overrides_exist():
    """Test that sport overrides exist for key sports."""
    assert "MMA" in SPORT_OVERRIDES, "MMA should have overrides"
    assert "NBA" in SPORT_OVERRIDES, "NBA should have overrides"
    assert "NFL" in SPORT_OVERRIDES, "NFL should have overrides"
    
    # MMA should have both main and props overrides
    assert "main" in SPORT_OVERRIDES["MMA"], "MMA should have main overrides"
    assert "props" in SPORT_OVERRIDES["MMA"], "MMA should have props overrides"
    
    # NBA/NFL should have props overrides
    assert "props" in SPORT_OVERRIDES["NBA"], "NBA should have props overrides"
    assert "props" in SPORT_OVERRIDES["NFL"], "NFL should have props overrides"
    
    print("  ✓ Sport overrides structure validated")


def test_get_book_weight_basic():
    """Test get_book_weight for basic cases."""
    # Main market - Pinnacle should be 4
    assert get_book_weight("pinnacle", "main") == 4
    assert get_book_weight("pinnacle", "h2h") == 4
    assert get_book_weight("pinnacle", "spreads") == 4
    
    # Props - DraftKings should be 4
    assert get_book_weight("draftkings", "props") == 4
    
    # Unknown book should return 0
    assert get_book_weight("unknown_book", "main") == 0
    assert get_book_weight("nonexistent", "props") == 0
    
    print("  ✓ Basic get_book_weight calls validated")


def test_get_book_weight_normalization():
    """Test input normalization in get_book_weight."""
    # Case insensitive
    assert get_book_weight("PINNACLE", "main") == 4
    assert get_book_weight("Pinnacle", "MAIN") == 4
    
    # Whitespace handling
    assert get_book_weight("  pinnacle  ", "  main  ") == 4
    
    # Market type aliases
    assert get_book_weight("pinnacle", "h2h") == 4
    assert get_book_weight("pinnacle", "spread") == 4
    assert get_book_weight("pinnacle", "spreads") == 4
    assert get_book_weight("pinnacle", "total") == 4
    assert get_book_weight("pinnacle", "totals") == 4
    assert get_book_weight("pinnacle", "moneyline") == 4
    
    print("  ✓ Input normalization validated")


def test_get_book_weight_sport_override():
    """Test sport-specific overrides in get_book_weight."""
    # MMA: BetOnline should be higher (4) than default (3)
    assert get_book_weight("betonline", "main") == 3  # default
    assert get_book_weight("betonline", "main", "MMA") == 4  # MMA override
    
    # NBA props: bet365 should be 3 (override from default 2)
    assert get_book_weight("bet365", "props") == 2  # default
    assert get_book_weight("bet365", "props", "NBA") == 3  # NBA override
    
    # Sport code normalization
    assert get_book_weight("draftkings", "props", "BASKETBALL_NBA") == get_book_weight("draftkings", "props", "NBA")
    assert get_book_weight("betonline", "main", "UFC") == get_book_weight("betonline", "main", "MMA")
    
    print("  ✓ Sport-specific overrides validated")


def test_get_book_weight_fallback():
    """Test fallback behavior when sport override doesn't have a book."""
    # If a book isn't in sport override, should fall back to global
    # Marathonbet is in global PLAYER_PROP_WEIGHTS but not in NBA override
    assert get_book_weight("marathonbet", "props") == 1  # global
    assert get_book_weight("marathonbet", "props", "NBA") == 1  # falls back to global
    
    print("  ✓ Fallback to global weights validated")


def test_get_book_display_name():
    """Test get_book_display_name function."""
    assert get_book_display_name("pinnacle") == "Pinnacle"
    assert get_book_display_name("draftkings") == "DraftKings"
    assert get_book_display_name("bet365_au") == "Bet365 AU"
    
    # Unknown book should return formatted code
    assert get_book_display_name("unknown_book") == "Unknown Book"
    
    print("  ✓ Display name function validated")


def test_list_books_by_weight():
    """Test list_books_by_weight function."""
    # Main market - check top books
    main_books = list_books_by_weight("main")
    assert "pinnacle" in main_books
    assert main_books["pinnacle"] == 4
    
    # Props with min_weight=3
    prop_books_3 = list_books_by_weight("props", min_weight=3)
    assert "pinnacle" in prop_books_3
    assert "draftkings" in prop_books_3
    assert "fanduel" in prop_books_3
    assert "bovada" not in prop_books_3  # weight 1
    
    # With sport override
    nba_props = list_books_by_weight("props", sport="NBA", min_weight=3)
    assert "bet365" in nba_props  # Should be 3 in NBA props
    
    print("  ✓ list_books_by_weight function validated")


def test_weight_scale_consistency():
    """Verify all weights are in valid 0-4 range."""
    for book, weight in MAIN_MARKET_WEIGHTS.items():
        assert 0 <= weight <= 4, f"Main market weight for {book} out of range: {weight}"
    
    for book, weight in PLAYER_PROP_WEIGHTS.items():
        assert 0 <= weight <= 4, f"Player prop weight for {book} out of range: {weight}"
    
    for sport, overrides in SPORT_OVERRIDES.items():
        for market_type, weights in overrides.items():
            for book, weight in weights.items():
                assert 0 <= weight <= 4, f"Override weight for {sport}/{market_type}/{book} out of range: {weight}"
    
    print("  ✓ All weights within valid 0-4 range")


def run_all_tests():
    """Run all tests."""
    print("\nRunning book_weights tests...\n")
    
    test_main_market_weights()
    test_player_prop_weights()
    test_sport_overrides_exist()
    test_get_book_weight_basic()
    test_get_book_weight_normalization()
    test_get_book_weight_sport_override()
    test_get_book_weight_fallback()
    test_get_book_display_name()
    test_list_books_by_weight()
    test_weight_scale_consistency()
    
    print("\n✓ All book_weights tests passed!\n")


if __name__ == "__main__":
    run_all_tests()
