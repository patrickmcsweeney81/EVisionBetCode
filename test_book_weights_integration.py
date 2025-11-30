#!/usr/bin/env python3
"""
Test book_weights integration with fair_prices module.

Run this to verify the new book_weights system is working correctly.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_book_weights_import():
    """Test that book_weights module imports correctly."""
    print("Test 1: Import book_weights module...")
    try:
        from core.book_weights import get_book_weight, list_books_by_weight, get_book_display_name
        print("✅ PASS: book_weights module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ FAIL: Could not import book_weights: {e}")
        return False


def test_get_book_weight():
    """Test get_book_weight function."""
    print("\nTest 2: Get book weights...")
    from core.book_weights import get_book_weight
    
    tests = [
        ("pinnacle", "main", None, 4),
        ("draftkings", "props", "NBA", 4),  # NBA override
        ("draftkings", "props", None, 4),   # Default props
        ("draftkings", "main", None, 3),    # Main markets
        ("bovada", "main", None, 1),        # Follower
        ("unknown_book", "main", None, 0),  # Unknown
    ]
    
    passed = 0
    for book, market, sport, expected in tests:
        result = get_book_weight(book, market, sport)
        status = "✅" if result == expected else "❌"
        sport_str = f", sport={sport}" if sport else ""
        print(f"  {status} {book} ({market}{sport_str}): {result} (expected {expected})")
        if result == expected:
            passed += 1
    
    print(f"  Result: {passed}/{len(tests)} tests passed")
    return passed == len(tests)


def test_list_books_by_weight():
    """Test list_books_by_weight function."""
    print("\nTest 3: List books by weight...")
    from core.book_weights import list_books_by_weight
    
    # Main markets, weight >= 3
    sharps_main = list_books_by_weight("main", min_weight=3)
    print(f"  Main market sharps (weight >= 3): {len(sharps_main)} books")
    print(f"    Top 3: {list(sharps_main.keys())[:3]}")
    
    # NBA props, weight >= 4
    top_nba_props = list_books_by_weight("props", sport="NBA", min_weight=4)
    print(f"  NBA props tier-1 (weight >= 4): {len(top_nba_props)} books")
    print(f"    Books: {list(top_nba_props.keys())}")
    
    # Check that Pinnacle is always included
    if "pinnacle" in sharps_main and "pinnacle" in top_nba_props:
        print("  ✅ PASS: Pinnacle present in both lists")
        return True
    else:
        print("  ❌ FAIL: Pinnacle missing from lists")
        return False


def test_weighted_median():
    """Test weighted_median function."""
    print("\nTest 4: Weighted median calculation...")
    from core.utils import weighted_median
    
    # Test 1: Weight 4 should dominate
    values1 = [(2.00, 4), (2.10, 3), (2.20, 1)]
    result1 = weighted_median(values1)
    print(f"  Test 4a: {values1} → {result1:.3f}")
    
    # Test 2: Equal tier-1 weights should use median
    values2 = [(2.00, 4), (2.10, 4), (2.20, 4)]
    result2 = weighted_median(values2)
    print(f"  Test 4b: {values2} → {result2:.3f}")
    
    # Test 3: Only weight 2 books (no tier-1)
    values3 = [(2.00, 2), (2.10, 2), (2.20, 2)]
    result3 = weighted_median(values3)
    print(f"  Test 4c: {values3} → {result3:.3f}")
    
    # Validate results - weighted median uses median after weighting, not exact value
    # Result1: Heavy weight on 2.0 (w=4) vs lighter on higher values → ~2.05
    # Result2/3: Equal weights → median of sorted values
    tolerance = 0.02  # Allow small variance from theoretical expectation
    
    expected1_range = (2.00, 2.10)  # Should favor 2.0 but not exactly
    expected2 = 2.10  # Median of [2.0, 2.1, 2.2]
    expected3 = 2.10  # Median of [2.0, 2.1, 2.2]
    
    pass1 = expected1_range[0] <= result1 <= expected1_range[1]
    pass2 = abs(result2 - expected2) < tolerance
    pass3 = abs(result3 - expected3) < tolerance
    
    if pass1 and pass2 and pass3:
        print("  ✅ PASS: Weighted median calculations within expected range")
        return True
    else:
        print(f"  ❌ FAIL: result1={result1:.3f} (expected {expected1_range[0]}-{expected1_range[1]}), result2={result2:.3f} (expected ~{expected2}), result3={result3:.3f} (expected ~{expected3})")
        return False


def test_fair_prices_integration():
    """Test that fair_prices.py can use book_weights."""
    print("\nTest 5: Fair prices integration...")
    try:
        from core.fair_prices import build_fair_price_from_books, build_fair_prices_two_way
        
        # Test single outcome fair price
        bookmaker_odds = {
            "pinnacle": 2.05,
            "draftkings": 2.10,
            "fanduel": 2.08,
            "bovada": 2.30  # Should be filtered out (weight 1)
        }
        
        fair = build_fair_price_from_books(bookmaker_odds, "props", "NBA")
        print(f"  Single outcome fair: {fair:.3f}")
        
        # Test two-way fair price
        odds_a = {"pinnacle": 2.05, "draftkings": 2.08}
        odds_b = {"pinnacle": 1.95, "draftkings": 1.92}
        
        fair_two_way = build_fair_prices_two_way(odds_a, odds_b, "props", "NBA")
        print(f"  Two-way fair: A={fair_two_way.get('A', 0):.3f}, B={fair_two_way.get('B', 0):.3f}")
        
        if fair > 0 and fair_two_way:
            print("  ✅ PASS: Fair price functions working")
            return True
        else:
            print("  ❌ FAIL: Fair price calculation failed")
            return False
    except Exception as e:
        print(f"  ❌ FAIL: Error in fair prices: {e}")
        return False


def test_h2h_handler_v2():
    """Test new h2h_handler v2 functions."""
    print("\nTest 6: H2H handler v2 integration...")
    try:
        from core.h2h_handler import process_h2h_event_v2, BOOK_WEIGHTS_AVAILABLE
        
        if BOOK_WEIGHTS_AVAILABLE:
            print("  ✅ PASS: book_weights available in h2h_handler")
            return True
        else:
            print("  ⚠️  WARNING: book_weights not available (import failed)")
            return False
    except Exception as e:
        print(f"  ❌ FAIL: Error importing h2h_handler: {e}")
        return False


def test_get_sharp_books_by_weight():
    """Test get_sharp_books_by_weight utility."""
    print("\nTest 7: Get sharp books by weight...")
    from core.utils import get_sharp_books_by_weight
    
    bookmaker_odds = {
        "pinnacle": 2.05,
        "draftkings": 2.10,
        "fanduel": 2.08,
        "bovada": 2.30,
        "unibet": 2.25
    }
    
    # Get weight >= 3 for NBA props
    sharps = get_sharp_books_by_weight(bookmaker_odds, "props", "NBA", min_weight=3)
    print(f"  Found {len(sharps)} sharp books (weight >= 3)")
    for book, odds, weight in sharps:
        print(f"    {book}: odds={odds:.2f}, weight={weight}")
    
    # Should have pinnacle (4), draftkings (4), fanduel (4)
    # Should NOT have bovada (1) or unibet (1)
    sharp_books = [b for b, _, _ in sharps]
    expected = ["pinnacle", "draftkings", "fanduel"]
    
    if all(book in sharp_books for book in expected) and len(sharps) >= 3:
        print("  ✅ PASS: Sharp books filtered correctly")
        return True
    else:
        print(f"  ❌ FAIL: Expected {expected}, got {sharp_books}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("BOOK WEIGHTS INTEGRATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_book_weights_import,
        test_get_book_weight,
        test_list_books_by_weight,
        test_weighted_median,
        test_fair_prices_integration,
        test_h2h_handler_v2,
        test_get_sharp_books_by_weight,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Integration successful!")
        print("\nNext steps:")
        print("1. Run bot with current code (uses legacy functions)")
        print("2. Test process_h2h_event_v2() on sample data")
        print("3. Migrate remaining handlers (spreads, totals, props)")
        print("4. Update main bot to pass sport parameter")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
